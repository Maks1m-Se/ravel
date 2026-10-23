"""Password-protected personal hosting entry point; local CLI stays loopback-only."""

import base64
import binascii
import hmac
import os
from urllib.parse import urlsplit


class PersonalAccess:
    """Gate the complete ASGI app, including NiceGUI uploads and Socket.IO."""

    def __init__(self, app, *, username, password):
        self.app = app
        self.username = username.encode('utf-8')
        self.password = password.encode('utf-8')

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
        if forbidden or not self.authorized(headers):
            if scope['type'] == 'websocket':
                await send({'type': 'websocket.close', 'code': 1008})
            else:
                await send({'type': 'http.response.start', 'status': 403 if forbidden else 401,
                            'headers': [(b'www-authenticate', b'Basic realm="Ravel personal test", charset="UTF-8"'),
                                        (b'cache-control', b'no-store')]})
                await send({'type': 'http.response.body', 'body': b'Access required.'})
            return

        async def private_send(message):
            if message['type'] == 'http.response.start':
                message = {**message, 'headers': [
                    (key, value) for key, value in message.get('headers', []) if key.lower() != b'cache-control'
                ] + [(b'cache-control', b'no-store'), (b'referrer-policy', b'same-origin')]}
            await send(message)

        await self.app(scope, receive, private_send)


def settings(environ):
    username = environ.get('RAVEL_AUTH_USERNAME', '')
    password = environ.get('RAVEL_AUTH_PASSWORD', '')
    if not username or ':' in username or len(password) < 16:
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
    app.add_middleware(PersonalAccess, username=username, password=password)
    launch(port=port, host='0.0.0.0')


if __name__ == '__main__':
    main()
