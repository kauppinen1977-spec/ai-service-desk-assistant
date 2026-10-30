"""Exact static routes; no application DB or external network."""
import json
import threading
import unittest
import urllib.request
import urllib.error
from http.server import HTTPServer
from unittest.mock import patch
import app

class SOCStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=HTTPServer(('127.0.0.1',0),app.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base='http://127.0.0.1:'+str(cls.server.server_port)
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def get(self,path,host=None):
        req=urllib.request.Request(self.base+path,headers={'Host':host} if host else {})
        try:
            with urllib.request.urlopen(req,timeout=5) as res:return res.status,res.headers,res.read()
        except urllib.error.HTTPError as res:return res.code,res.headers,res.read()
    def test_css_and_banner_are_exact_bytes_with_correct_headers(self):
        for route,(filename,kind) in app.STATIC_FILES.items():
            with self.subTest(route=route):
                status,headers,body=self.get(route)
                self.assertEqual(status,200);self.assertTrue(headers['Content-Type'].startswith(kind))
                self.assertEqual(body,(app.ROOT/filename).read_bytes())
                self.assertEqual(int(headers['Content-Length']),len(body))
                self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
                self.assertEqual(headers['Cache-Control'],'no-store')
    def test_unknown_paths_traversal_database_and_source_are_not_served(self):
        for path in ['/app.py','/solution_memory.py','/.env','/.git','/data/solutions.sqlite3','/../soc-theme.css','/%2e%2e/soc-banner.jpg','/soc-theme.css/extra','/soc-banner.jpg?path=app.py','/SOC-THEME.CSS','/docs/13_ratkaisumuistin_pikaohje.md','/pikaohje/../app.py','/pikaohje?file=app.py','/pikaohje/extra']:
            with self.subTest(path=path):self.assertEqual(self.get(path)[0],404)
    def test_foreign_host_cannot_read_resources(self):
        for path in app.STATIC_FILES:self.assertEqual(self.get(path,'attacker.example')[0],403)
    def test_missing_resource_returns_404(self):
        with patch.dict(app.STATIC_FILES,{'/missing.css':('not-present.css','text/css')}):
            self.assertEqual(self.get('/missing.css')[0],404)
    def test_symlink_or_outside_resource_is_rejected(self):
        with patch('pathlib.Path.is_symlink',return_value=True):self.assertEqual(self.get('/soc-theme.css')[0],404)
        with patch.dict(app.STATIC_FILES,{'/outside.css':('../AGENTS.md','text/css')}):self.assertEqual(self.get('/outside.css')[0],404)
    def test_memory_keeps_token_and_only_approved_assets(self):
        status,_,body=self.get('/memory');html=body.decode('utf-8')
        self.assertEqual(status,200);self.assertIn(app.TOKEN,html);self.assertNotIn('__TOKEN__',html)
        self.assertIn('href="/soc-theme.css"',html);self.assertNotIn('soc-app.js',html)
        self.assertNotIn('localStorage',html)
        self.assertIn(app.APP_VERSION,html);self.assertNotIn('__BASE_VERSION__',html)
        self.assertEqual(app.APP_UPDATED,'29.10.2026');self.assertIn('Sovellus päivitetty: '+app.APP_UPDATED,html);self.assertNotIn('__APP_UPDATED__',html)
    def test_guide_is_exact_text_and_only_available_under_exact_local_route(self):
        status,headers,body=self.get('/pikaohje');self.assertEqual(status,200)
        self.assertTrue(headers['Content-Type'].startswith('text/plain'))
        self.assertEqual(body,(app.ROOT/'docs'/'13_ratkaisumuistin_pikaohje.md').read_bytes())
        self.assertEqual(self.get('/pikaohje','attacker.example')[0],403)
        with patch('pathlib.Path.is_symlink',return_value=True):self.assertEqual(self.get('/pikaohje')[0],404)

if __name__=='__main__':unittest.main()
