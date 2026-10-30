import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from desk import DeskError
from solution_memory import Memory
from test_solution_memory import FakeEncoder, SAMPLE
from test_memory_tools import COMMAND, LINK


class DeleteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'memory.sqlite3'
        self.memory = Memory(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def create_verified(self, title):
        row = self.memory.save(dict(SAMPLE, title=title, tools={'commands': [COMMAND], 'links': [LINK]}))
        return self.memory.transition(dict(id=row['id'], revision=row['revision'], confirmed=True, verified_by='Testi'), 'verified')

    def test_verified_and_retired_delete_preserves_other_records_and_invalidates_cache(self):
        keep = self.create_verified('Säilytettävä VPN')
        removed = self.create_verified('Poistettava VPN')
        before = self.memory.search('VPN E42', backend='vector', model=FakeEncoder())
        self.assertIn(removed['id'], [hit['record']['id'] for hit in before['hits']])
        cache = self.path.with_suffix('.vectors.json')
        self.assertTrue(cache.exists())
        with self.assertRaises(DeskError):
            self.memory.delete_permanently(dict(id=removed['id'], revision=removed['revision'], confirmation_title='väärä'))
        with self.assertRaises(DeskError) as conflict:
            self.memory.delete_permanently(dict(id=removed['id'], revision=removed['revision']-1, confirmation_title=removed['title']))
        self.assertEqual(conflict.exception.status, 409)
        self.assertTrue(cache.exists())
        self.assertEqual(self.memory.delete_permanently(dict(id=removed['id'], revision=removed['revision'], confirmation_title=removed['title']))['deleted_id'], removed['id'])
        self.assertFalse(cache.exists())
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('select count(*) from solution_versions where solution_id=?', (removed['id'],)).fetchone()[0], 0)
            self.assertEqual(db.execute('select count(*) from solution_tools_history where solution_id=?', (removed['id'],)).fetchone()[0], 0)
        db.close()
        self.assertEqual(Memory(self.path).list(), [keep])
        for backend in ('keyword', 'vector'):
            result = Memory(self.path).search('VPN E42', backend=backend, model=FakeEncoder())
            ids = [hit['record']['id'] for hit in result['hits']]
            self.assertNotIn(removed['id'], ids)
            self.assertIn(keep['id'], ids)
        retired = self.create_verified('Poistettu käytöstä')
        retired = self.memory.transition(dict(id=retired['id'], revision=retired['revision'], reason='Harjoitus'), 'retired')
        self.memory.delete_permanently(dict(id=retired['id'], revision=retired['revision'], confirmation_title=retired['title']))
        self.assertEqual(Memory(self.path).list(), [keep])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('select count(*) from solution_versions where solution_id=?', (retired['id'],)).fetchone()[0], 0)
        db.close()

    def test_rollback_when_cache_or_transaction_fails(self):
        row = self.create_verified('Testi')
        args = dict(id=row['id'], revision=row['revision'], confirmation_title=row['title'])
        with patch('pathlib.Path.unlink', side_effect=PermissionError('busy')):
            with self.assertRaises(DeskError):
                self.memory.delete_permanently(args)
        self.assertEqual(self.memory.list()[0], row)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER reject_delete BEFORE DELETE ON solutions BEGIN SELECT RAISE(ABORT, 'test'); END")
        db.close()
        with self.assertRaises(sqlite3.IntegrityError):
            self.memory.delete_permanently(args)
        self.assertEqual(self.memory.list()[0], row)
        self.assertEqual(len(self.memory.versions(row['id'])['versions']), 1)


if __name__ == '__main__':
    unittest.main()
