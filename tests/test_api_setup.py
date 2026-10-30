"""API onboarding tests: synthetic responses only; external networking is forbidden."""
import io
import json
import os
import socket
import ssl
import unittest
import urllib.error
from unittest.mock import Mock, patch

import app
import desk
from api_settings import APISettings
import test_http


PROPOSAL = {'title': 'Kuvitteellinen zoomaus', 'solution': 'Palauta zoomaus 100 prosenttiin.',
            'limitations': 'Kokeilematon harjoitusehdotus.', 'commands': [], 'links': []}
REQUEST = {'problem': 'Harjoitussivu näkyy liian pienenä.', 'environment': 'Kuvitteellinen selain.',
           'send_to_api': True}
FAKE_KEY = 'fixture-secret-not-a-real-key'


def response(value=PROPOSAL):
    return io.BytesIO(json.dumps({'status': 'completed', 'output': [
        {'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(value)}]}]}).encode())


def web_source_response(url='https://support.example.com/help'):
    return io.BytesIO(json.dumps({'status':'completed','output':[
        {'type':'web_search_call','status':'completed','action':{'type':'search','sources':[{'url':url,'title':'Support'}]}},
        {'type':'message','content':[{'type':'output_text','text':'Relevant support results.','annotations':[]}]}]}).encode())


def provider_failure(status, code=None, kind=None, raw=None):
    body = raw if raw is not None else json.dumps({'error': {
        'code': code, 'type': kind, 'message': FAKE_KEY, 'param': FAKE_KEY}}).encode()
    return urllib.error.HTTPError('https://api.openai.com/v1/responses', status, FAKE_KEY, {}, io.BytesIO(body))


class APISetupTests(unittest.TestCase):
    def setUp(self):
        self.settings = APISettings()
        self.env = patch.dict(os.environ, {'OPENAI_API_KEY': '', 'OPENAI_MODEL': 'gpt-4.1-mini'})
        self.env.start()
        self.addCleanup(self.env.stop)
        for target in ('app.settings', 'desk.settings'):
            p = patch(target, self.settings)
            p.start()
            self.addCleanup(p.stop)
        # Even a missed mock cannot make a real API connection in these tests.
        p = patch('socket.create_connection', side_effect=AssertionError('External networking forbidden'))
        p.start()
        self.addCleanup(p.stop)

    def post(self, action, obj, token=app.TOKEN):
        handler = test_http.RejectedPostTests.handler('/api/memory/' + action, json.dumps(obj).encode(), token)
        handler.do_POST()
        headers, _, raw = handler.wfile.getvalue().partition(b'\r\n\r\n')
        return int(headers.split()[1]), json.loads(raw), headers

    def configure(self, key=FAKE_KEY, model='gpt-4.1-mini'):
        return self.post('api-settings', {'api_key': key, 'model': model})

    def test_update_status_and_clear_never_open_database_or_return_secret(self):
        with patch('solution_memory.Memory', side_effect=AssertionError('Settings must not use DB')), \
             patch('desk.open_model', side_effect=AssertionError('Settings must not call API')):
            status, state, headers = self.configure('  ' + FAKE_KEY + '  ')
            self.assertEqual(status, 200)
            self.assertEqual(state['source'], 'local')
            self.assertEqual(state['persistence'], 'process_memory')
            self.assertEqual(state['last_result'], 'not_tested')
            self.assertNotIn(FAKE_KEY, json.dumps(state))
            self.assertIn(b'Cache-Control: no-store', headers)
            self.assertEqual(self.post('api-status', {})[1], state)
            self.assertEqual(self.post('api-settings', {'clear': True})[1]['configured'], False)

    def test_inherited_environment_override_and_restart_semantics(self):
        os.environ['OPENAI_API_KEY'] = 'inherited-fixture'
        self.assertEqual(self.settings.status()['source'], 'environment')
        self.configure()
        self.assertEqual(os.environ['OPENAI_API_KEY'], 'inherited-fixture')
        self.assertEqual(self.settings.snapshot()[0], FAKE_KEY)
        self.post('api-settings', {'clear': True})
        self.assertFalse(self.settings.status()['configured'])
        self.assertEqual(APISettings().snapshot()[0], 'inherited-fixture')

    def test_settings_and_status_require_valid_session(self):
        for action in ('api-status', 'api-settings'):
            for token in (None, 'wrong'):
                self.assertEqual(self.post(action, {'api_key': FAKE_KEY}, token)[0], 403)
        self.assertFalse(self.settings.status()['configured'])

    def test_foreign_hostname_cannot_read_local_page_or_token(self):
        handler = test_http.RejectedPostTests.handler('/memory', b'', None)
        handler.headers['Host'] = 'attacker.invalid:8502'
        handler.do_GET()
        raw = handler.wfile.getvalue()
        self.assertTrue(raw.startswith(b'HTTP/1.0 403 '))
        self.assertNotIn(app.TOKEN.encode(), raw)

    def test_invalid_key_format_is_local_and_does_not_replace_setting(self):
        self.configure()
        for value in ('', ' ', 'a b', 'a\nb', '"quoted"', "'quoted'", 'ä', 42, None, 'x' * 513):
            with self.subTest(value_type=type(value).__name__):
                status, result, _ = self.post('api-settings', {'api_key': value})
                self.assertEqual(status, 400)
                self.assertEqual(result['code'], 'invalid_key_format')
                self.assertEqual(self.settings.snapshot()[0], FAKE_KEY)
        self.assertEqual(self.configure(model=FAKE_KEY + ' invalid')[0], 400)

    def test_missing_key_does_not_call_provider(self):
        with patch('desk.open_model') as provider:
            status, result, _ = self.post('suggest', REQUEST)
        self.assertEqual(status, 400)
        self.assertEqual(result['code'], 'missing_api_key')
        self.assertIn('API-asetukset', result['help'])
        provider.assert_not_called()

    def test_malformed_inherited_key_is_a_local_setting_error(self):
        for key in ('"quoted-fixture"', 'fixture\nheader', 'fixture with spaces', 'ä'):
            os.environ['OPENAI_API_KEY'] = key
            with patch('desk.open_model') as provider:
                self.assertEqual(self.post('suggest', REQUEST)[1]['code'], 'invalid_key_format')
            provider.assert_not_called()

    def test_rotation_applies_to_next_request_and_request_is_correct(self):
        seen = []

        def fake(request, timeout):
            seen.append((request, timeout))
            return response()

        with patch('desk.open_model', side_effect=fake), patch('solution_memory.Memory') as memory:
            for key, model in ((FAKE_KEY, 'gpt-4.1-mini'), ('rotated-fixture', 'fixture-model')):
                self.configure(key, model)
                status, result, _ = self.post('suggest', dict(REQUEST, api_key='never-send-extra'))
                self.assertEqual(status, 200)
                self.assertEqual(result['state'], 'unverified')
                self.assertEqual(result['suggestion'], dict(PROPOSAL, web_search=False, additional_instructions=''))
                request, timeout = seen[-1]
                self.assertEqual(request.full_url, 'https://api.openai.com/v1/responses')
                self.assertEqual(request.method, 'POST')
                self.assertEqual(request.get_header('Authorization'), 'Bearer ' + key)
                self.assertEqual(timeout, 45)
                payload = json.loads(request.data)
                self.assertEqual(payload['model'], model)
                self.assertFalse(payload['store'])
                self.assertEqual(json.loads(payload['input']), {k: REQUEST[k] for k in ('problem', 'environment')})
                self.assertNotIn(key, request.data.decode())
                self.assertNotIn('never-send-extra', request.data.decode())
                self.assertEqual(payload['text']['format']['type'], 'json_schema')
                self.assertEqual(self.settings.status()['last_result'], 'success')
            memory.return_value.save.assert_not_called()

    def test_provider_error_matrix_and_redaction(self):
        self.configure()
        cases = [(401, 'invalid_api_key', None, 'invalid_api_key'),
                 (401, None, None, 'api_authentication'),
                 (401, 'ip_not_authorized', None, 'api_forbidden'),
                 (403, 'insufficient_permissions', None, 'api_forbidden'),
                 (403, None, None, 'api_forbidden'),
                 (404, 'model_not_found', None, 'api_model_access'),
                 (403, 'model_access_denied', None, 'api_model_access'),
                 (404, None, None, 'api_not_found'),
                 (429, 'insufficient_quota', None, 'api_billing'),
                 (429, 'credit_balance_exhausted', None, 'api_billing'),
                 (429, 'project_spend_limit_exceeded', None, 'api_billing'),
                 (429, 'organization_spend_limit_exceeded', None, 'api_billing'),
                 (429, 'organization_usage_limit_exceeded', None, 'api_billing'),
                 (429, None, 'insufficient_quota', 'api_billing'),
                 (429, 'rate_limit_exceeded', None, 'api_rate_limit'),
                 (400, 'invalid_json_schema', None, 'api_bad_request'),
                 (422, None, None, 'api_bad_request'),
                 (500, None, None, 'api_unavailable'),
                 (503, 'server_is_overloaded', None, 'api_unavailable'),
                 (307, None, None, 'api_redirect'),
                 (401, FAKE_KEY, FAKE_KEY, 'api_authentication')]
        for upstream, code, kind, expected in cases:
            with self.subTest(upstream=upstream, expected=expected):
                with patch('desk.open_model', side_effect=provider_failure(upstream, code, kind)) as provider:
                    status, result, _ = self.post('suggest', REQUEST)
                self.assertEqual(status, 502)
                self.assertEqual(result['code'], expected)
                self.assertEqual(result['upstream_status'], upstream)
                self.assertNotIn(FAKE_KEY, json.dumps(result))
                self.assertTrue(result['help'])
                self.assertEqual(provider.call_count, 1)
                self.assertEqual(self.settings.status()['last_result'], expected)

    def test_gpt41mini_web_search_does_not_reintroduce_filters_after_old_rejection(self):
        self.configure()
        body={'error':{'message':"Parameter 'filters' not supported with model 'gpt-4.1-mini'",'type':'invalid_request_error','code':None,'param':'tools'}}
        with patch('desk.open_model', side_effect=provider_failure(400,raw=json.dumps(body).encode())) as provider:
            status,result,_=self.post('suggest',dict(REQUEST,web_search=True,vendor_domain='microsoft.com'))
        self.assertEqual(status,502)
        self.assertEqual(result['code'],'api_bad_request')
        self.assertEqual(result['provider_param'],'tools')
        self.assertEqual(result['provider_code'],'ei ilmoitettu')
        self.assertIn('gpt-4.1-mini',result['provider_description'])
        self.assertIn('Sovellus tarkistaa valmistajan verkkotunnuksen',result['help'])
        provider.assert_called_once()
        payload=json.loads(provider.call_args.args[0].data)
        self.assertEqual(payload['model'],'gpt-4.1-mini')
        self.assertEqual(payload['tools'],[{'type':'web_search'}])
        self.assertEqual(payload['include'],['web_search_call.action.sources'])
        self.assertIsInstance(payload['input'],str)
        self.assertNotIn('text',payload)

    def test_web_search_preserves_selected_model_and_omits_filters(self):
        for model in ('gpt-4.1-mini','custom-fixture-model'):
            self.configure(model=model)
            with self.subTest(model=model), patch('desk.open_model',side_effect=[web_source_response(),response()]) as provider:
                status,search,_=self.post('suggest',dict(REQUEST,web_search=True,vendor_domain='example.com',web_stage='search'))
                self.assertEqual(status,200);self.assertEqual(search['state'],'web_sources_ready')
                status,result,_=self.post('suggest',dict(REQUEST,web_search=True,vendor_domain='example.com',web_stage='compose',source_request_id=search['source_request_id']))
                self.assertEqual(status,200);self.assertEqual(result['suggestion']['links'],[])
                first,second=[json.loads(call.args[0].data) for call in provider.call_args_list]
                self.assertEqual(first['model'],model);self.assertEqual(first['tools'],[{'type':'web_search'}])
                self.assertEqual(first['include'],['web_search_call.action.sources']);self.assertNotIn('text',first)
                self.assertEqual(second['model'],model);self.assertNotIn('tools',second)
                self.assertEqual(second['text']['format']['type'],'json_schema')
                provider.assert_has_calls(provider.call_args_list)
                self.assertEqual(provider.call_count,2)

    def test_unreadable_error_bodies_do_not_become_invalid_key(self):
        self.configure()
        for raw in (b'not JSON', b'[]', b'{"error":null}', b'{"error":{"code":[],"type":{}}}', b'x' * 65537):
            with patch('desk.open_model', side_effect=provider_failure(401, raw=raw)):
                self.assertEqual(self.post('suggest', REQUEST)[1]['code'], 'api_authentication')

    def test_safe_provider_diagnostics_for_both_search_modes(self):
        self.configure()
        for web in (False, True):
            detail={'error':{'code':'invalid_json_schema','type':'invalid_request_error',
                             'param':'text.format.schema',
                             'message':'Invalid schema: '+FAKE_KEY+' Authorization: Bearer '+FAKE_KEY+' private prompt'}}
            with self.subTest(web=web), patch('desk.open_model', side_effect=provider_failure(400, raw=json.dumps(detail).encode())) as provider:
                status,result,_=self.post('suggest',dict(REQUEST,web_search=web,vendor_domain='example.com'))
                self.assertEqual(status,502)
                self.assertEqual(result['provider_code'],'invalid_json_schema')
                self.assertEqual(result['provider_param'],'text.format.schema')
                self.assertIn('vastausskeeman',result['provider_description'])
                self.assertNotIn(FAKE_KEY,json.dumps(result))
                self.assertNotIn('private prompt',json.dumps(result))
                payload=json.loads(provider.call_args.args[0].data)
                self.assertEqual(payload['model'],'gpt-4.1-mini')
                if web:
                    self.assertEqual(payload['tools'],[{'type':'web_search'}])
                    self.assertEqual(payload['include'],['web_search_call.action.sources'])
                    self.assertEqual(payload['tool_choice'],'required')
                    self.assertNotIn('text',payload)
                else:
                    self.assertEqual(payload['text']['format']['type'],'json_schema')
                    self.assertNotIn('tools',payload)
                provider.assert_called_once()

    def test_unknown_provider_fields_and_unsafe_description_are_not_reflected(self):
        self.configure()
        detail={'error':{'code':FAKE_KEY,'param':'input.'+FAKE_KEY,'message':'Authorization: Bearer '+FAKE_KEY+' private prompt'}}
        with patch('desk.open_model', side_effect=provider_failure(400, raw=json.dumps(detail).encode())):
            _,result,_=self.post('suggest',REQUEST)
        self.assertEqual(result['provider_code'],'ei turvallisesti näytettävissä')
        self.assertEqual(result['provider_param'],'ei turvallisesti näytettävissä')
        self.assertNotIn(FAKE_KEY,json.dumps(result))
        self.assertNotIn('private prompt',json.dumps(result))

    def test_tools_rejection_exposes_only_safe_compatibility_terms(self):
        self.configure()
        for message,terms in [('Unsupported web_search with json_schema. Secret '+FAKE_KEY, ['web_search','json_schema']),
                              ('Unsupported tool. '+FAKE_KEY, [])]:
            detail={'error':{'code':None,'type':'invalid_request_error','param':'tools','message':message}}
            with self.subTest(message=message[:20]), patch('desk.open_model', side_effect=provider_failure(400,raw=json.dumps(detail).encode())) as provider:
                status,result,_=self.post('suggest',dict(REQUEST,web_search=True,vendor_domain='example.com'))
            self.assertEqual(status,502)
            self.assertEqual(result['provider_code'],'ei ilmoitettu')
            self.assertEqual(result['provider_param'],'tools')
            self.assertEqual(result['provider_terms'],terms)
            self.assertNotIn(FAKE_KEY,json.dumps(result))
            provider.assert_called_once()

    def test_network_errors_and_timeouts_never_become_key_errors(self):
        self.configure()
        cases = [(TimeoutError(FAKE_KEY), 'api_timeout', 504),
                 (urllib.error.URLError(socket.timeout(FAKE_KEY)), 'api_timeout', 504),
                 (urllib.error.URLError(socket.gaierror(FAKE_KEY)), 'api_connection', 502),
                 (urllib.error.URLError(ssl.SSLError(FAKE_KEY)), 'api_connection', 502),
                 (OSError(FAKE_KEY), 'api_connection', 502)]
        for error, code, expected_status in cases:
            with patch('desk.open_model', side_effect=error) as provider:
                status, result, _ = self.post('suggest', REQUEST)
            self.assertEqual((status, result['code']), (expected_status, code))
            self.assertNotIn(FAKE_KEY, json.dumps(result))
            self.assertEqual(provider.call_count, 1)

    def test_invalid_and_incomplete_responses_do_not_overwrite_drafts(self):
        self.configure()
        cases = [(b'not JSON', 'api_format'), (b'x' * 1000001, 'api_format'),
                 (b'{"status":"incomplete","output":[]}', 'model_incomplete')]
        for raw, code in cases:
            with patch('desk.open_model', return_value=io.BytesIO(raw)):
                self.assertEqual(self.post('suggest', REQUEST)[1]['code'], code)
        with patch('desk.open_model', return_value=response({'title': 'incomplete'})):
            self.assertEqual(self.post('suggest', REQUEST)[1]['code'], 'invalid_model_output')

    def test_old_response_does_not_mark_rotated_setting_tested(self):
        self.configure()
        revision = self.settings.snapshot()[2]
        self.configure('rotated-fixture')
        self.settings.record(revision, 'success')
        self.assertEqual(self.settings.status()['last_result'], 'not_tested')

    def test_redirects_never_forward_credentials(self):
        req = Mock()
        self.assertIsNone(desk.NoAPIRedirect().redirect_request(req, None, 307, '', {}, 'https://example.invalid'))
        with patch('desk.urllib.request.build_opener') as build:
            desk.open_model(req, 45)
            self.assertIsInstance(build.call_args.args[0], desk.NoAPIRedirect)
            build.return_value.open.assert_called_once_with(req, timeout=45)


if __name__ == '__main__':
    unittest.main()
