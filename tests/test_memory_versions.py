import sqlite3
import tempfile
import unittest
from pathlib import Path

from desk import DeskError
from solution_memory import Memory

BASE = dict(title='Aiempi otsikko', problem='VPN ei toimi E42', environment='Testiympäristö', solution='Alkuperäinen ratkaisu')
COMMAND = dict(id='test-command', name='Tarkistus', type='powershell', content='Get-Date', description='Näyttää ajan', environment='Testikone', admin=False, effect='check', impact='', rollback='', test_status='human_tested', tested_by='Testi', tested_at='2026-10-29T10:00:00+02:00', test_environment='Testikone')


class VersionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'test.sqlite3'
        self.mem = Memory(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_full_snapshots_preserve_state_tools_and_conflict_rules(self):
        tools = {'commands': [COMMAND], 'links': [{'name': 'Ohje', 'url': 'https://example.org/', 'purpose': 'Testi'}]}
        first = self.mem.save(dict(BASE, tools=tools))
        second = self.mem.transition(dict(id=first['id'], revision=1, confirmed=True, verified_by='Testi'), 'verified')
        changed = dict(COMMAND, content='Get-Date\n# muutos')
        third = self.mem.save(dict(BASE, id=first['id'], revision=second['revision'], solution='Uusi ratkaisu', tools={'commands': [changed], 'links': tools['links']}))
        versions = self.mem.versions(first['id'])
        self.assertFalse(versions['older_versions_missing'])
        self.assertEqual([r['revision'] for r in versions['versions']], [2, 1])
        self.assertEqual(versions['versions'][0]['status'], 'verified')
        self.assertEqual(versions['versions'][0]['solution'], 'Alkuperäinen ratkaisu')
        self.assertEqual(versions['versions'][0]['tools'], tools)
        self.assertEqual(third['status'], 'draft')
        self.assertEqual(third['tools']['commands'][0]['test_status'], 'untested')
        with self.assertRaises(DeskError):
            self.mem.save(dict(BASE, id=first['id'], revision=second['revision']))
        self.assertEqual(len(self.mem.versions(first['id'])['versions']), 2)
        fourth = self.mem.transition(dict(id=first['id'], revision=third['revision'], confirmed=True, verified_by='Testi'), 'verified')
        self.mem.transition(dict(id=first['id'], revision=fourth['revision'], reason='Vanhentunut'), 'retired')
        self.assertFalse(self.mem.search('VPN E42')['hits'])
        self.assertEqual(len(self.mem.versions(first['id'])['versions']), 4)
        self.assertEqual(self.mem.list()[0]['retirement_reason'], 'Vanhentunut')

    def test_missing_legacy_versions_are_not_invented(self):
        row = self.mem.save(BASE)
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE solutions SET revision=5 WHERE id=?', (row['id'],))
        db.close()
        result = self.mem.versions(row['id'])
        self.assertEqual(result['versions'], [])
        self.assertTrue(result['older_versions_missing'])
        self.mem.save(dict(BASE, id=row['id'], revision=5, solution='Muokattu'))
        result = self.mem.versions(row['id'])
        self.assertEqual([r['revision'] for r in result['versions']], [5])
        self.assertTrue(result['older_versions_missing'])


if __name__ == '__main__':
    unittest.main()
