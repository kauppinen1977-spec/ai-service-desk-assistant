import json
import math
import sqlite3
import tempfile
import unittest
from contextlib import closing, ExitStack
from pathlib import Path
from unittest.mock import patch

from desk import DeskError
from solution_memory import ENVIRONMENT_FIELDS, Memory, as_guide, check_environment, database, search_filters
from test_solution_memory import SAMPLE, FakeEncoder


ENV = dict(operating_system='Windows 11', product='AuroraVPN', product_version='5.2')


class RankingEncoder:
    # Controlled cosine similarity reproduces the real F17 ranking failure.
    def encode(self, texts, **kwargs):
        return [[0.5, math.sqrt(0.75)] if value.startswith('Projektikansion') else [1., 0.]
                for value in texts]


class MemoryEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'memory.sqlite3'
        self.memory = Memory(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def verified(self, memory=None, **fields):
        memory = memory or self.memory
        row = memory.save(dict(SAMPLE, **dict(ENV, **fields)))
        return memory.transition(dict(id=row['id'], revision=row['revision'], confirmed=True,
                                      verified_by='Kuvitteellinen testivahvistus'), 'verified')

    def legacy_database(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""CREATE TABLE solutions (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, problem TEXT NOT NULL,
                environment TEXT NOT NULL, solution TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('draft','verified','retired')),
                revision INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                verified_at TEXT, verified_by TEXT, retirement_reason TEXT)""")
            for status in ('draft', 'verified', 'retired'):
                db.execute('INSERT INTO solutions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                           ('old-'+status, SAMPLE['title'], SAMPLE['problem'], SAMPLE['environment'],
                            SAMPLE['solution'], status, 7, '2026-10-20', '2026-10-21',
                            None if status == 'draft' else '2026-10-21',
                            None if status == 'draft' else 'Alkuperäinen vahvistaja',
                            'Vanha poistamisen syy' if status == 'retired' else None))
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute('SELECT * FROM solutions ORDER BY id')]

    def test_migration_preserves_every_original_field_and_never_infers_metadata(self):
        original = self.legacy_database()
        migrated = sorted(self.memory.list(), key=lambda row: row['id'])
        self.assertEqual([{key:row[key] for key in original[0]} for row in migrated], original)
        self.assertTrue(all(row[key] is None for row in migrated for key in ENVIRONMENT_FIELDS))
        self.assertEqual(sorted(Memory(self.path).list(), key=lambda row:row['id']), migrated)
        with closing(sqlite3.connect(self.path)) as db, db:
            columns = {row[1]:row for row in db.execute('PRAGMA table_info(solutions)')}
            self.assertTrue(all(columns[key][3] == 0 for key in ENVIRONMENT_FIELDS))
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        result = self.memory.search('VPN E42', filters=ENV)
        self.assertEqual(len(result['hits']), 1)
        self.assertEqual(result['hits'][0]['environment_check']['status'], 'needs_review')
        self.assertEqual(set(result['hits'][0]['environment_check']['missing_record_fields']), set(ENV))

    def test_migration_rolls_back_schema_if_operation_fails(self):
        original = self.legacy_database()
        with self.assertRaisesRegex(RuntimeError, 'rollback'):
            with database(self.path):
                raise RuntimeError('rollback')
        with closing(sqlite3.connect(self.path)) as db, db:
            self.assertTrue(set(ENV).isdisjoint(row[1] for row in db.execute('PRAGMA table_info(solutions)')))
            db.row_factory = sqlite3.Row
            self.assertEqual([dict(row) for row in db.execute('SELECT * FROM solutions ORDER BY id')], original)

    def test_optional_fields_normalize_whitespace_and_validate_without_partial_writes(self):
        for field, limit in ENVIRONMENT_FIELDS.items():
            for value in (True, 42, [], 'x'*(limit+1)):
                with self.subTest(field=field, value=type(value).__name__), self.assertRaises(DeskError):
                    self.memory.save(dict(SAMPLE, **{field:value}))
        self.assertEqual(self.memory.list(), [])
        row = self.memory.save(dict(SAMPLE, operating_system='  Windows  11 ', product=' ', product_version=None))
        self.assertEqual(row['operating_system'], 'Windows 11')
        self.assertIsNone(row['product'])
        self.assertIsNone(row['product_version'])

    def test_older_edit_preserves_metadata_and_explicit_clear_revokes_verification(self):
        row = self.verified()
        updated = self.memory.save(dict(SAMPLE, id=row['id'], revision=row['revision']))
        self.assertEqual({key:updated[key] for key in ENV}, ENV)
        self.assertEqual(updated['status'], 'draft')
        self.assertIsNone(updated['verified_by'])
        cleared = self.memory.save(dict(SAMPLE, id=updated['id'], revision=updated['revision'], product_version=''))
        self.assertIsNone(cleared['product_version'])
        self.assertEqual(cleared['operating_system'], ENV['operating_system'])

    def test_each_environment_conflict_is_excluded_for_both_backends(self):
        for backend in ('keyword', 'vector'):
            for key, conflict in [('operating_system','macOS 15'), ('product','OtherVPN'), ('product_version','6.1')]:
                with self.subTest(backend=backend, field=key):
                    memory = Memory(self.path.with_name(backend+'-'+key+'.sqlite3'))
                    good = self.verified(memory)
                    bad = self.verified(memory, **{key:conflict})
                    result = memory.search('VPN E42', backend, FakeEncoder(), filters=ENV)
                    self.assertEqual([hit['record']['id'] for hit in result['hits']], [good['id']])
                    self.assertEqual(result['environment_filter']['excluded'], [{'id':bad['id'], 'conflicting_fields':[key]}])
                    self.assertEqual(result['hits'][0]['environment_check']['status'], 'declared_match')

    def test_filtering_happens_before_top_three_selection(self):
        good = self.verified()
        for _ in range(5):
            self.verified(product_version='6.1')
        for backend in ('keyword','vector'):
            with self.subTest(backend=backend):
                result = self.memory.search('VPN E42', backend, FakeEncoder(), filters=ENV)
                self.assertEqual([hit['record']['id'] for hit in result['hits']], [good['id']])
                self.assertEqual(result['environment_filter']['excluded_count'], 5)

    def test_missing_record_and_query_fields_are_reviewable_and_not_compatible(self):
        row = self.verified(product_version=None)
        result = self.memory.search('VPN E42', filters=dict(ENV, operating_system=None))
        hit = result['hits'][0]
        self.assertEqual(hit['record']['id'], row['id'])
        self.assertEqual(hit['environment_check']['status'], 'needs_review')
        self.assertEqual(hit['environment_check']['missing_record_fields'], ['product_version'])
        self.assertEqual(hit['environment_check']['missing_query_fields'], ['operating_system'])
        self.assertEqual(result['environment_filter']['review_hit_count'], 1)
        self.assertNotIn('compatible', hit)
        no_filters = self.memory.search('VPN E42')['hits'][0]['environment_check']
        self.assertEqual(set(no_filters['missing_query_fields']), set(ENV))
        self.assertEqual(no_filters['status'], 'needs_review')

    def test_exact_version_matching_and_case_whitespace_normalization(self):
        row = self.verified()
        result = self.memory.search('VPN E42', filters=dict(operating_system=' windows  11 ', product=' AURORAVPN ', product_version=' 5.2 '))
        self.assertEqual(result['hits'][0]['record']['id'], row['id'])
        self.assertEqual(result['hits'][0]['environment_check']['status'], 'declared_match')
        self.assertEqual(self.memory.search('VPN E42', filters=dict(ENV, product_version='5.20'))['hits'], [])

    def test_conflicting_records_do_not_load_a_model(self):
        self.verified()
        with patch('search.encoder', side_effect=AssertionError('Model loaded')):
            result = self.memory.search('VPN E42', 'vector', filters=dict(ENV, operating_system='Ubuntu 24.04'))
        self.assertEqual(result['hits'], [])
        self.assertEqual(result['environment_filter']['excluded_count'], 1)

    def test_cache_alternation_never_leaks_other_environment(self):
        windows = self.verified()
        mac = self.verified(operating_system='macOS 15')
        fingerprints = []
        for selected, expected in [(ENV,windows), (dict(ENV,operating_system='macOS 15'),mac), (ENV,windows)]:
            result = self.memory.search('VPN E42','vector',FakeEncoder(),filters=selected)
            self.assertEqual([hit['record']['id'] for hit in result['hits']], [expected['id']])
            fingerprints.append(json.loads(self.path.with_suffix('.vectors.json').read_text())['fingerprint'])
        self.assertNotEqual(fingerprints[0], fingerprints[1])
        self.assertEqual(fingerprints[0], fingerprints[2])

    def test_unknown_problem_with_same_environment_is_not_declared_applicable(self):
        self.verified()
        for backend in ('keyword','vector'):
            result = self.memory.search('Tulostimen paperitukos',backend,FakeEncoder(),filters=ENV)
            self.assertEqual(result['hits'], [])
            self.assertEqual(result['state'], 'insufficient')
            self.assertIn('Samankaltaisuus ei osoita soveltuvuutta', result['message'])

    def test_invalid_search_filters_fail_cleanly(self):
        for filters in ([], 'Windows', {'operating_system':42}, {'product':'x'*121}, {'unknown':'x'}):
            with self.subTest(filters=filters), self.assertRaises(DeskError):
                self.memory.search('VPN E42',filters=filters)

    def test_drafts_and_retired_are_excluded_even_with_matching_metadata(self):
        row = self.verified()
        self.memory.transition(dict(id=row['id'], revision=row['revision'], reason='Testi'), 'retired')
        self.memory.save(dict(SAMPLE, **ENV))
        for backend in ('keyword','vector'):
            self.assertEqual(self.memory.search('VPN E42',backend,FakeEncoder(),filters=ENV)['hits'], [])

    def test_known_os_aliases_match_both_directions_without_rewriting_records(self):
        pairs = [('Win 11','Windows 11'), ('win11','WINDOWS11'),
                 ('Win 10','Windows 10'), ('Mac OS 15','macOS 15'),
                 ('Ubuntu24.04','Ubuntu 24.04'), ('Debian12','Debian 12'),
                 ('Android15','Android 15')]
        for index, pair in enumerate(pairs):
            for direction, (actual, wanted) in enumerate((pair, pair[::-1])):
                with self.subTest(actual=actual,wanted=wanted):
                    memory=Memory(self.path.with_name(f'alias-{index}-{direction}.sqlite3'))
                    record=self.verified(memory,operating_system=actual)
                    result=memory.search('VPN E42',filters=dict(ENV,operating_system=wanted))
                    self.assertEqual([hit['record']['id'] for hit in result['hits']], [record['id']])
                    self.assertEqual(memory.list()[0]['operating_system'],actual)
                    self.assertEqual(result['hits'][0]['environment_check']['status'],'declared_match')

    def test_os_aliases_never_merge_versions_editions_products_or_missing_values(self):
        for actual, wanted in [('Windows 10','Win 11'), ('Windows 11.1','Win 11'),
                               ('macOS 15.1','Mac OS 15'), ('Ubuntu 24.10','Ubuntu24.04'),
                               ('Windows 11 Pro','Win 11'), ('Windows','Win 11')]:
            with self.subTest(actual=actual,wanted=wanted):
                check=check_environment(dict(ENV,operating_system=actual),search_filters(dict(ENV,operating_system=wanted)))
                self.assertEqual(check['conflicting_fields'],['operating_system'])
        for field, actual, wanted in [('product','Win 11','Windows 11'), ('product_version','5.2','5.20')]:
            check=check_environment(dict(ENV,**{field:actual}),search_filters(dict(ENV,**{field:wanted})))
            self.assertEqual(check['conflicting_fields'],[field])
        check=check_environment(dict(ENV,operating_system=None),search_filters(dict(ENV,operating_system='Win 11')))
        self.assertEqual(check['status'],'needs_review')
        self.assertEqual(check['missing_record_fields'],['operating_system'])

    def ranking_fixture(self):
        vpn=self.verified(title='VPN E42 Windowsissa')
        legacy=self.memory.save(dict(title='Projektikansion käyttöoikeus',problem='Verkkokansion käyttö estetty.',
                                     environment='Windowsin verkkolevy.',solution='Tarkista projektiryhmän käyttöoikeudet.'))
        legacy=self.memory.transition(dict(id=legacy['id'],revision=legacy['revision'],confirmed=True,verified_by='Testi'),'verified')
        query='Koivun Windows 11:n AuroraVPN 5.2 ei yhdisty E42:n vuoksi, vaikka verkkosivut avautuvat.'
        return vpn,legacy,query

    def test_memory_keeps_vector_order_when_poc_word_stem_promotes_review_candidate(self):
        vpn,legacy,query=self.ranking_fixture()
        result=self.memory.search(query,'vector',RankingEncoder(),filters=ENV)
        self.assertEqual([hit['record']['id'] for hit in result['hits']],[vpn['id'],legacy['id']])
        self.assertEqual([hit['score'] for hit in result['hits']],[1.,0.5])
        self.assertEqual([hit['record']['id'] for hit in result['compatible_hits']],[vpn['id']])
        self.assertEqual([hit['record']['id'] for hit in result['review_hits']],[legacy['id']])

    def test_poc_default_keeps_original_heuristics_and_pure_query_is_explicit(self):
        from search import VectorSearch
        vpn,legacy,query=self.ranking_fixture()
        index=VectorSearch([as_guide(row) for row in self.memory.list('verified')],RankingEncoder(),self.path.with_suffix('.vectors.json'))
        original=index.query(query)
        self.assertEqual(original,index.query(query,apply_poc_heuristics=True))
        self.assertEqual(original['hits'][0]['guide_id'],legacy['id'])
        self.assertEqual(original['reranking']['matched_terms'],['verkkosivut'])
        pure=index.query(query,apply_poc_heuristics=False)
        self.assertEqual(pure['hits'][0]['guide_id'],vpn['id'])
        self.assertIsNone(pure['reranking'])
        self.assertEqual(pure['threshold'],0.43)

    def test_pure_query_skips_all_poc_heuristics_without_changing_safety_stop(self):
        from search import VectorSearch
        self.ranking_fixture()
        index=VectorSearch([as_guide(row) for row in self.memory.list('verified')],RankingEncoder(),self.path.with_suffix('.vectors.json'))
        names=('_rerank_same_category','_rerank_unsolicited_approval','_rerank_credential_threat',
               '_rerank_mailbox_capacity','_apply_request_scope')
        with ExitStack() as stack:
            for name in names:
                stack.enter_context(patch('search.'+name,side_effect=AssertionError('PoC heuristic called')))
            pure=index.query('VPN E42, verkkosivut toimivat.',apply_poc_heuristics=False)
        self.assertTrue(pure['hits'])
        with patch('search.encoder',side_effect=AssertionError('Model loaded')):
            self.assertEqual(self.memory.search('Akku on turvonnut.','vector',filters=ENV)['state'],'safety_stop')

    def test_review_only_results_explicitly_have_no_compatible_candidates(self):
        self.verified(product_version=None)
        for backend in ('keyword','vector'):
            result=self.memory.search('VPN E42',backend,FakeEncoder(),filters=ENV)
            self.assertEqual(result['compatible_hits'],[])
            self.assertEqual(result['review_hits'],result['hits'])
            self.assertIn('yhteensopivia ehdokkaita ei löytynyt',result['message'])
            self.assertTrue(result['hits'])

    def test_groups_are_complete_disjoint_subsequences_of_vector_order(self):
        self.verified()
        self.verified(product_version=None)
        result=self.memory.search('VPN E42','vector',FakeEncoder(),filters=ENV)
        compatible=result['compatible_hits'];review=result['review_hits']
        self.assertEqual(len(compatible),1)
        self.assertEqual(len(review),1)
        self.assertEqual({hit['record']['id'] for hit in result['hits']},
                         {hit['record']['id'] for hit in compatible+review})
        self.assertEqual(compatible,[hit for hit in result['hits'] if hit['environment_check']['status']=='declared_match'])
        no_filters=self.memory.search('VPN E42','vector',FakeEncoder())
        self.assertEqual(no_filters['compatible_hits'],[])
        self.assertEqual(len(no_filters['review_hits']),2)
        empty=self.memory.search('VPN E42',filters=dict(ENV,operating_system='Android 15'))
        self.assertEqual(empty['compatible_hits'],[])
        self.assertEqual(empty['review_hits'],[])

    def test_safety_stop_precedes_model_and_database_access(self):
        with patch('search.encoder', side_effect=AssertionError('Model loaded')):
            result = self.memory.search('VPN ei toimi ja akku on turvonnut.','vector',filters=ENV)
        self.assertEqual(result['state'],'safety_stop')
        self.assertFalse(self.path.exists())


if __name__ == '__main__':
    unittest.main()
