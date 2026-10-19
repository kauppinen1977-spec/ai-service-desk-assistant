"""Conservative fallback and real response chain; no embedding/model/API calls."""
import copy
import math
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import desk
import search
from corpus import load_guides


class HybridFallbackTests(unittest.TestCase):
    ticket = 'Ylikirjoitin tiedoston uuden version päälle. Tarvitsen eilisen sisällön.'

    def setUp(self):
        self.guides = load_guides('batch1')
        self.pure = dict(backend='vector',category='muu',ambiguous=False,threshold=.43,hits=[],
                         best_candidate=dict(guide_id='IAM-004',score=.423190),
                         fingerprint='synthetic-only',reranking=None)

    def fallback(self, ticket=None, guides=None, pure=None):
        return search.hybrid_fallback(ticket or self.ticket, self.pure if pure is None else pure,
                                      self.guides if guides is None else guides)

    def test_overwrite_gap_is_rescued_in_real_demo_and_mocked_live_chain(self):
        for mode in ('demo','live'):
            index=SimpleNamespace(query=Mock(return_value=copy.deepcopy(self.pure)))
            # Include the real known facts in the mock assembly, as a real
            # provider path does. The actual vector wrapper is not mocked.
            from response_rules import known_facts
            def select(ticket,docs):
                self.assertEqual([g['id'] for g in docs],['DEVICE-012'])
                return desk.assemble(dict(state='suggestion',primary_source_id=docs[0]['id'],summary='Mock'),docs,known_facts(ticket))
            with self.subTest(mode=mode),patch.object(desk,'CORPUS','batch1'), \
                 patch.object(search,'_cached',None),patch.object(search,'_cached_signature',None), \
                 patch.object(search,'VectorSearch',return_value=index), \
                 patch('desk.call_model',side_effect=select) as model, \
                 patch('urllib.request.urlopen',side_effect=AssertionError('No API')):
                out=desk.answer(self.ticket,mode,'vector')
            self.assertEqual(out['result']['state'],'suggestion' if mode=='live' else 'candidates')
            self.assertEqual([c['guide_id'] for c in out['candidates'] if c['eligible']],['DEVICE-012'])
            self.assertEqual(out['search']['pure_vector'],self.pure)
            self.assertIsNone(out['candidates'][0]['score'])
            self.assertEqual(out['candidates'][0]['retrieval_method'],'lexical_fallback')
            self.assertEqual(model.call_count,int(mode=='live'))

    def test_original_result_is_immutable_and_cosine_is_not_fabricated(self):
        before=copy.deepcopy(self.pure)
        out=self.fallback()
        self.assertEqual(self.pure,before)
        self.assertEqual(out['pure_vector'],before)
        self.assertEqual(out['threshold'],.43)
        self.assertEqual(out['best_candidate']['score'],.423190)
        self.assertTrue(out['fallback']['applied'])
        self.assertIsNone(out['hits'][0]['score'])

    def test_nonempty_vector_hits_are_never_replaced(self):
        raw=dict(self.pure,hits=[dict(guide_id='IAM-004',score=.6)],category='käyttöoikeudet')
        self.assertEqual(self.fallback(pure=raw),raw)

    def test_keyword_without_positive_applicability_is_not_enough(self):
        for ticket in ('Ylikirjoitin sähköpostiviestin.', 'Tiedosto ei avaudu.',
                       'En ylikirjoittanut tiedostoa.', 'Tiedoston nimi on ylikirjoitin.'):
            with self.subTest(ticket=ticket):self.assertEqual(self.fallback(ticket),self.pure)

    def test_negated_hypothetical_quoted_and_content_requests_abstain(self):
        for ticket in ('Jos ylikirjoitin tiedoston, voiko sen palauttaa?',
                       'Ehkä ylikirjoitin tiedoston.',
                       'Ohjeessa lukee "Ylikirjoitin tiedoston".',
                       'Kirjoita tarina, jossa ylikirjoitin tiedoston.',
                       'Kuvittele seuraava tilanne. Ylikirjoitin tiedoston.',
                       'Ylikirjoitin tiedoston. En ylikirjoittanut sitä.',
                       'En tiedä, poistinko vai ylikirjoitin tiedoston.',
                       'En ole varma. Ylikirjoitin tiedoston?'):
            with self.subTest(ticket=ticket):self.assertEqual(self.fallback(ticket),self.pure)

    def test_generic_keyword_is_not_a_specific_event_match(self):
        guide=copy.deepcopy(next(g for g in self.guides if g['id']=='DEVICE-012'))
        guide['keywords']=['tiedosto']
        self.assertEqual(self.fallback('Tiedosto on ylikirjoitettu.',guides=[guide]),self.pure)

    def test_multiple_eligible_sources_do_not_choose_by_order(self):
        guide=copy.deepcopy(next(g for g in self.guides if g['id']=='DEVICE-012'))
        other=dict(guide,id='ALTERNATIVE')
        for guides in ([guide,other],[other,guide]):
            self.assertEqual(self.fallback(guides=guides),self.pure)

    def test_source_identifiers_are_not_used_to_find_the_match(self):
        guide=copy.deepcopy(next(g for g in self.guides if g['id']=='DEVICE-012'))
        guide['id']='UNRELATED-ID'
        self.assertEqual(self.fallback(guides=[guide])['hits'][0]['guide_id'],'UNRELATED-ID')

    def test_service_boundary_and_ambiguous_result_are_not_bypassed(self):
        for raw in (dict(self.pure,scope_filter={'reason':'unsupported_requested_action'}),
                    dict(self.pure,ambiguous=True)):
            self.assertEqual(self.fallback(pure=raw),raw)
        self.assertEqual(self.fallback(self.ticket+' Korvaako vakuutus tiedoston palautuksen?'),self.pure)

    def test_pure_vector_query_remains_below_threshold(self):
        # Controlled unit vectors exercise the real cosine/threshold algorithm.
        # The production query itself must not silently become hybrid search.
        index=object.__new__(search.VectorSearch)
        index.guides={g['id']:g for g in self.guides}
        index.model=SimpleNamespace(encode=Mock(return_value=[[1.,0.]]))
        index.threshold=.43; index.fingerprint='synthetic'
        index.chunks=[dict(guide_id=id,chunk_id=id+':test',text='synthetic')
                      for id in ('IAM-004','DEVICE-012')]
        index.vectors=[[s,math.sqrt(1-s*s)] for s in (.423190,.3)]
        pure=index.query(self.ticket)
        self.assertEqual(pure['hits'],[])
        self.assertEqual(pure['best_candidate']['score'],.423190)
        self.assertNotIn('fallback',pure)
        hybrid=search.hybrid_fallback(self.ticket,pure,self.guides)
        self.assertEqual(hybrid['pure_vector'],pure)
        self.assertEqual(hybrid['hits'][0]['guide_id'],'DEVICE-012')
        index.model.encode.assert_called_once()

    def test_safety_stop_keeps_priority_without_search_or_model(self):
        with patch.object(desk,'CORPUS','batch1'), \
             patch('search.vector_search',side_effect=AssertionError('No search')), \
             patch('desk.call_model',side_effect=AssertionError('No model')):
            out=desk.answer(self.ticket+' Akku on turvonnut.','live','vector')
        self.assertEqual(out['result']['state'],'safety_stop')

    def test_deletion_also_uses_confirmed_event_not_only_overwrite_word(self):
        self.assertEqual(self.fallback('Poistin tiedoston vahingossa.')['hits'][0]['guide_id'],'DEVICE-012')


if __name__=='__main__':unittest.main()
