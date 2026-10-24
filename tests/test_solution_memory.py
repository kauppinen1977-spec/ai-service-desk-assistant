import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from desk import DeskError
from solution_memory import Memory, suggest


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
    def test_no_api_without_explicit_send(self):
        with patch('desk.request_model') as provider:
            with self.assertRaises(DeskError):
                suggest(dict(problem=SAMPLE['problem'], environment=SAMPLE['environment']))
            provider.assert_not_called()

    def test_api_result_is_unverified_and_only_explicit_fields_are_sent(self):
        response = dict(title='VPN E42', solution='Tarkista asiakkaan versio.', limitations='Syy ei ole varma.')
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


if __name__ == '__main__':
    unittest.main()
