"""Fail-closed access checks without importing the optional UI dependency."""

import base64
import unittest

from ravel.web import PersonalAccess, settings


class PersonalWebTests(unittest.IsolatedAsyncioTestCase):
    async def request(self, path='/', method='GET', *, kind='http', auth=True, origin=None):
        self.reached = False

        async def application(scope, receive, send):
            self.reached = True
            if kind == 'websocket':
                await send({'type': 'websocket.accept'})
            else:
                await send({'type': 'http.response.start', 'status': 200, 'headers': []})
                await send({'type': 'http.response.body', 'body': b'private'})

        messages = []

        async def send(message):
            messages.append(message)

        async def receive():
            return {'type': 'websocket.connect' if kind == 'websocket' else 'http.request'}

        headers = [(b'host', b'ravel.example')]
        if auth:
            headers.append((b'authorization', b'Basic ' + base64.b64encode(b'fixture:invented-test-password')))
        if origin is not None:
            headers.append((b'origin', origin))
        await PersonalAccess(application, username='fixture', password='invented-test-password')(
            {'type': kind, 'path': path, 'method': method, 'headers': headers}, receive, send)
        return messages

    async def test_all_http_surfaces_require_access_before_routing(self):
        for method, path in [('GET', '/'), ('POST', '/_nicegui/client/upload/element'),
                             ('GET', '/_nicegui/download/opaque'), ('GET', '/favicon.ico'),
                             ('GET', '/_nicegui_ws/socket.io/?transport=polling')]:
            with self.subTest(path=path):
                messages = await self.request(path, method, auth=False)
                self.assertEqual(messages[0]['status'], 401)
                self.assertFalse(self.reached)

    async def test_wrong_and_malformed_credentials_are_rejected(self):
        gate = PersonalAccess(None, username='fixture', password='invented-test-password')
        for value in [b'', b'Bearer abc', b'Basic !!!', b'Basic bm9jb2xvbg==',
                      b'Basic ' + base64.b64encode(b'fixture:wrong'),
                      b'Basic ' + base64.b64encode(b'wrong:invented-test-password')]:
            self.assertFalse(gate.authorized({b'authorization': value}))

    async def test_authorized_response_is_private(self):
        messages = await self.request()
        self.assertTrue(self.reached)
        self.assertIn((b'cache-control', b'no-store'), messages[0]['headers'])

    async def test_health_is_generic_and_only_get_head_are_exempt(self):
        for method in ['GET', 'HEAD']:
            messages = await self.request('/healthz', method, auth=False)
            self.assertEqual(messages[0]['status'], 200)
            self.assertFalse(self.reached)
            self.assertEqual(messages[1]['body'], b'ok' if method == 'GET' else b'')
        self.assertEqual((await self.request('/healthz', 'POST', auth=False))[0]['status'], 401)

    async def test_websocket_needs_both_access_and_same_origin(self):
        for auth, origin in [(False, b'https://ravel.example'), (True, None),
                             (True, b'https://another.example')]:
            messages = await self.request(kind='websocket', auth=auth, origin=origin)
            self.assertEqual(messages[0]['type'], 'websocket.close')
            self.assertFalse(self.reached)
        messages = await self.request(kind='websocket', origin=b'https://ravel.example')
        self.assertEqual(messages[0]['type'], 'websocket.accept')
        self.assertTrue(self.reached)

    async def test_cross_origin_upload_and_polling_are_rejected(self):
        for path in ['/_nicegui/client/upload/element', '/_nicegui_ws/socket.io/']:
            messages = await self.request(path, 'POST', origin=b'https://another.example')
            self.assertEqual(messages[0]['status'], 403)
            self.assertFalse(self.reached)

    def test_hosting_configuration_fails_closed_without_exposing_values(self):
        for env in [{}, {'RAVEL_AUTH_USERNAME': 'fixture'},
                    {'RAVEL_AUTH_USERNAME': 'fixture', 'RAVEL_AUTH_PASSWORD': 'short'},
                    {'RAVEL_AUTH_USERNAME': 'a:b', 'RAVEL_AUTH_PASSWORD': 'invented-test-password'}]:
            with self.assertRaises(ValueError):
                settings(env)
        env = {'RAVEL_AUTH_USERNAME': 'fixture', 'RAVEL_AUTH_PASSWORD': 'invented-test-password'}
        self.assertEqual(settings(env)[2], 10000)
        self.assertEqual(settings({**env, 'PORT': '8765'})[2], 8765)
        for port in ['zero', '0', '65536']:
            with self.assertRaises(ValueError):
                settings({**env, 'PORT': port})
