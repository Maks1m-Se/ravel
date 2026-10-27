"""Public hosting stays explicit and bounds work before engine execution."""

from copy import deepcopy
import unittest

from ravel.dataset import template
from ravel.recipe import ValidationError, new_recipe, validate
from ravel.web import DemoCapacity, MAX_REQUEST_BYTES, PersonalAccess, check_demo_recipe, settings


class PublicDemoTests(unittest.IsolatedAsyncioTestCase):
    async def call(self, *, kind='http', path='/', method='GET', origin=None, chunks=()):
        self.reached, self.body = False, b''

        async def application(scope, receive, send):
            self.reached = True
            if method == 'POST':
                self.body = (await receive())['body']
            await send({'type': 'websocket.accept'} if kind == 'websocket' else
                       {'type': 'http.response.start', 'status': 200, 'headers': []})

        incoming = iter({'type': 'http.request', 'body': chunk, 'more_body': i < len(chunks) - 1}
                        for i, chunk in enumerate(chunks))

        async def receive():
            return next(incoming)

        messages = []

        async def send(message):
            messages.append(message)

        headers = [(b'host', b'ravel.example')]
        if origin:
            headers.append((b'origin', origin))
        await PersonalAccess(application, username='', password='', public_demo=True)(
            dict(type=kind, path=path, method=method, headers=headers), receive, send)
        return messages

    async def test_public_pages_and_same_origin_socket_need_no_credentials(self):
        self.assertEqual((await self.call())[0]['status'], 200)
        self.assertTrue(self.reached)
        self.assertEqual((await self.call(kind='websocket', origin=b'https://ravel.example'))[0]['type'], 'websocket.accept')
        for origin in [None, b'https://another.example']:
            self.assertEqual((await self.call(kind='websocket', origin=origin))[0]['type'], 'websocket.close')
            self.assertFalse(self.reached)

    async def test_upload_framing_is_preserved_and_oversized_chunked_body_rejected(self):
        messages = await self.call(method='POST', chunks=(b'first', b'second'))
        self.assertEqual(messages[0]['status'], 200)
        self.assertEqual(self.body, b'firstsecond')
        messages = await self.call(method='POST', chunks=(b'x' * MAX_REQUEST_BYTES, b'x'))
        self.assertEqual(messages[0]['status'], 413)
        self.assertFalse(self.reached)
        messages = await self.call(method='POST', origin=b'https://another.example', chunks=(b'x',))
        self.assertEqual(messages[0]['status'], 403)
        self.assertFalse(self.reached)

    def test_public_access_requires_exact_explicit_flag(self):
        self.assertEqual(settings({'RAVEL_PUBLIC_DEMO': '1'}), ('', '', 10000))
        for env in [{}, {'RAVEL_PUBLIC_DEMO': '0'}, {'RAVEL_PUBLIC_DEMO': 'true'}, {'RAVEL_PUBLIC_DEMO': 'yes'}]:
            with self.assertRaises(ValueError):
                settings(env)

    def test_row_and_cell_bounds_cover_whole_dataset_without_changing_recipe(self):
        recipe = new_recipe()
        before = deepcopy(recipe)
        check_demo_recipe(recipe)
        self.assertEqual(recipe, before)
        recipe['table']['row_count'] = 1001
        with self.assertRaisesRegex(ValidationError, '1,000 rows'):
            check_demo_recipe(recipe)
        recipe['table']['row_count'] = 1000
        field = recipe['table']['fields'][0]
        recipe['table']['fields'] = [dict(field, id=f'c{i}', name=f'column{i}') for i in range(21)]
        validate(recipe)
        with self.assertRaisesRegex(ValidationError, '20,000 cells'):
            check_demo_recipe(recipe)
        linked = template()
        check_demo_recipe(linked)
        linked['tables'][0]['row_count'] = 400
        linked['tables'][1]['row_count'] = 800
        validate(linked)
        with self.assertRaisesRegex(ValidationError, '1,000 rows'):
            check_demo_recipe(linked)

    def test_capacity_and_rate_recover_including_after_failure(self):
        clock = [100.0]
        capacity = DemoCapacity(lambda: clock[0])
        recipe = new_recipe()
        with capacity.reserve(recipe), capacity.reserve(recipe):
            with self.assertRaisesRegex(ValidationError, 'busy'):
                with capacity.reserve(recipe):
                    self.fail('Third concurrent job started')
        with self.assertRaises(RuntimeError):
            with capacity.reserve(recipe):
                raise RuntimeError('invented engine failure')
        self.assertEqual(capacity.active, 0)
        for _ in range(27):
            with capacity.reserve(recipe):
                pass
        with self.assertRaisesRegex(ValidationError, 'busy'):
            with capacity.reserve(recipe):
                self.fail('Rate limit bypassed')
        clock[0] += 60
        with capacity.reserve(recipe):
            self.assertEqual(capacity.active, 1)


if __name__ == '__main__':
    unittest.main()
