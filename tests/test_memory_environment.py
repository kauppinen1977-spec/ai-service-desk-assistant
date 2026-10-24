import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from desk import DeskError
from solution_memory import ENVIRONMENT_FIELDS, Memory, database
from test_solution_memory import SAMPLE, FakeEncoder


ENV = dict(operating_system='Windows 11', product='AuroraVPN', product_version='5.2')


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

    def test_safety_stop_precedes_model_and_database_access(self):
        with patch('search.encoder', side_effect=AssertionError('Model loaded')):
            result = self.memory.search('VPN ei toimi ja akku on turvonnut.','vector',filters=ENV)
        self.assertEqual(result['state'],'safety_stop')
        self.assertFalse(self.path.exists())


if __name__ == '__main__':
    unittest.main()
