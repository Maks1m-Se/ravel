"""Check protected local hosting, mobile workflows and independent browser contexts.

Local credentials are random, ephemeral test fixtures, never written to evidence.
For a real deployment use --base-url and hosting secrets in the process environment.
"""

import argparse
import asyncio
import base64
import csv
from datetime import datetime, timezone
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import traceback
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def runtime_hashes():
    return {p.relative_to(ROOT).as_posix(): sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / 'ravel').rglob('*')
            if p.suffix in {'.py', '.css', '.js'} and '__pycache__' not in p.parts}


def free_port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def response(base, path, auth=None, method='GET', origin=None):
    headers = {} if auth is None else {'Authorization': auth}
    if origin:
        headers['Origin'] = origin
    try:
        with urlopen(Request(base + path, method=method, headers=headers), timeout=10) as result:
            return result.status, result.read()
    except HTTPError as result:
        return result.code, result.read()


async def websocket_checks(base, authorization):
    from websockets.asyncio.client import connect
    from websockets.exceptions import InvalidStatus
    url = base.replace('http', 'ws', 1) + '/_nicegui_ws/socket.io/?EIO=4&transport=websocket'
    for headers, origin in [({}, base), ({'Authorization': authorization}, 'https://other.example')]:
        try:
            async with connect(url, origin=origin, additional_headers=headers, proxy=None):
                raise AssertionError('Unauthorized WebSocket accepted')
        except InvalidStatus as error:
            assert error.response.status_code == 403
    async with connect(url, origin=base, additional_headers={'Authorization': authorization}, proxy=None) as ws:
        greeting = await ws.recv()
        assert greeting.startswith('0{') and 'sid' in json.loads(greeting[1:])


def mobile_case(browser, base, credentials, out, theme, errors, *, public_demo=False):
    from playwright.sync_api import expect
    context = browser.new_context(viewport={'width': 412, 'height': 915}, is_mobile=True,
                                  has_touch=True, device_scale_factor=2.625,
                                  http_credentials=credentials, accept_downloads=True)
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(base + '/table?theme=' + theme.lower())
    expect(page.get_by_label('Rows', exact=True)).to_have_value('1000')

    def button(name):
        return page.get_by_role('button', name=name, exact=True)

    def generate():
        button('Generate table').click()
        expect(page.locator('.result-state')).to_contain_text('Current', timeout=30000)
        expect(page.locator('.preview-view .preview-table tbody tr')).to_have_count(100)

    def download(name, filename):
        with page.expect_download() as pending:
            button(name).click()
        target = out / f'{theme.lower()}-{filename}'
        pending.value.save_as(target)
        return target.read_bytes(), pending.value.url

    def no_page_overflow():
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')

    generate()
    data, download_url = download('Export CSV', '1000.csv')
    assert len(list(csv.reader(StringIO(data.decode())))) == 1001
    recipe, _ = download('Save recipe', 'recipe.json')
    assert json.loads(recipe)['table']['row_count'] == 1000
    # NiceGUI byte downloads are blobs delivered over the protected Socket.IO
    # channel; file/URL downloads use authenticated HTTP instead.
    if download_url.startswith('blob:'):
        assert download_url.startswith('blob:' + base)
    else:
        assert response('', download_url)[0] == 401
    button('Fields').click()
    page.get_by_label('Maximum', exact=True).fill('20')
    expect(page.locator('.edit-actions')).to_have_attribute('data-pending', 'true')
    button('Apply changes').click()
    expect(page.locator('.edit-actions')).to_have_attribute('data-pending', 'false')
    expect(button('Export CSV')).to_be_disabled()
    page.get_by_label('Maximum', exact=True).fill('30')
    button('Discard edits').click()
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('20')
    generate()
    changed, _ = download('Export CSV', 'applied.csv')
    changed_rows = list(csv.reader(StringIO(changed.decode())))
    assert changed_rows[0] == ['id', 'value']
    assert all(0 <= int(row[1]) <= 20 for row in changed_rows[1:])
    button('Fields').click()

    # Pixel 8 CSS dimensions; reduced height approximates the visual keyboard area.
    for label, width, height in [('portrait', 412, 915), ('landscape', 915, 412),
                                  ('keyboard-height', 412, 420)]:
        page.set_viewport_size({'width': width, 'height': height})
        no_page_overflow()
        field = page.get_by_label('Maximum', exact=True)
        field.fill('31')
        button('Apply changes').scroll_into_view_if_needed()
        expect(button('Apply changes')).to_be_in_viewport(ratio=1)
        expect(button('Discard edits')).to_be_in_viewport(ratio=1)
        button('Discard edits').click()
        expect(field).to_have_value('20')
        field.scroll_into_view_if_needed()
        expect(field).to_be_in_viewport(ratio=1)
        assert field.evaluate('(e)=>document.elementFromPoint(e.getBoundingClientRect().x+5,e.getBoundingClientRect().y+5)===e')
        page.screenshot(path=out / f'{theme.lower()}-{label}-properties.png')
        # Wide definitions must scroll inside their own region.
        region = page.locator('.fields-view')
        assert region.evaluate('(e)=>e.scrollWidth > e.clientWidth') == (width < 540)
        region.evaluate('(e)=>e.scrollLeft=e.scrollWidth')
        if width < 540:
            assert region.evaluate('(e)=>e.scrollLeft>0')
        no_page_overflow()

    page.set_viewport_size({'width': 412, 'height': 915})
    button('Import CSV').click()
    dialog = page.locator('.sample-dialog')
    # Only invented fixture bytes enter the app.
    with page.expect_request(lambda request: '/upload/' in request.url and request.method == 'POST') as upload:
        dialog.locator('input[type=file]').set_input_files(ROOT / 'examples/sample-assisted/ten-rows.csv')
    expect(dialog.locator('.source-count')).to_contain_text('10 rows')
    if public_demo:
        assert upload.value.response().ok
    else:
        assert response('', upload.value.url, method='POST')[0] == 401
    confirm = page.get_by_role('checkbox', name='Use the displayed sequential identifier rules', exact=True)
    confirm.click()
    expect(confirm).to_be_checked()
    for height in [915, 420]:
        page.set_viewport_size({'width': 412, 'height': height})
        expect(button('Use sample')).to_be_in_viewport(ratio=1)
        expect(button('Cancel import')).to_be_in_viewport(ratio=1)
        page.screenshot(path=out / f'{theme.lower()}-import-{height}.png')
    button('Use sample').click()
    expect(dialog).not_to_be_visible()
    generate()
    imported, _ = download('Export CSV', 'imported.csv')
    rows = list(csv.reader(StringIO(imported.decode())))
    assert len(rows) == 1001 and rows[1][0] == '11' and rows[-1][0] == '1010'
    assert all(row[-1] == 'generated' for row in rows[1:])
    assert rows[0] == ['sample_id', 'length_mm', 'material', 'row_origin']
    context.close()
    return {'theme': theme, 'result': 'passed', 'viewports': ['412x915', '915x412', '412x420'],
            'checks': '1000 rows; pending/apply/stale/discard; CSV/recipe; invented CSV import; table scroll; reachable Properties/actions; reduced keyboard height'}


def isolation(browser, base, credentials):
    from playwright.sync_api import expect
    contexts = [browser.new_context(http_credentials=credentials) for _ in range(2)]
    try:
        first, second = [context.new_page() for context in contexts]
        for page in [first, second]:
            page.goto(base + '/table')
            expect(page.get_by_label('Column name', exact=True)).to_have_value('value')
        first.get_by_label('Column name', exact=True).fill('session_alpha')
        first.get_by_role('button', name='Apply changes', exact=True).click()
        first.get_by_role('button', name='Generate table', exact=True).click()
        expect(first.locator('.result-state')).to_contain_text('Current', timeout=30000)
        expect(second.get_by_label('Column name', exact=True)).to_have_value('value')
        expect(second.locator('.result-state')).not_to_contain_text('Current')
        second.get_by_label('Rows', exact=True).fill('7')
        second.get_by_role('button', name='Apply changes', exact=True).click()
        second.get_by_role('button', name='Generate table', exact=True).click()
        expect(second.locator('.preview-table tbody tr')).to_have_count(7)
        expect(first.get_by_label('Rows', exact=True)).to_have_value('1000')
        expect(first.locator('.preview-table tbody tr')).to_have_count(100)
        expect(first.get_by_label('Column name', exact=True)).to_have_value('session_alpha')
    finally:
        for context in contexts:
            context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', help='Existing protected HTTPS deployment; omit for an owned local server.')
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/render-personal/browser')
    parser.add_argument('--desktop', action='store_true', help='Run the maintained full desktop matrix on an owned loopback server.')
    parser.add_argument('--desktop-workflow', default='all', help='Focused desktop diagnosis, otherwise all workflows.')
    parser.add_argument('--executable-path', help='Explicit installed Chromium review binary.')
    parser.add_argument('--serve-desktop', type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.serve_desktop:
        from ravel.ui import app, launch
        identity = {'source_sha256': runtime_hashes(), 'snapshot': 'personal-render-desktop'}
        app.get('/__ravel_test/identity')(lambda: identity)
        launch(port=args.serve_desktop)
        return
    if args.desktop and args.base_url:
        parser.error('--desktop uses an owned local server, not --base-url.')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    process = log = None
    record = {'started_utc': datetime.now(timezone.utc).isoformat(), 'runtime_sha256': runtime_hashes(),
              'page_errors': [], 'cases': [], 'scope': 'remote HTTPS' if args.base_url else 'local protected hosting entry point'}
    try:
        if args.base_url:
            base = args.base_url.rstrip('/')
            if not base.startswith('https://'):
                raise ValueError('Remote checks require HTTPS.')
            credentials = {'username': os.environ['RAVEL_AUTH_USERNAME'], 'password': os.environ['RAVEL_AUTH_PASSWORD']}
        else:
            base = f'http://127.0.0.1:{free_port()}'
            credentials = {'username': 'invented-test', 'password': secrets.token_urlsafe(32)}
            env = {**os.environ, 'PORT': base.rsplit(':', 1)[1], 'RAVEL_AUTH_USERNAME': credentials['username'],
                   'RAVEL_AUTH_PASSWORD': credentials['password'], 'PYTHONUTF8': '1'}
            log = (out / 'server.log').open('w', encoding='utf-8')
            command = ([sys.executable, str(Path(__file__)), '--serve-desktop', env['PORT']]
                       if args.desktop else [sys.executable, '-m', 'ravel.web'])
            process = subprocess.Popen(command, cwd=ROOT, env=env,
                                       stdout=log, stderr=subprocess.STDOUT)
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('Local server exited; inspect server.log.')
                try:
                    if response(base, '/__ravel_test/identity' if args.desktop else '/healthz')[0] == 200:
                        break
                except (OSError, URLError):
                    time.sleep(.2)
            else:
                raise RuntimeError('Local server did not start.')
        if args.desktop:
            subprocess.run([sys.executable, str(ROOT / 'scripts/check_generator_browser.py'),
                            '--base-url', base, '--workflow', args.desktop_workflow,
                            '--verify-source', '--output', str(out / 'desktop')]
                           + (['--executable-path', args.executable_path] if args.executable_path else []), cwd=ROOT, check=True)
            record['result'] = 'passed'
            record['scope'] = 'owned local desktop server; see desktop/results.json'
            return
        auth = 'Basic ' + base64.b64encode(f'{credentials["username"]}:{credentials["password"]}'.encode()).decode()
        for method, path in [('GET', '/'), ('GET', '/table'), ('GET', '/favicon.ico'),
                             ('POST', '/_nicegui/client/upload/element'),
                             ('GET', '/_nicegui_ws/socket.io/?EIO=4&transport=polling')]:
            assert response(base, path, method=method)[0] == 401, (method, path)
        assert response(base, '/', 'Basic aW52YWxpZDppbnZhbGlk')[0] == 401
        assert response(base, '/', auth, origin='https://other.example')[0] == 403
        assert response(base, '/', auth)[0] == 200
        asyncio.run(websocket_checks(base, auth))
        record['http_websocket_access'] = 'passed'
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(**({'executable_path': args.executable_path} if args.executable_path else {'channel': 'chrome'}), headless=True)
            record['browser'] = browser.version
            for theme in ['Light', 'Dark']:
                record['cases'].append(mobile_case(browser, base, credentials, out, theme, record['page_errors']))
                print(f'PASS protected mobile {theme}', flush=True)
            isolation(browser, base, credentials)
            record['two_browser_contexts'] = 'passed'
            browser.close()
        assert not record['page_errors'], record['page_errors']
        assert runtime_hashes() == record['runtime_sha256']
        record['result'] = 'passed'
    except Exception:
        record['result'] = 'failed'
        record['failure'] = traceback.format_exc()
        raise
    finally:
        if process:
            process.terminate()
            process.wait(timeout=15)
        if log:
            log.close()
        record['finished_utc'] = datetime.now(timezone.utc).isoformat()
        (out / 'results.json').write_text(json.dumps(record, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
