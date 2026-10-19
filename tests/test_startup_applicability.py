"""Koko laitteen käynnistymispyyntö ei oikeuta käyttökuntoa olettaviin ohjeisiin."""
import unittest
from unittest.mock import patch

import desk
from response_rules import applicable, known_facts


class StartupApplicabilityTests(unittest.TestCase):
    def raw(self, ids=('DEVICE-002','DEVICE-003','NET-002'), ambiguous=False):
        return dict(backend='vector',category='laitteet',ambiguous=ambiguous,
                    hits=[dict(guide_id=id,score=.9-i*.01) for i,id in enumerate(ids)])

    def answer(self, ticket, ids=('DEVICE-002','DEVICE-003','NET-002'), mode='demo', backend='vector', ambiguous=False):
        with patch('search.'+backend+'_search',return_value=self.raw(ids,ambiguous)), \
             patch('desk.call_model',side_effect=AssertionError('No real or selected model call')):
            return desk.answer(ticket,mode,backend)

    def assert_gap(self, output):
        result=output['result']
        self.assertEqual(result['state'],'insufficient')
        self.assertEqual(result['source_ids'],[])
        self.assertEqual(result['steps'],[])
        self.assertEqual(output['sources'],[])
        self.assertFalse(output['model_used'])
        self.assertTrue(result['needs_human'])
        self.assertIn('?',result['summary'])
        self.assertIn('käynnistysyrityksellä',result['summary'])
        self.assertTrue(all(not c['eligible'] and c['exclusion_reason'] for c in output['candidates']))

    def test_original_and_paraphrases_reject_high_scoring_near_matches(self):
        for ticket in ['Tietokone ei lähde käyntiin.','Kone ei käynnisty.',
                       'Pöytäkone ei lähde päälle.','Kannettavani ei enää käynnisty.',
                       'En saa tietokonetta käyntiin.']:
            with self.subTest(ticket=ticket):
                output=self.answer(ticket)
                self.assert_gap(output)
                self.assertEqual([c['guide_id'] for c in output['candidates']],['DEVICE-002','DEVICE-003','NET-002'])
                self.assertEqual([c['score'] for c in output['candidates']],[.9,.89,.88])

    def test_both_modes_and_backends_do_not_delegate_gap_to_model(self):
        for mode in ['demo','live']:
            for backend in ['keyword','vector']:
                with self.subTest(mode=mode,backend=backend):
                    self.assert_gap(self.answer('Tietokone ei lähde käyntiin.',mode=mode,backend=backend))

    def test_empty_search_and_ambiguous_near_matches_still_ask(self):
        self.assert_gap(self.answer('Tietokone ei käynnisty.',ids=()))
        self.assert_gap(self.answer('Tietokone ei käynnisty.',ambiguous=True))

    def test_coverage_rule_uses_guide_scope_not_source_identifiers(self):
        facts=known_facts('Tietokone ei käynnisty.')
        self.assertFalse(applicable(dict(id='OTHER',title='Näytön tarkistus',
                                        symptoms='Kannettava toimii, ulkoinen näyttö on musta.'),facts)[0])
        self.assertTrue(applicable(dict(id='NEW-GUIDE',title='Käynnistymisen selvitys',
                                       symptoms='Tietokone ei käynnisty.'),facts)[0])

    def test_current_supported_problem_types_remain_candidates(self):
        cases=[('Tietokone käynnistyy, mutta ulkoinen näyttö ei näytä kuvaa.','DEVICE-002'),
               ('Tietokone toimii, mutta levytila on loppu.','DEVICE-003'),
               ('Tietokone toimii, mutta langaton verkko ei yhdisty.','NET-002'),
               ('Vain laskutusohjelma ei käynnisty.','DEVICE-005'),
               ('Kannettava ei lataudu.','DEVICE-004')]
        for ticket,id in cases:
            with self.subTest(ticket=ticket):
                out=self.answer(ticket,ids=(id,))
                self.assertEqual(out['result']['state'],'candidates')
                self.assertTrue(out['candidates'][0]['eligible'])

    def test_denied_hypothetical_quoted_and_conflicting_reports_are_not_assumed(self):
        tickets=['Tietokone käynnistyy. Vain ohjelma ei käynnisty.',
                 'Ei ole totta, että tietokone ei käynnisty.',
                 'Jos tietokone ei käynnisty, mitä tehdään?',
                 'Ohjeessa lukee "Tietokone ei käynnisty". Oma kone toimii.',
                 'Tietokone ei käynnisty. Tietokone käynnistyy kuitenkin normaalisti.',
                 'Ehkä tietokone ei käynnisty. En ole kokeillut.',
                 'En ole varma, ettei tietokone käynnisty.']
        for ticket in tickets:
            with self.subTest(ticket=ticket):
                out=self.answer(ticket,ids=('DEVICE-005',),ambiguous=True)
                self.assertFalse(any(f['field']=='device_startup_unresolved' for f in out['known_facts']))
                # Only the first request actually reports an application problem.
                self.assertEqual(out['candidates'][0]['eligible'], ticket==tickets[0])
                self.assertNotIn('käynnistysyrityksellä',out['result']['summary'])

    def test_safety_stop_has_priority_over_missing_startup_guide(self):
        for danger,id in [('Akku on turvonnut.','DEVICE-004'),
                          ('Saan tunnistautumispyyntöjä, vaikka en yritä kirjautua.','IAM-003'),
                          ('Annoin salasanani kalastelusivulle.','MAIL-003')]:
            with self.subTest(danger=danger), patch('search.vector_search',side_effect=AssertionError('No search')), \
                 patch('desk.call_model',side_effect=AssertionError('No model')):
                out=desk.answer('Tietokone ei käynnisty. '+danger,'live','vector')
                self.assertEqual(out['result']['state'],'safety_stop')
                self.assertEqual(out['result']['source_ids'],[id])

    def test_covered_problem_still_uses_mocked_live_selection(self):
        guide=next(g for g in desk.guides() if g['id']=='DEVICE-002')
        ticket='Tietokone toimii, mutta ulkoinen näyttö ei näytä kuvaa.'
        expected=desk.assemble(dict(state='suggestion',primary_source_id=guide['id'],
                                    summary='Lähdevalinta käsitelty.'),[guide],known_facts(ticket))
        with patch('search.vector_search',return_value=self.raw((guide['id'],))), \
             patch('desk.call_model',return_value=expected) as model:
            out=desk.answer(ticket,'live','vector')
        model.assert_called_once_with(ticket,[guide])
        self.assertEqual(out['result'],expected)
