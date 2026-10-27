"""Explicit personal or bounded public hosting; local CLI stays loopback-only."""

import base64
import binascii
import hmac
import os
import time
from collections import deque
from contextlib import contextmanager
from urllib.parse import urlsplit

from .recipe import MAX_BYTES, ValidationError

DEMO_ROWS = 1_000
DEMO_CELLS = 20_000
MAX_REQUEST_BYTES = MAX_BYTES + 65_536  # one recipe/CSV plus multipart framing


def check_demo_recipe(recipe):
    """Apply hosting limits to an already validated recipe, never alter its rules."""
    tables = recipe.get('tables', [recipe.get('table')])
    if sum(table['row_count'] for table in tables) > DEMO_ROWS:
        raise ValidationError('demo', 'Public demo: use at most 1,000 rows across all tables. Save your recipe to run larger jobs locally.')
    if sum(table['row_count'] * len(table['fields']) for table in tables) > DEMO_CELLS:
        raise ValidationError('demo', 'Public demo: use at most 20,000 cells per run. Reduce rows or columns, or run the recipe locally.')


class DemoCapacity:
    """Bound active generation and its rate in the single hosted process."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.active = 0
        self.started = deque()

    @contextmanager
    def reserve(self, recipe):
        check_demo_recipe(recipe)
        now = self.clock()
        while self.started and self.started[0] <= now - 60:
            self.started.popleft()
        if self.active >= 2 or len(self.started) >= 30:
            raise ValidationError('demo', 'The shared demo is busy. Please try Generate again in a minute; your settings are kept.')
        self.active += 1
        self.started.append(now)
        try:
            yield
        finally:
            self.active -= 1


class PersonalAccess:
    """Gate the complete ASGI app, including NiceGUI uploads and Socket.IO."""

    def __init__(self, app, *, username, password, public_demo=False):
        self.app = app
        self.username = username.encode('utf-8')
        self.password = password.encode('utf-8')
        self.public_demo = public_demo

    def authorized(self, headers):
        try:
            scheme, encoded = headers.get(b'authorization', b'').split(b' ', 1)
            if scheme.lower() != b'basic':
                return False
            username, password = base64.b64decode(encoded, validate=True).split(b':', 1)
            return (hmac.compare_digest(username, self.username)
                    & hmac.compare_digest(password, self.password))
        except (ValueError, binascii.Error):
            return False

    async def __call__(self, scope, receive, send):
        if scope['type'] not in {'http', 'websocket'}:
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        if scope['type'] == 'http' and scope['path'] == '/healthz' and scope['method'] in {'GET', 'HEAD'}:
            await send({'type': 'http.response.start', 'status': 200,
                        'headers': [(b'content-type', b'text/plain'), (b'cache-control', b'no-store')]})
            await send({'type': 'http.response.body', 'body': b'' if scope['method'] == 'HEAD' else b'ok'})
            return
        origin = headers.get(b'origin')
        try:
            same_origin = bool(origin) and urlsplit(origin.decode('ascii')).netloc.lower() == headers.get(b'host', b'').decode('ascii').lower()
        except (UnicodeError, ValueError):
            same_origin = False
        forbidden = (origin is not None and not same_origin) or (scope['type'] == 'websocket' and not same_origin)
        if forbidden or (not self.public_demo and not self.authorized(headers)):
            if scope['type'] == 'websocket':
                await send({'type': 'websocket.close', 'code': 1008})
            else:
                await send({'type': 'http.response.start', 'status': 403 if forbidden else 401,
                            'headers': [(b'www-authenticate', b'Basic realm="Ravel personal test", charset="UTF-8"'),
                                        (b'cache-control', b'no-store')]})
                await send({'type': 'http.response.body', 'body': b'Access required.'})
            return

        if self.public_demo and scope['type'] == 'http' and scope['method'] in {'POST', 'PUT', 'PATCH'}:
            chunks, size = [], 0
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return
                body = message.get('body', b'')
                size += len(body)
                if size > MAX_REQUEST_BYTES:
                    await send({'type': 'http.response.start', 'status': 413,
                                'headers': [(b'content-type', b'text/plain'), (b'cache-control', b'no-store')]})
                    await send({'type': 'http.response.body', 'body': b'Upload a single file no larger than 1 MiB.'})
                    return
                chunks.append(body)
                if not message.get('more_body', False):
                    break
            original_receive = receive
            buffered = b''.join(chunks)

            async def receive():
                nonlocal buffered
                if buffered is not None:
                    body, buffered = buffered, None
                    return {'type': 'http.request', 'body': body, 'more_body': False}
                return await original_receive()

        async def private_send(message):
            if message['type'] == 'http.response.start':
                message = {**message, 'headers': [
                    (key, value) for key, value in message.get('headers', []) if key.lower() != b'cache-control'
                ] + [(b'cache-control', b'no-store'), (b'referrer-policy', b'same-origin')]}
            await send(message)

        await self.app(scope, receive, private_send)


def settings(environ):
    mode = environ.get('RAVEL_PUBLIC_DEMO', '0')
    if mode not in {'0', '1'}:
        raise ValueError('RAVEL_PUBLIC_DEMO must be 0 (personal) or 1 (public demo).')
    username = environ.get('RAVEL_AUTH_USERNAME', '')
    password = environ.get('RAVEL_AUTH_PASSWORD', '')
    if mode != '1' and (not username or ':' in username or len(password) < 16):
        raise ValueError('Set hosting secrets RAVEL_AUTH_USERNAME (no colon) and RAVEL_AUTH_PASSWORD (at least 16 characters).')
    try:
        port = int(environ.get('PORT', '10000'))
    except ValueError:
        raise ValueError('PORT must be an integer from 1 to 65535.') from None
    if not 1 <= port <= 65535:
        raise ValueError('PORT must be an integer from 1 to 65535.')
    return username, password, port


def main():
    username, password, port = settings(os.environ)
    from .ui import app, launch
    public_demo = os.environ.get('RAVEL_PUBLIC_DEMO') == '1'
    app.add_middleware(PersonalAccess, username=username, password=password, public_demo=public_demo)
    launch(port=port, host='0.0.0.0', public_demo=public_demo)


if __name__ == '__main__':
    main()
