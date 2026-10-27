"""Check the public demo and compact controls with invented data only."""

import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_personal_web import free_port, isolation, mobile_case, response, runtime_hashes
from scripts.check_workbook_browser import activate, popup_ready, set_theme
from ravel.web import MAX_REQUEST_BYTES
from playwright.sync_api import expect, sync_playwright


async def sockets(base):
    from websockets.asyncio.client import connect
    from websockets.exceptions import InvalidStatus
    url = base.replace('http', 'ws', 1) + '/_nicegui_ws/socket.io/?EIO=4&transport=websocket'
    async with connect(url, origin=base) as connection:
        assert (await connection.recv()).startswith('0{')
    try:
        async with connect(url, origin='https://other.example'):
            raise AssertionError('Foreign-origin socket accepted')
    except InvalidStatus as error:
        assert error.response.status_code == 403


def compact_case(browser, base, out, theme, errors):
    context = browser.new_context(viewport={'width': 1366, 'height': 657})
    page = context.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(base + '/table?theme=' + theme.lower())
    expect(page.get_by_label('Rows', exact=True)).to_have_value('1000')
    expect(page.locator('.demo-note')).to_contain_text('Invented data only')
    for name in ['Add column', 'Duplicate column', 'Remove selected column']:
        button = page.get_by_role('button', name=name, exact=True)
        expect(button).to_be_visible()
        assert name not in button.inner_text()
        button.hover()
        expect(page.get_by_role('tooltip').filter(has_text=name)).to_be_visible()
    page.mouse.move(5, 5)
    geometry = []
    for label in ['Table name', 'Rows', 'Seed', 'Column name', 'Minimum', 'Maximum']:
        field = page.get_by_label(label, exact=True)
        field.scroll_into_view_if_needed()
        metric = field.evaluate('''e => {
            const r=e.getBoundingClientRect(), c=e.closest('.q-field__control').getBoundingClientRect(), s=getComputedStyle(e);
            return {label:e.getAttribute('aria-label'), height:r.height, controlHeight:c.height,
                line:parseFloat(s.lineHeight), top:parseFloat(s.paddingTop), bottom:parseFloat(s.paddingBottom),
                overflow:r.bottom-c.bottom};
        }''')
        assert metric['height'] >= metric['line'] + metric['top'] + metric['bottom'] - 1, (label, metric)
        assert metric['bottom'] >= 4 and metric['overflow'] <= 1, (label, metric)
        geometry.append({'field': label, **metric})
    help_button = page.get_by_role('button', name='Properties help', exact=True)
    assert help_button.locator('.q-icon').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)') <= 16
    activate(page, 'More options')
    popup_ready(page, '.workbench-options')
    page.screenshot(path=out / f'compact-{theme.lower()}-menu.png')
    page.keyboard.press('Escape')
    expect(page.get_by_role('button', name='More options', exact=True)).to_be_focused()
    page.get_by_label('Maximum', exact=True).fill('20')
    set_theme(page, 'Dark' if theme == 'Light' else 'Light')
    set_theme(page, theme)
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('20')
    expect(page.locator('.edit-actions')).to_have_attribute('data-pending', 'true')
    page.screenshot(path=out / f'compact-{theme.lower()}-pending.png')
    activate(page, 'Discard edits')
    activate(page, 'Duplicate column')
    expect(page.locator('.definition-table tbody tr')).to_have_count(3)
    activate(page, 'Remove selected column')
    expect(page.locator('.remove-dialog')).to_be_visible()
    page.keyboard.press('Escape')
    expect(page.locator('.definition-table tbody tr')).to_have_count(3)
    page.get_by_label('Rows', exact=True).fill('1001')
    activate(page, 'Apply changes')
    activate(page, 'Generate table')
    expect(page.locator('.status-line')).to_contain_text('Public demo: use at most 1,000 rows')
    expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_disabled()
    page.get_by_label('Rows', exact=True).fill('1000')
    activate(page, 'Apply changes')
    activate(page, 'Generate table')
    expect(page.locator('.result-state')).to_contain_text('Current', timeout=30000)
    page.screenshot(path=out / f'compact-{theme.lower()}-generated.png')
    context.close()
    return {'theme': theme, 'result': 'passed', 'input_geometry': geometry,
            'checks': 'icon names/tooltips; smaller help; input clearance; keyboard menu/focus; theme preserves draft; duplicate/remove confirmation; demo limit/recovery'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', help='Public HTTPS demo; omit to own a loopback server.')
    parser.add_argument('--executable-path', help='Explicit installed review browser; otherwise Chrome.')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--serve', type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.serve:
        from ravel.ui import app, launch
        from ravel.web import PersonalAccess
        app.add_middleware(PersonalAccess, username='', password='', public_demo=True)
        launch(port=args.serve, public_demo=True)
        return
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    process = log = None
    record = dict(started_utc=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
                  platform=platform.platform(), runtime_sha256=runtime_hashes(), cases=[], page_errors=[])
    try:
        base = args.base_url.rstrip('/') if args.base_url else f'http://127.0.0.1:{free_port()}'
        if args.base_url and not base.startswith('https://'):
            parser.error('Remote checks require HTTPS.')
        if not args.base_url:
            log = (out / 'server.log').open('w', encoding='utf-8')
            process = subprocess.Popen([sys.executable, __file__, '--serve', base.rsplit(':', 1)[1],
                                        '--output', str(out)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('Owned test server exited; inspect server.log.')
                try:
                    if response(base, '/healthz')[0] == 200:
                        break
                except (OSError, URLError):
                    time.sleep(.2)
            else:
                raise RuntimeError('Owned test server did not start.')
        record['base_url'] = base
        assert response(base, '/healthz') == (200, b'ok')
        assert response(base, '/')[0] == 200
        assert response(base, '/', origin='https://other.example')[0] == 403
        try:
            urlopen(Request(base + '/_nicegui/client/upload/element', data=b'x' * (MAX_REQUEST_BYTES + 1)), timeout=30)
            raise AssertionError('Oversized request accepted')
        except HTTPError as error:
            assert error.code == 413
        asyncio.run(sockets(base))
        record['http_websocket_checks'] = 'passed'
        with sync_playwright() as p:
            browser = p.chromium.launch(**({'executable_path': args.executable_path} if args.executable_path else {'channel': 'chrome'}), headless=True)
            record['browser'] = browser.version
            for theme in ['Light', 'Dark']:
                record['cases'].append(compact_case(browser, base, out, theme, record['page_errors']))
                record['cases'].append(mobile_case(browser, base, None, out, theme, record['page_errors'], public_demo=True))
                print('PASS public demo + compact controls ' + theme, flush=True)
            isolation(browser, base, None)
            record['separate_sessions'] = 'passed'
            browser.close()
        assert not record['page_errors'], record['page_errors']
        assert runtime_hashes() == record['runtime_sha256'], 'Runtime changed during review.'
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
        (out / 'results.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
