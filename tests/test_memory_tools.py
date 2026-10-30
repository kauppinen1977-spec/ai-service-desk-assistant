import sqlite3
import tempfile
import unittest
from pathlib import Path

from desk import DeskError
from solution_memory import Memory

BASE = dict(title='VPN testi', problem='VPN yhteys ei toimi E42', environment='Testi Windows', solution='Tarkista yhteys.')
COMMAND = dict(id='check-1', name='Päivämäärä', type='powershell', content='Get-Date\r\n# ääkköset <>&\r\n',
               description='Näyttää ajan.', environment='Windows', admin=False, effect='check', impact='', rollback='',
               test_status='human_tested', tested_by='Testaaja', tested_at='2026-10-29T12:00:00+02:00', test_environment='Windows 11')
LINK = dict(name='Ohje', url='https://example.org/help', purpose='Tuotteen ohje')


class ToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'memory.sqlite3'
        self.memory = Memory(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_legacy_database_migrates_without_losing_record(self):
        db = sqlite3.connect(self.path)
        db.execute('''CREATE TABLE solutions(id TEXT PRIMARY KEY,title TEXT NOT NULL,problem TEXT NOT NULL,environment TEXT NOT NULL,solution TEXT NOT NULL,status TEXT NOT NULL,revision INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,verified_at TEXT,verified_by TEXT,retirement_reason TEXT)''')
        db.execute('INSERT INTO solutions VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', ('old','Vanha','Ongelma','Ympäristö','Ratkaisu','retired',3,'a','b',None,None,'Syy'))
        db.commit(); db.close()
        row = self.memory.list()[0]
        self.assertEqual((row['id'], row['revision'], row['retirement_reason']), ('old', 3, 'Syy'))
        self.assertEqual(row['tools'], {'commands': [], 'links': []})
        self.assertEqual(self.memory.tools_history('old'), [])

    def test_roundtrip_change_reconfirmation_history_and_legacy_client(self):
        cmd = dict(COMMAND)
        second = dict(COMMAND, id='cmd-2', name='Versio', type='cmd', content='ver', test_status='untested', tested_by='', tested_at='', test_environment='')
        tools = {'commands': [cmd, second], 'links': [LINK]}
        created = self.memory.save(dict(BASE, tools=tools))
        self.assertEqual(Memory(self.path).list()[0]['tools'], tools)
        verified = self.memory.transition(dict(id=created['id'], revision=1, confirmed=True, verified_by='Tuki'), 'verified')
        changed = dict(COMMAND, content='Get-Date\n# muuttunut')
        updated = self.memory.save(dict(BASE, id=created['id'], revision=verified['revision'], tools={'commands': [changed, second], 'links': [LINK]}))
        self.assertEqual(updated['status'], 'draft')
        self.assertEqual(updated['tools']['commands'][0]['test_status'], 'untested')
        self.assertEqual(updated['tools']['commands'][0]['tested_by'], '')
        history = self.memory.tools_history(created['id'])
        self.assertTrue(any(h['tools']['commands'][0]['content'] == COMMAND['content'] for h in history if h['tools']['commands']))
        self.assertTrue(any(h['tools']['commands'][0]['content'] == changed['content'] for h in history if h['tools']['commands']))
        with self.assertRaises(DeskError):
            self.memory.save(dict(BASE, id=created['id'], revision=verified['revision'], tools=tools))
        confirmed = self.memory.transition(dict(id=created['id'], revision=updated['revision'], confirmed=True, verified_by='Tuki'), 'verified')
        self.assertEqual(confirmed['tools']['commands'][0]['test_status'], 'untested')
        legacy = self.memory.save(dict(BASE, id=created['id'], revision=confirmed['revision']))
        self.assertEqual(legacy['tools'], updated['tools'])

    def test_invalid_links_and_missing_impact_or_test_details_rejected(self):
        for url in ['javascript:alert(1)', 'data:text/html,hi', 'https://good.example@evil.example/', 'http://example.org\\@evil.org', 'https://example.org\n.evil', '//example.org']:
            with self.subTest(url=url), self.assertRaises(DeskError):
                self.memory.save(dict(BASE, tools={'commands': [], 'links': [dict(LINK, url=url)]}))
        for cmd in [dict(COMMAND, effect='change', impact='', rollback=''), dict(COMMAND, tested_by=''), dict(COMMAND, tested_at='2026-10-29')]:
            with self.subTest(cmd=cmd), self.assertRaises(DeskError):
                self.memory.save(dict(BASE, tools={'commands': [cmd], 'links': []}))
        change = dict(COMMAND, effect='change', impact='Asetus muuttuu', rollback='Palautusohjetta ei ole')
        self.assertEqual(self.memory.save(dict(BASE, tools={'commands': [change], 'links': []}))['tools']['commands'][0]['rollback'], 'Palautusohjetta ei ole')

    def test_blank_cards_are_ignored_and_partial_cards_are_rejected(self):
        blank = dict(COMMAND, name='', content='', description='', environment='', test_status='untested', tested_by='', tested_at='', test_environment='')
        tools = {'commands': [blank], 'links': [dict(name='', url=' ', purpose='')]}
        row = self.memory.save(dict(BASE, tools=tools))
        self.assertEqual(row['tools'], {'commands': [], 'links': []})
        self.assertEqual(Memory(self.path).list()[0]['tools'], row['tools'])
        for partial in [dict(blank, content='ver'), dict(blank, type='cmd')]:
            with self.subTest(partial=partial), self.assertRaises(DeskError):
                self.memory.save(dict(BASE, tools={'commands': [partial], 'links': []}))
        with self.assertRaises(DeskError):
            self.memory.save(dict(BASE, tools={'commands': [], 'links': [dict(name='Ohje', url='', purpose='')]}))


if __name__ == '__main__':
    unittest.main()
