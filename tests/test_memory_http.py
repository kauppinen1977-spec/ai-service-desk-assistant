import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import patch

import app
from test_solution_memory import SAMPLE


class MemoryHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = patch('solution_memory.DB_PATH', Path(self.temp.name) / 'memory.sqlite3')
        self.db.start()
        self.server = HTTPServer(('127.0.0.1', 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.db.stop()
        self.temp.cleanup()

    def post(self, action, obj, token=app.TOKEN):
        request = urllib.request.Request(self.url + '/api/memory/' + action,
                                        data=json.dumps(obj).encode(),
                                        headers={'X-Desk-Token': token, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_complete_save_verify_search_retire_workflow(self):
        status, saved = self.post('save', SAMPLE)
        self.assertEqual(status, 200)
        row = saved['record']
        self.assertEqual(self.post('search', {'query': 'VPN E42'})[1]['hits'], [])
        status, verified = self.post('verify', dict(id=row['id'], revision=row['revision'],
                                                  confirmed=True, verified_by='HTTP-testaaja'))
        self.assertEqual(status, 200)
        self.assertEqual(self.post('search', {'query': 'VPN E42'})[1]['hits'][0]['record']['id'], row['id'])
        self.assertEqual(self.post('retire', dict(id=row['id'], revision=verified['record']['revision'],
                                                reason='Vanhentunut'))[0], 200)
        self.assertEqual(self.post('search', {'query': 'VPN E42'})[1]['hits'], [])
        self.assertEqual(self.post('list', {})[1]['records'][0]['status'], 'retired')

    def test_every_memory_action_requires_session_token(self):
        for action in ('list', 'save', 'verify', 'retire', 'search', 'suggest'):
            self.assertEqual(self.post(action, {}, token='wrong')[0], 403)

    def test_ui_is_served_without_exposing_token_placeholder(self):
        with urllib.request.urlopen(self.url + '/memory') as response:
            page = response.read().decode()
        self.assertIn('Ratkaisumuisti', page)
        self.assertNotIn('__TOKEN__', page)
        self.assertIn(app.TOKEN, page)

    def test_unknown_action_and_missing_fields_fail_cleanly(self):
        self.assertEqual(self.post('nonexistent', {})[0], 404)
        self.assertEqual(self.post('save', {})[0], 400)


if __name__ == '__main__':
    unittest.main()
