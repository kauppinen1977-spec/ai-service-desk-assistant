import json,threading,unittest,urllib.request,urllib.error
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
if __name__=='__main__':unittest.main()
