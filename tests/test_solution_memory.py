import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from desk import DeskError
from solution_memory import Memory, suggest, dispatch


SAMPLE = dict(title='Harjoitusyrityksen VPN E42', problem='VPN yhteys epäonnistuu virheellä E42.',
              environment='Kuvitteellinen VPN-asiakas 5.2, Windows 11.',
              solution='Korjaa asiakkaan profiili hyväksytyllä asetustiedostolla. Vain versio 5.2.')


class FakeEncoder:
    """Synthetic vectors test index lifecycle, not semantic quality."""
    def encode(self, texts, **kwargs):
        return [[1., 0.] if any(word in t.casefold() for word in ('vpn', 'etäyhteys'))
                else [0., 1.] for t in texts]


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'memory.sqlite3'
        self.memory = Memory(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def verified(self):
        row = self.memory.save(SAMPLE)
        return self.memory.transition(dict(id=row['id'], revision=row['revision'],
                                          confirmed=True, verified_by='Testitukihenkilö'), 'verified')

    def test_draft_is_not_searchable_but_persists_after_reopening(self):
        row = self.memory.save(SAMPLE)
        self.assertEqual(self.memory.search('VPN E42')['hits'], [])
        self.assertEqual(Memory(self.path).list()[0]['id'], row['id'])

    def test_verified_record_is_searchable_with_provenance(self):
        row = self.verified()
        hit = self.memory.search('VPN E42')['hits'][0]['record']
        self.assertEqual(hit['id'], row['id'])
        self.assertEqual(hit['verified_by'], 'Testitukihenkilö')
        self.assertTrue(hit['verified_at'])
        self.assertEqual(hit['environment'], SAMPLE['environment'])

    def test_draft_edit_verify_and_rediscover_in_isolated_database(self):
        draft=self.memory.save(SAMPLE)
        self.assertEqual(self.memory.search('VPN E42')['hits'],[])
        edited=self.memory.save(dict(SAMPLE,id=draft['id'],revision=draft['revision'],
                                     solution='Päivitetty harjoitusohje.'))
        self.assertEqual(edited['status'],'draft')
        verified=self.memory.transition(dict(id=edited['id'],revision=edited['revision'],
            confirmed=True,verified_by='Synteettinen testaaja'),'verified')
        reopened=Memory(self.path)
        hit=reopened.search('VPN E42')['hits'][0]['record']
        self.assertEqual(hit['id'],verified['id'])
        self.assertEqual(hit['solution'],'Päivitetty harjoitusohje.')
        self.assertEqual(hit['verified_by'],'Synteettinen testaaja')

    def test_verification_requires_explicit_confirmation(self):
        row = self.memory.save(SAMPLE)
        with self.assertRaises(DeskError):
            self.memory.transition(dict(id=row['id'], revision=1, verified_by='Testi'), 'verified')
        self.assertEqual(self.memory.list()[0]['status'], 'draft')

    def test_edit_revokes_verification_and_removes_from_search(self):
        row = self.verified()
        updated = self.memory.save(dict(SAMPLE, id=row['id'], revision=row['revision'], solution='Uusi korjaus.'))
        self.assertEqual(updated['status'], 'draft')
        self.assertIsNone(updated['verified_by'])
        self.assertIsNone(updated['verified_at'])
        self.assertEqual(self.memory.search('VPN E42')['hits'], [])

    def test_stale_edit_and_retire_do_not_overwrite_newer_revision(self):
        row = self.verified()
        self.memory.save(dict(SAMPLE, id=row['id'], revision=row['revision'], title='Uusi otsikko'))
        for action in ('save', 'retire'):
            with self.assertRaises(DeskError) as caught:
                if action == 'save':
                    self.memory.save(dict(SAMPLE, id=row['id'], revision=row['revision']))
                else:
                    self.memory.transition(dict(id=row['id'], revision=row['revision'], reason='Vanha'), 'retired')
            self.assertEqual(caught.exception.status, 409)
        self.assertEqual(self.memory.list()[0]['title'], 'Uusi otsikko')

    def test_retired_is_preserved_but_not_searchable_or_reverified(self):
        row = self.verified()
        retired = self.memory.transition(dict(id=row['id'], revision=row['revision'], reason='Väärä versio'), 'retired')
        self.assertEqual(self.memory.search('VPN E42')['hits'], [])
        self.assertEqual(Memory(self.path).list()[0]['retirement_reason'], 'Väärä versio')
        with self.assertRaises(DeskError):
            self.memory.transition(dict(id=row['id'], revision=retired['revision'],
                                        confirmed=True, verified_by='Testi'), 'verified')

    def test_vector_cache_rebuild_excludes_retired_records(self):
        first = self.verified()
        other = self.memory.save(dict(SAMPLE, title='Toinen VPN ratkaisu', problem='VPN toinen virhe.'))
        self.memory.transition(dict(id=other['id'], revision=1, confirmed=True, verified_by='Testi'), 'verified')
        before = self.memory.search('Etäyhteys ei yhdisty', 'vector', FakeEncoder())
        self.assertEqual(len(before['hits']), 2)
        self.memory.transition(dict(id=first['id'], revision=first['revision'], reason='Virheellinen'), 'retired')
        after = self.memory.search('Etäyhteys ei yhdisty', 'vector', FakeEncoder())
        self.assertEqual([hit['record']['id'] for hit in after['hits']], [other['id']])
        cache = json.loads(self.path.with_suffix('.vectors.json').read_text())
        self.assertEqual(len(cache['vectors']), 5)

    def test_unknown_problem_returns_no_keyword_candidate(self):
        self.verified()
        self.assertEqual(self.memory.search('Tulostin paperitukos')['hits'], [])

    def test_invalid_record_does_not_write_partial_data(self):
        for obj in (dict(SAMPLE, solution=''), dict(SAMPLE, title=42), dict(SAMPLE, environment='x' * 2001)):
            with self.assertRaises(DeskError):
                self.memory.save(obj)
        self.assertEqual(self.memory.list(), [])

    def test_safety_stop_overrides_saved_candidates(self):
        self.verified()
        result = self.memory.search('VPN ei toimi ja akku on turvonnut.')
        self.assertEqual(result['state'], 'safety_stop')
        self.assertEqual(result['hits'], [])


class SuggestionTests(unittest.TestCase):
    def test_optional_environment_and_declared_fields_are_sent_without_opening_database(self):
        response = dict(title='Luonnos', solution='Tarkista versio.', limitations='Kokeilematon.', commands=[], links=[])
        for context in ({}, {'operating_system': 'Windows 11', 'product': 'AuroraVPN',
                             'product_version': '5.2', 'environment': 'Vapaa kuvaus.'}):
            with self.subTest(context=context), patch('desk.request_model', side_effect=lambda *args, **kwargs: dict(response)) as provider, \
                    patch('solution_memory.Memory', side_effect=AssertionError('Suggestion must not open database')):
                result = dispatch('suggest', dict(problem=SAMPLE['problem'], send_to_api=True,
                                                  unrelated_secret='never-send', **context))
                sent = json.loads(provider.call_args.args[0]['input'])
                self.assertEqual(sent, dict(problem=SAMPLE['problem'], environment='', **context)
                                 if 'environment' not in context else dict(problem=SAMPLE['problem'], **context))
                self.assertEqual(result['state'], 'unverified')

    def test_invalid_optional_fields_do_not_call_provider(self):
        for context in ({'operating_system': 42}, {'product_version': 'x' * 81},
                        {'environment': 'x' * 2001}, {'environment': None}):
            with self.subTest(context=context), patch('desk.request_model') as provider:
                with self.assertRaises(DeskError):
                    suggest(dict(problem=SAMPLE['problem'], send_to_api=True, **context))
                provider.assert_not_called()

    def test_safety_stop_checks_declared_environment_too(self):
        with patch('desk.request_model') as provider:
            result = suggest(dict(problem=SAMPLE['problem'], product='Akku on turvonnut.', send_to_api=True))
            provider.assert_not_called()
            self.assertEqual(result['state'], 'safety_stop')

    def test_no_api_without_explicit_send(self):
        with patch('desk.request_model') as provider:
            with self.assertRaises(DeskError):
                suggest(dict(problem=SAMPLE['problem'], environment=SAMPLE['environment']))
            provider.assert_not_called()

    def test_api_result_is_unverified_and_only_explicit_fields_are_sent(self):
        response = dict(title='VPN E42', solution='Tarkista asiakkaan versio.', limitations='Syy ei ole varma.', commands=[], links=[])
        with patch('desk.request_model', return_value=response) as provider:
            result = suggest(dict(problem=SAMPLE['problem'], environment=SAMPLE['environment'],
                                  send_to_api=True, unrelated_secret='do-not-send'))
        self.assertEqual(result['state'], 'unverified')
        payload = provider.call_args.args[0]
        self.assertNotIn('do-not-send', json.dumps(payload))
        self.assertFalse(payload['store'])
        self.assertEqual(set(json.loads(payload['input'])), {'problem', 'environment'})

    def test_bad_model_output_is_rejected(self):
        with patch('desk.request_model', return_value={'solution': 'x'}):
            with self.assertRaises(DeskError) as caught:
                suggest(dict(problem=SAMPLE['problem'], environment=SAMPLE['environment'], send_to_api=True))
        self.assertEqual(caught.exception.code, 'invalid_model_output')

    def test_safety_stop_prevents_api_call(self):
        with patch('desk.request_model') as provider:
            result = suggest(dict(problem='Kannettavan akku on turvonnut.',
                                  environment='Harjoituslaite', send_to_api=True))
            provider.assert_not_called()
        self.assertEqual(result['state'], 'safety_stop')


class MemoryKeywordSymptomTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.memory = Memory(Path(self.temp.name) / 'synthetic.sqlite3')
        self.filters = dict(operating_system='Windows 11', product='LENOVO', product_version='83GS')
        self.display = self.verified('Näytönohjaimen asetukset Nvidia E42', 'Näytön ohjain asetukset eivät ole kohdillaan',
                                     'Windows 11 ja Nvidia E42')
        self.mouse = self.verified('Hiiren vianetsintä', 'Hiiri ei toimi', 'Hiiri ei toimi')

    def verified(self, title, problem, environment):
        row = self.memory.save(dict(title=title, problem=problem, environment=environment,
                                    solution='Tarkista laitteen asetukset.', operating_system='Windows 11'))
        return self.memory.transition(dict(id=row['id'], revision=row['revision'], confirmed=True,
                                           verified_by='Synteettinen testaaja'), 'verified')

    def search(self, query):
        return self.memory.search(query, filters=self.filters)

    def test_five_baseline_queries(self):
        for query in ('Näytön ohjain ei toimi kunnolla ja kaipaan siihen päivitystä',
                      'Näytönohjain ei toimi'):
            with self.subTest(query=query):
                self.assertEqual([h['record']['id'] for h in self.search(query)['hits']], [self.display['id']])
        self.assertEqual([h['record']['id'] for h in self.search('Hiiri ei toimi')['hits']], [self.mouse['id']])
        generic = self.search('Ei toimi')
        self.assertEqual((generic['state'], generic['hits'], generic['message']),
                         ('clarification', [], 'Mikä laite, ohjelma tai toiminto ei toimi?'))
        missing = self.search('Teamsissa mikrofoni ei toimi')
        self.assertEqual((missing['state'], missing['hits']), ('insufficient', []))

    def test_specific_match_suffices_and_symptom_still_adds_score(self):
        self.assertEqual(self.search('Hiiri')['hits'][0]['score'], 1)
        self.assertEqual(self.search('Hiiri ei toimi')['hits'][0]['score'], 2)
        # Search validation already requires five characters, including for codes.
        for query in ('Nvidia', 'E42!!'):
            with self.subTest(query=query):
                self.assertEqual([h['record']['id'] for h in self.search(query)['hits']], [self.display['id']])

    def test_symptom_candidates_filtered_before_top_three(self):
        for i in range(4):
            self.verified('Muu laite ' + str(i), 'Laite ei toimi', 'Testiympäristö')
        self.assertEqual([h['record']['id'] for h in self.search('Hiiri ei toimi')['hits']], [self.mouse['id']])

    def test_environment_alone_or_with_symptom_does_not_qualify(self):
        self.verified('Näyttö jumittaa', 'Näyttö ei toimi', 'Reititin ZX123 E99')
        for query in ('ZX123', 'E99!!', 'Reititin ei toimi'):
            with self.subTest(query=query):
                result = self.search(query)
                self.assertEqual(result['hits'], [])
                self.assertEqual(result['state'], 'insufficient')

    def test_environment_supplements_without_counting_duplicate_words(self):
        record = self.verified('Skanneri ZX123', 'Skanneri ei toimi', 'Skanneri ZX123 E99')
        result = self.search('Skanneri ZX123 E99 ei toimi')
        hit = next(h for h in result['hits'] if h['record']['id'] == record['id'])
        self.assertEqual(hit['score'], 4)  # skanneri, zx123, e99, toimi, once each
        self.assertEqual(self.search('Skanneri')['hits'][0]['score'], 1)

    def test_environment_only_cannot_displace_qualifying_top_three(self):
        for i in range(4):
            self.verified('Laite jumittaa ' + str(i), 'Laite ei toimi', 'Hiiri hiiri')
        self.assertEqual([h['record']['id'] for h in self.search('Hiiri ei toimi')['hits']], [self.mouse['id']])

    def test_clarification_is_narrow_and_applies_even_without_eligible_records(self):
        self.assertEqual(self.search(' EI   TOIMI! ')['state'], 'clarification')
        self.assertEqual(self.search('Tuntematon laite ei toimi')['state'], 'insufficient')
        self.assertEqual(self.memory.search('Ei toimi', filters=dict(self.filters, operating_system='macOS'))['state'], 'clarification')

    def test_vector_path_is_not_filtered_or_clarified(self):
        hit = dict(guide_id=self.mouse['id'], score=0.8)
        with patch('search.VectorSearch') as vector:
            vector.return_value.query.return_value = dict(hits=[hit])
            result = self.memory.search('Ei toimi', 'vector', filters=self.filters)
        self.assertEqual(result['state'], 'candidates')
        self.assertEqual(result['hits'][0]['record']['id'], self.mouse['id'])

    def test_boundary_comparison_keeps_symptom_and_environment_rules(self):
        from keyword_boundary_comparison import boundary_search
        self.verified('Näyttö jumittaa', 'Näyttö ei toimi', 'Reititin ZX147')
        for query in ('Ääniohjain ei toimi', 'Reititin ei toimi', 'Missä vika on?'):
            with self.subTest(query=query):
                self.assertEqual(boundary_search(self.memory, query, self.filters)['hits'], [])
        for query in ('Näytön ohjain ei toimi', 'Näytönohjain ei toimi', 'Näytönohjainta päivittää'):
            with self.subTest(query=query):
                self.assertIn(self.display['id'], [h['record']['id'] for h in
                              boundary_search(self.memory, query, self.filters)['hits']])
        self.assertEqual(boundary_search(self.memory, 'Ei toimi', self.filters)['state'], 'clarification')


class JointSearchPrototypeTests(unittest.TestCase):
    class Model:
        def encode(self, texts, **kwargs):
            return [[1., 0.] if any(w in t.casefold() for w in ('skanneri', 'digilaite')) else [0., 1.] for t in texts]

    def setUp(self):
        from joint_search_prototype import JointSearchPrototype
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.memory = Memory(Path(self.temp.name) / 'joint.sqlite3')
        row = self.memory.save(dict(title='Skanneri E42', problem='Skanneri ei toimi',
                                    environment='Vain ympäristössä ZX147', solution='Tarkista laite.',
                                    operating_system='Windows 11', product='Mallituote', product_version='1'))
        self.record = self.memory.transition(dict(id=row['id'], revision=row['revision'],
                                                  confirmed=True, verified_by='Testi'), 'verified')
        self.search = JointSearchPrototype(self.memory, self.Model())

    def test_scope_filter_and_explicit_conflict_are_preserved(self):
        self.assertEqual(self.search.search('Skanneri ei toimi', {'operating_system':'macOS'})['hits'], [])
        hit = self.search.search('Skanneri ei toimi', {'operating_system':'Windows 11'})['hits'][0]
        self.assertEqual(hit['record']['id'], self.record['id'])
        self.assertEqual(hit['environment_check']['status'], 'needs_review')

    def test_environment_does_not_supply_lexical_or_semantic_evidence(self):
        first = self.search.search('Skanneri ZX147')
        self.assertEqual(first['hits'][0]['keyword_score'], 1)
        self.assertEqual(self.search.search('ZX147')['hits'], [])

    def test_clarification_and_technical_error_are_distinct(self):
        self.assertEqual(self.search.search('Ei toimi')['state'], 'clarification')
        with patch.object(self.search.model, 'encode', side_effect=RuntimeError('mallivirhe')):
            result = self.search.search('Skanneri ei toimi')
            empty = self.search.search('Tulostin paperitukos')
        self.assertEqual(result['semantic_status'], 'error')
        self.assertTrue(result['keyword_fallback'])
        from keyword_boundary_comparison import boundary_search
        self.assertEqual(result['hits'], boundary_search(self.memory, 'Skanneri ei toimi', score_environment=False)['hits'])
        self.assertEqual((empty['state'], empty['hits'], empty['semantic_status']), ('insufficient', [], 'error'))

    def test_joint_dispatch_fallback_uses_boundary_search_for_both_false_positives(self):
        row = self.memory.save(dict(title='Windows 11:ssä näytönohjaimen asetukset',
                                    problem='Näytön ohjain ei toimi', environment='Testi', solution='Tarkista.'))
        self.memory.transition(dict(id=row['id'], revision=row['revision'], confirmed=True, verified_by='Testi'), 'verified')
        for query in ('Ääniohjain ei toimi', 'Missä vika on?'):
            with self.subTest(query=query), patch('joint_search_prototype.encoder', side_effect=RuntimeError('mallivirhe')):
                result = self.memory.search(query, 'joint')
                self.assertEqual(result['hits'], [])
                self.assertEqual(result['semantic_status'], 'error')
                self.assertEqual(result['message'], 'Merkityshaku ei ole käytettävissä. Näytetään sanahaun tulokset.')

    def test_joint_dispatch_accepts_explicit_option_and_keeps_keyword_default(self):
        self.assertEqual(self.memory.search('Skanneri ei toimi')['backend'], 'keyword')
        result = self.memory.search('Skanneri ei toimi', 'joint', self.Model())
        self.assertEqual(result['backend'], 'joint_prototype')
        self.assertEqual(result['hits'][0]['record']['id'], self.record['id'])

    def test_no_semantic_candidate_is_a_normal_empty_result(self):
        result = self.search.search('Tulostin paperitukos')
        self.assertEqual((result['state'], result['hits']), ('insufficient', []))
        self.assertEqual(result['semantic_status'], 'ok')
        self.assertFalse(result['keyword_fallback'])

    def test_semantic_only_candidate_and_request_scope(self):
        result = self.search.search('Digilaite jumissa')
        self.assertEqual(result['hits'][0]['record']['id'], self.record['id'])
        self.assertEqual(result['hits'][0]['keyword_score'], 0)
        with patch('joint_search_prototype._apply_request_scope', return_value={'hits': []}) as scoped:
            self.assertEqual(self.search.search('Digilaite jumissa')['hits'], [])
            scoped.assert_called_once()



if __name__ == '__main__':
    unittest.main()
