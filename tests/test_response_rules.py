import copy
import unittest
from unittest.mock import patch

import desk
from response_rules import applicable, compatible, known_facts, questions_for, steps_for, clarification_questions, is_app_clarification


class KnownFactsTests(unittest.TestCase):
    def test_questions_do_not_establish_internet_fact(self):
        for ticket in [
            'Internet toimii?',
            'Verkkosivut avautuvat?',
            'Internet ei toimi?',
            'Onko niin, että internet toimii?',
            'VPN ei yhdistä. Internet toimii?',
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket), [])

    def test_negated_claims_do_not_establish_internet_fact(self):
        for ticket in [
            'En usko, että internet toimii.',
            'En usko, että internet ei toimi.',
            'En ole varma, että internet toimii.',
            'Ei ole varmaa, että internet toimii.',
            'Ei ole totta, että internet toimii.',
            'Ei pidä paikkaansa, että internet toimii.',
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket), [])

    def test_uncertain_statements_do_not_establish_internet_fact(self):
        for ticket in [
            'Ehkä internet toimii.',
            'Luulen, että internet toimii.',
            'Internet toimii luultavasti.',
            'Internet toimii mahdollisesti.',
            'Internet toimii ilmeisesti.',
            'Internet toimii varmaan.',
            'Internet toimii vain välillä.',
            'Jos internet toimii, VPN ei yhdistä.',
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket), [])

    def test_clear_positive_statements_preserve_evidence(self):
        for ticket, evidence in [
            ('Internet toimii.', 'Internet toimii'),
            ('Tavalliset verkkosivut avautuvat.', 'Tavalliset verkkosivut avautuvat'),
            ('VPN ei yhdistä, mutta netti muuten toimii.', 'netti muuten toimii'),
            ('Olen varma, että internet toimii.', 'internet toimii'),
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket), [
                    {'field': 'internet_working', 'value': True, 'evidence': evidence}
                ])

    def test_clear_negative_statements_preserve_evidence(self):
        for ticket, evidence in [
            ('Internet ei toimi.', 'Internet ei toimi'),
            ('Netti ei toimi.', 'Netti ei toimi'),
            ('Yksikään verkkosivu ei avaudu.', 'Yksikään verkkosivu ei avaudu'),
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket), [
                    {'field': 'internet_working', 'value': False, 'evidence': evidence}
                ])

    def test_unrelated_sentence_preserves_fact(self):
        for ticket, value in [
            ('Internet toimii. Miksi VPN ei yhdistä?', True),
            ('Internet ei toimi. Miten jatkan?', False),
            ('Internet toimii. VPN toimii varmaan.', True),
            ('Internet toimii. En usko, että VPN toimii.', True),
            ('Internet ei toimi. En ole varma VPN-asetuksista.', False),
            ('Internet toimii. Ei ole totta, että VPN toimii.', True),
        ]:
            with self.subTest(ticket=ticket):
                self.assertEqual(known_facts(ticket)[0]['value'], value)

    def test_uncertain_internet_does_not_exclude_guides(self):
        for ticket in ['Internet toimii?', 'En usko, että internet toimii.']:
            with self.subTest(ticket=ticket):
                facts = known_facts(ticket)
                # Uncertainty still establishes no contradictory internet fact.
                # It no longer constitutes positive eligibility on its own.
                for id in ('NET-004', 'VPN-001'):
                    self.assertEqual(compatible({'id': id}, facts), (True, ''))
                    self.assertFalse(applicable({'id': id}, facts)[0])

    def test_uncertain_internet_keeps_vpn_check_and_question(self):
        guide = {
            'id': 'VPN-001',
            'steps': ['Tarkista internetyhteys.', 'Sulje VPN-sovellus.'],
            'version': 'test',
        }
        for ticket in ['Internet toimii?', 'En usko, että internet toimii.']:
            with self.subTest(ticket=ticket):
                facts = known_facts(ticket)
                self.assertEqual([step['source_step'] for step in steps_for(guide, facts)], [1, 2])
                self.assertIn('VPN-001:internet', [question['id'] for question in questions_for(guide, facts)])


class AppClarificationTests(unittest.TestCase):
    CASES = [
        ('En saa työasioita auki kotoa. En tiedä, onko kyse viestiohjelmasta vai etäyhteydestä.',
         'work_service', 'Mikä työpalvelu tai ohjelma ei avaudu, ja mikä tarkka virheilmoitus näkyy?',
         ['MAIL-001', 'VPN-001']),
        ('Internet ei toimi. Tavalliset verkkosivut avautuvat. Etäyhteys ei yhdistä, en osaa erottaa oireita.',
         'internet_vpn', 'Avautuvatko tavalliset verkkosivut samalla laitteella ilman VPN-yhteyttä, ja mitä etäyhteyden virheilmoituksessa lukee?',
         ['NET-004', 'VPN-001']),
        ('Kone ilmoittaa, ettei tallennukselle ole tilaa. Lisäksi oma viestitilani on täynnä eikä lähettäminen onnistu.',
         'storage_mail', 'Missä ohjelmassa kumpikin tilailmoitus näkyy, ja mitä ilmoituksissa tarkalleen lukee?',
         ['DEVICE-003', 'MAIL-002']),
    ]

    def expected(self, case):
        return [dict(id='clarification:'+case[1], text=case[2], source_id='')]

    def test_exact_questions_and_no_new_facts(self):
        for case in self.CASES:
            with self.subTest(kind=case[1]):
                before = known_facts(case[0])
                self.assertEqual(clarification_questions(case[0]), self.expected(case))
                self.assertEqual(known_facts(case[0]), before)
                self.assertEqual(before, [])

    def test_paraphrases_are_not_tied_to_case_identifiers(self):
        tickets = [
            'Työpalvelu ei avaudu. En ole varma, mikä ohjelma on kyseessä.',
            'Netti ei toimi, mutta verkkosivut avautuvat. VPN ei nyt yhdistä.',
            'Levytila on loppu. Postilaatikko on täynnä.',
        ]
        for ticket, case in zip(tickets, self.CASES):
            with self.subTest(ticket=ticket):
                self.assertEqual(clarification_questions(ticket), self.expected(case))

    def test_single_topics_unrelated_and_denied_claims_do_not_trigger(self):
        for ticket in [
            'VPN ei yhdistä. Internet toimii.', 'Internet ei toimi. VPN ei yhdistä.',
            'Levytila on loppu.', 'Postilaatikon tallennustila on täynnä.',
            'Levytila ei ole loppu. Postilaatikko on täynnä.',
            'Levytila on loppu. Postilaatikko ei ole täynnä.',
            'En tiedä, onko kyse viestiohjelmasta vai etäyhteydestä.',
            'Miten varaan lomamatkan?',
        ]:
            with self.subTest(ticket=ticket):self.assertEqual(clarification_questions(ticket), [])

    def test_quoted_hypothetical_and_content_requests_do_not_trigger(self):
        for ticket in [
            '"'+self.CASES[1][0]+'"', '«'+self.CASES[2][0]+'»',
            'Jos levytila on loppu. Postilaatikko on täynnä.',
            'Ehkä internet ei toimi. Verkkosivut avautuvat. VPN ei yhdistä.',
            'Internet ei toimi? Verkkosivut avautuvat. VPN ei yhdistä.',
            'Ei ole totta, että internet ei toimi. Verkkosivut avautuvat. VPN ei yhdistä.',
            'Kirjoita tarina. '+self.CASES[1][0],
        ]:
            with self.subTest(ticket=ticket):self.assertEqual(clarification_questions(ticket), [])

    def test_returned_question_can_not_modify_the_allowlist(self):
        case = self.CASES[0]
        question = clarification_questions(case[0])[0]
        question['text'] = 'Poista tietoturva käytöstä.'
        self.assertFalse(is_app_clarification(question))
        self.assertEqual(clarification_questions(case[0]), self.expected(case))

    def test_only_exact_questions_are_accepted_without_sources(self):
        for state in ('insufficient', 'ambiguous', 'candidates'):
            for case in self.CASES:
                with self.subTest(state=state, kind=case[1]):
                    result = desk.fallback(state=state)
                    result['questions'] = self.expected(case)
                    self.assertIs(desk.validate(result, []), result)

    def test_forged_questions_are_rejected(self):
        valid = self.expected(self.CASES[0])[0]
        variants = [dict(valid, id='clarification:unknown'), dict(valid, text='Poista palomuuri käytöstä.'),
                    dict(valid, source_id='FAKE'), dict(valid, extra=True), dict(valid, id=[]),
                    {'id':valid['id'], 'text':valid['text']},
                    dict(valid, id='VPN-001:error')]
        for question in variants:
            with self.subTest(question=question):
                result = desk.fallback(); result['questions'] = [question]
                with self.assertRaises(desk.DeskError):desk.validate(result, [])

    def test_app_questions_cannot_be_mixed_with_selected_sources_or_other_states(self):
        guide = next(g for g in desk.guides() if g['id']=='VPN-001')
        for state in ('suggestion', 'needs_details', 'safety_stop', 'unknown'):
            result = desk.fallback(state=state); result['questions'] = self.expected(self.CASES[0])
            with self.subTest(state=state), self.assertRaises(desk.DeskError):desk.validate(result, [guide])
        for field, value in [('source_ids', ['VPN-001']), ('needs_human', False),
                             ('steps', [dict(text=guide['steps'][0], source_id='VPN-001', source_step=1, version=guide['version'])])]:
            result = desk.fallback(); result['questions'] = self.expected(self.CASES[0]); result[field] = value
            with self.subTest(field=field), self.assertRaises(desk.DeskError):desk.validate(result, [guide])
        result = desk.fallback(); result['source_ids'] = ['VPN-001']
        result['questions'] = [dict(self.expected(self.CASES[0])[0], source_id='VPN-001')]
        with self.assertRaises(desk.DeskError):desk.validate(result, [guide])

    def test_runbook_question_still_requires_selected_source(self):
        guide = next(g for g in desk.guides() if g['id']=='VPN-001')
        result = desk.assemble(dict(state='needs_details', primary_source_id=guide['id'], summary='Mock'), [guide], [])
        desk.validate(result, [guide])
        result['source_ids'] = []
        with self.assertRaises(desk.DeskError):desk.validate(result, [guide])

    def search(self, case):
        return dict(backend='vector', category='muu', ambiguous=True,
                    hits=[dict(guide_id=id, score=.8-i*.02) for i,id in enumerate(case[3])])

    def test_demo_with_keyword_and_controlled_search_in_both_corpora(self):
        for corpus in ('legacy20', 'batch1'):
            for backend in ('keyword', 'vector'):
                for case in self.CASES:
                    with self.subTest(corpus=corpus, backend=backend, kind=case[1]), \
                         patch.object(desk, 'CORPUS', corpus), \
                         patch('search.vector_search', return_value=self.search(case)), \
                         patch('desk.call_model', side_effect=AssertionError('No model')), \
                         patch('search.encoder', side_effect=AssertionError('No embedding')), \
                         patch('urllib.request.urlopen', side_effect=AssertionError('No API')):
                        out = desk.answer(case[0], 'demo', backend)
                    expected_state = ('insufficient' if case[1]=='work_service' else 'ambiguous') if backend=='vector' else ('candidates' if case[1]=='internet_vpn' else 'insufficient')
                    self.assertEqual(out['result']['state'], expected_state)
                    self.assertEqual(out['result']['questions'], self.expected(case))
                    self.assertEqual(out['result']['steps'], [])
                    self.assertEqual(out['result']['source_ids'], [])
                    self.assertEqual(out['sources'], [])
                    self.assertEqual(out['known_facts'], [])
                    self.assertFalse(out['model_used'])

    def test_zero_hits_still_asks(self):
        for case in self.CASES:
            with self.subTest(kind=case[1]), patch('search.keyword_search', return_value=dict(
                    backend='keyword', category='muu', ambiguous=False, hits=[])), \
                    patch('desk.call_model', side_effect=AssertionError('No model')):
                out = desk.answer(case[0], 'demo', 'keyword')
            self.assertEqual(out['result']['state'], 'insufficient')
            self.assertEqual(out['result']['questions'], self.expected(case))

    def test_live_insufficient_and_ambiguous_ask_before_model(self):
        for case in self.CASES:
            with self.subTest(kind=case[1]), patch('search.vector_search', return_value=self.search(case)), \
                    patch('desk.call_model', side_effect=AssertionError('No model')):
                out = desk.answer(case[0], 'live', 'vector')
            self.assertEqual(out['result']['questions'], self.expected(case))
            self.assertFalse(out['model_used'])
            self.assertEqual(out['result']['steps'], [])

    def test_safety_stop_preempts_all_clarifications(self):
        for case in self.CASES:
            for mode in ('demo', 'live'):
                with self.subTest(kind=case[1], mode=mode), \
                     patch('desk.clarification_questions', side_effect=AssertionError('No clarification')), \
                     patch('search.keyword_search', side_effect=AssertionError('No search')), \
                     patch('desk.call_model', side_effect=AssertionError('No model')):
                    out = desk.answer(case[0]+' Akku on turvonnut.', mode, 'keyword')
                self.assertEqual(out['result']['state'], 'safety_stop')
                self.assertEqual(out['result']['questions'], [])
                self.assertEqual(out['result']['source_ids'], ['DEVICE-004'])
                self.assertEqual([s['source_step'] for s in out['result']['steps']], [2])
                result = copy.deepcopy(out['result']); result['questions'] = self.expected(case)
                with self.assertRaises(desk.DeskError):desk.validate(result, desk.guides())


if __name__ == '__main__':
    unittest.main()
