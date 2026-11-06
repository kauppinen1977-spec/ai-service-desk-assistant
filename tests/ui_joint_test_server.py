"""Disposable localhost browser-test server with synthetic SQLite and fake AI.

Run from the worktree, then set JOINT_TEST_BASE to the printed localhost URL
and run `node tests/ui_memory_browser_test.cjs --joint-db`. GET /test/shutdown
stops this test server and removes its temporary database.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from http.server import HTTPServer
from unittest.mock import patch

os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
os.environ.pop('OPENAI_API_KEY', None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app
from solution_memory import Memory


def no_outbound(event, args):
    if event in ('socket.connect', 'socket.sendto'):
        raise RuntimeError('Outbound networking is disabled in the synthetic test server')


def main():
    sys.addaudithook(no_outbound)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'synthetic.sqlite3'
        memory = Memory(path)
        row = memory.save(dict(title='Harjoituslaitteen näyttö jumittaa', problem='Näyttö jumittaa',
                               environment='Windows 11', solution='Tarkista laite.', operating_system='Windows 11'))
        memory.transition(dict(id=row['id'], revision=row['revision'], confirmed=True,
                               verified_by='Selaintesti'), 'verified')
        fake = dict(title='Harjoitusehdotus', solution='Tarkista liitäntä.',
                    limitations='Mallia ei vahvistettu.', commands=[], links=[])

        class Handler(app.Handler):
            def do_GET(self):
                if self.path == '/test/count':
                    rows = Memory(path).list()
                    return self.reply(200, json.dumps({'total': len(rows),
                                                      'drafts': sum(r['status'] == 'draft' for r in rows)}))
                if self.path == '/test/shutdown':
                    self.reply(200, '{}')
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                return super().do_GET()

        with patch('solution_memory.DB_PATH', path), \
             patch('joint_search_prototype.encoder', side_effect=RuntimeError('synthetic model failure')), \
             patch('desk.request_model', side_effect=lambda *args, **kwargs: dict(fake)):
            server = HTTPServer(('127.0.0.1', 0), Handler)
            print(f'TEST_URL http://127.0.0.1:{server.server_port}', flush=True)
            try:
                server.serve_forever()
            finally:
                server.server_close()


if __name__ == '__main__':
    main()
