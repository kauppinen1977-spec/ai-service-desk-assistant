import io,json,threading,unittest,urllib.request,urllib.error
from unittest.mock import patch
from http.server import HTTPServer
import app
from desk import DeskError
class HTTPTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=HTTPServer(('127.0.0.1',0),app.Handler);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.url='http://127.0.0.1:'+str(cls.server.server_port)
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
 def post(self,body,token=app.TOKEN):
  req=urllib.request.Request(self.url+'/api/answer',data=body,headers={'Content-Type':'application/json','X-Desk-Token':token})
  try:
   with urllib.request.urlopen(req,timeout=5) as r:return r.status,json.load(r)
  except urllib.error.HTTPError as e:return e.code,json.load(e)
 def test_expired_session(self):
  status,d=self.post(b'{}','wrong');self.assertEqual(status,403);self.assertEqual(d['code'],'session_expired')
 def test_invalid_json(self):
  status,d=self.post(b'{');self.assertEqual(status,400);self.assertEqual(d['code'],'invalid_request')
 def test_provider_error_is_actionable(self):
  with patch('app.answer',side_effect=DeskError('API-avain ei kelpaa.','invalid_api_key',502,'Aseta avain uudelleen.')):
   status,d=self.post(b'{"ticket":"VPN ei toimi"}')
  self.assertEqual(status,502);self.assertEqual(d['code'],'invalid_api_key');self.assertTrue(d['help'])
 def test_unexpected_error_does_not_leak(self):
  with patch('app.answer',side_effect=RuntimeError('private-test-key')):
   status,d=self.post(b'{"ticket":"VPN ei toimi"}')
  self.assertEqual(status,500);self.assertNotIn('private-test-key',json.dumps(d))
 def test_actual_keyword_search_mode(self):
  status,d=self.post(b'{"ticket":"VPN ei toimi","mode":"demo","backend":"keyword"}')
  self.assertEqual(status,200);self.assertEqual(d['result']['state'],'candidates');self.assertEqual(d['result']['steps'],[])


class RejectedPostTests(unittest.TestCase):
    @staticmethod
    def handler(path, body, token, declared_size=None):
        # Exercise the real response writer without timing-dependent TCP resets.
        handler = app.Handler.__new__(app.Handler)
        handler.path = path
        handler.command = 'POST'
        handler.request_version = 'HTTP/1.0'
        handler.requestline = f'POST {path} HTTP/1.0'
        handler.headers = {'Content-Length': str(len(body) if declared_size is None else declared_size)}
        if token is not None:
            handler.headers['X-Desk-Token'] = token
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()
        return handler

    def test_expired_session_consumes_body_before_403_without_decoding_or_dispatch(self):
        # Unread POST bytes when replying caused intermittent WinError 10053.
        # Invalid JSON must still yield session_expired, without parsing it.
        body = b'not-json:' + b'x' * 8192
        paths = ['/api/answer'] + ['/api/memory/' + action for action in
                                 ('list', 'save', 'verify', 'retire', 'search', 'suggest')]
        for path in paths:
            for token in ('wrong', None):
                with self.subTest(path=path, token=token):
                    handler = self.handler(path, body, token)

                    class ResponseAfterBody(io.BytesIO):
                        def write(buffer, data):
                            if handler.rfile.tell() != len(body):
                                raise AssertionError('HTTP response sent with unread POST body')
                            return super().write(data)

                    handler.wfile = ResponseAfterBody()
                    with patch('app.json.loads', side_effect=AssertionError('Unauthorized JSON decoded')) as decode, \
                         patch('app.answer') as answer, patch('solution_memory.dispatch') as dispatch:
                        handler.do_POST()
                    headers, _, payload = handler.wfile.getvalue().partition(b'\r\n\r\n')
                    self.assertTrue(headers.startswith(b'HTTP/1.0 403 '))
                    self.assertEqual(json.loads(payload)['code'], 'session_expired')
                    decode.assert_not_called()
                    answer.assert_not_called()
                    dispatch.assert_not_called()

    def test_oversized_unauthenticated_body_is_rejected_without_reading(self):
        for path, limit in (('/api/answer', 20000), ('/api/memory/save', 120000)):
            with self.subTest(path=path):
                handler = self.handler(path, b'', 'wrong', declared_size=limit + 1)
                with patch.object(handler.rfile, 'read', side_effect=AssertionError('Oversized body read')) as read, \
                     patch('app.answer') as answer, patch('solution_memory.dispatch') as dispatch:
                    handler.do_POST()
                headers, _, payload = handler.wfile.getvalue().partition(b'\r\n\r\n')
                self.assertTrue(headers.startswith(b'HTTP/1.0 400 '))
                self.assertIn('error', json.loads(payload))
                read.assert_not_called()
                answer.assert_not_called()
                dispatch.assert_not_called()

if __name__=='__main__':unittest.main()
