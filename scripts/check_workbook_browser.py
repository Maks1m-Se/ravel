"""Keyboard/state assertions for the running fixture workbook; see development.md."""

import argparse
from datetime import datetime, timezone
import json
from importlib.metadata import version
from pathlib import Path
import platform
import re
import sys
import traceback
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.workbook.config import new_config  # noqa: E402


def keyboard_to(page, target):
    """Navigate only; never use this helper to assert post-action focus."""
    for _ in range(65):
        if target.evaluate('(e) => e === document.activeElement || e.contains(document.activeElement)'):
            return
        page.keyboard.press('Tab')
    raise AssertionError(f'Cannot reach {target} with Tab')


def type_value(page, label, value):
    target = page.get_by_label(label, exact=True)
    keyboard_to(page, target)
    page.keyboard.press('Control+a')
    page.keyboard.type(value)


def activate(page, name):
    keyboard_to(page, page.get_by_role('button', name=name, exact=True))
    page.keyboard.press('Enter')


def assert_error(page, label, message, *, focused=True):
    target = page.get_by_label(label, exact=True)
    expect(target).to_have_attribute('aria-invalid', 'true')
    if focused:
        expect(target).to_be_focused()  # no Tab helper after the failed action
    described_by = target.get_attribute('aria-describedby')
    assert described_by, f'{label} has no associated error message'
    error = page.locator(f'#{described_by.split()[0]}')
    expect(error).to_contain_text(message)
    expect(error).to_be_in_viewport(ratio=1)
    expect(target).to_be_in_viewport(ratio=1)
    # Viewport presence alone does not catch an error painted over another input.
    assert error.evaluate('''e => {
        const r = e.getBoundingClientRect();
        const field = e.closest('.q-field');
        const f = field.getBoundingClientRect();
        return r.top >= f.top && r.bottom <= f.bottom + 1 &&
            [...document.querySelectorAll('.q-field__control')].every(other => {
                const o = other.getBoundingClientRect();
                return r.right <= o.left || r.left >= o.right || r.bottom <= o.top || r.top >= o.bottom;
            });
    }'''), f'{label}: error overlaps a control or escapes its field'
    return {'label': label, 'message': error.inner_text(),
            'bounds': error.bounding_box(), 'focused': focused}


def assert_focus_style(page, target):
    expect(target).to_be_focused()
    result = target.evaluate('''e => {
        const ring = e.closest('.q-field') || e;
        const style = getComputedStyle(ring);
        return {tag: e.tagName, label: e.getAttribute('aria-label') || e.innerText,
            focusVisible: e.matches(':focus-visible'), outline: style.outline,
            outlineWidth: parseFloat(style.outlineWidth), outlineStyle: style.outlineStyle,
            boxShadow: style.boxShadow, color: style.color, background: style.backgroundColor};
    }''')
    assert result['focusVisible'], result
    assert ((result['outlineWidth'] >= 2 and result['outlineStyle'] not in ('none', 'hidden'))
            or result['boxShadow'] != 'none'), result
    expect(target).to_be_in_viewport(ratio=1)
    return result


def save_json(page, path):
    with page.expect_download() as pending:
        activate(page, 'Save configuration')
    pending.value.save_as(path)
    return json.loads(path.read_text())


def reload_json(page, path):
    activate(page, 'Reload configuration')
    expect(page.locator('.load-dialog')).to_be_visible()
    page.locator('input[type=file]').set_input_files(path)


def exercise(page, out, width, height, entry, results):
    prefix = f'{width}x{height}-{entry}'
    observations = {'viewport': [width, height], 'entry': entry, 'errors': [], 'focus': []}
    results['cases'].append(observations)
    page.goto(results['base_url'] + '/')
    activate(page, 'Create from scratch' if entry == 'scratch' else 'Start from a sample')
    name = 'value' if entry == 'scratch' else 'length_mm'
    expect(page.get_by_label('Field name', exact=True)).to_have_value(name)
    activate(page, 'New table' if entry == 'scratch' else 'Sample table')
    activate(page, name)
    # These assertions must precede any keyboard_to/type_value call.
    expect(page.get_by_label('Field name', exact=True)).to_be_focused()
    observations['field_activation_focus'] = 'Field name'
    observations['focus'].append(assert_focus_style(page, page.get_by_label('Field name', exact=True)))
    page.screenshot(path=out / f'{prefix}-focus-input.png')

    # Link, ordinary button, field button, selector and input keyboard indicators.
    for target, suffix in [
        (page.get_by_role('link', name='Workbook home'), 'link'),
        (page.get_by_role('button', name='Save configuration', exact=True), 'button'),
        (page.get_by_role('button', name=name, exact=True), 'field-button'),
        (page.get_by_label('Field type', exact=True), 'selector'),
    ]:
        keyboard_to(page, target)
        observations['focus'].append(assert_focus_style(page, target))
        page.screenshot(path=out / f'{prefix}-focus-{suffix}.png')

    type_value(page, 'Minimum', '200')
    activate(page, 'Apply field')
    observations['errors'].append(assert_error(page, 'Minimum', 'Minimum must not exceed maximum'))
    expect(page.get_by_label('Maximum', exact=True)).to_have_attribute('aria-invalid', 'true')
    assert_error(page, 'Maximum', 'Minimum must not exceed maximum', focused=False)
    expect(page.get_by_label('Minimum', exact=True)).to_have_value('200')
    page.screenshot(path=out / f'{prefix}-range-error.png')
    type_value(page, 'Minimum', '5')
    activate(page, 'Apply field')
    expect(page.locator('.status-line')).to_contain_text('Field applied')
    expect(page.locator('.properties [aria-invalid=true]')).to_have_count(0)
    expect(page.locator('.provenance')).to_contain_text('Minimum: user override')

    type_value(page, 'Missing percent', '150')
    activate(page, 'material' if entry == 'sample' else 'Apply field')
    observations['errors'].append(assert_error(page, 'Missing percent', 'between 0 and 100'))
    expect(page.get_by_label('Missing percent', exact=True)).to_have_value('150')
    if entry == 'sample':
        expect(page.locator('.properties .section-title')).to_have_text('length_mm')
        expect(page.locator('.properties .help[role=alert]')).to_contain_text('Field switch refused')
    page.screenshot(path=out / f'{prefix}-missing-error.png')
    type_value(page, 'Missing percent', '15')
    activate(page, 'material' if entry == 'sample' else 'Apply field')
    if entry == 'sample':
        expect(page.get_by_label('Field name', exact=True)).to_be_focused()
        expect(page.get_by_label('Field name', exact=True)).to_have_value('material')
        activate(page, 'length_mm')
        expect(page.get_by_label('Field name', exact=True)).to_be_focused()
        expect(page.get_by_label('Missing percent', exact=True)).to_have_value(re.compile(r'15(?:\.0)?'))
    expect(page.locator('.properties [aria-invalid=true]')).to_have_count(0)

    # The preview and its headers stay fixed even when the field draft changes.
    activate(page, 'Illustrative preview')
    expect(page.locator('.preview-table tbody tr')).to_have_count(10 if entry == 'sample' else 3)
    expect(page.locator('.preview-warning')).to_contain_text('NOT GENERATED OUTPUT')
    preview_region = page.get_by_role('region', name='Fixed illustration table; use arrow keys to scroll')
    keyboard_to(page, preview_region)
    observations['focus'].append(assert_focus_style(page, preview_region))
    page.keyboard.press('ArrowDown')
    page.screenshot(path=out / f'{prefix}-preview.png')
    preview = page.locator('.preview-table').inner_text()
    type_value(page, 'Maximum', '20')
    activate(page, 'Field definitions')
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('20')
    activate(page, 'Illustrative preview')
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('20')
    assert page.locator('.preview-table').inner_text() == preview
    activate(page, 'Field definitions')
    if entry == 'sample':
        expect(page.locator('.count-note')).to_contain_text('1,000 generated rows + 0 retained')
        keyboard_to(page, page.get_by_label('Output mode', exact=True))
        page.keyboard.press('Enter')
        page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')
        expect(page.locator('.count-note')).to_contain_text('10 retained source rows + 990 generated rows')

    # Failed Save must neither apply the valid field draft nor download anything.
    applied_before = page.locator('.provenance').inner_text()
    definitions_before = page.locator('.definition-table').inner_text()
    downloads = []
    record_download = lambda download: downloads.append(download)
    page.on('download', record_download)
    type_value(page, 'Requested rows (new or total)', '9' if entry == 'sample' else '0')
    activate(page, 'Save configuration')
    observations['errors'].append(assert_error(page, 'Requested rows (new or total)',
                                              'at least 10' if entry == 'sample' else 'whole number'))
    expect(page.locator('.status-line')).to_contain_text('at least 10' if entry == 'sample' else 'whole number')
    assert page.locator('.provenance').inner_text() == applied_before
    assert page.locator('.definition-table').inner_text() == definitions_before
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('20')
    expect(page.get_by_label('Requested rows (new or total)', exact=True)).to_have_value('9' if entry == 'sample' else '0')
    assert downloads == [], 'Failed Save produced a download'
    page.screenshot(path=out / f'{prefix}-save-error.png')
    page.remove_listener('download', record_download)
    type_value(page, 'Requested rows (new or total)', '1000')
    saved_path = out / f'{prefix}-saved.json'
    saved = save_json(page, saved_path)
    field = saved['table']['fields'][-1]
    assert field['settings']['maximum'] == 20 and field['settings']['missing_percent'] == 15
    assert field['origins']['maximum'] == 'user override'
    assert saved['output'] == {'mode': 'extend' if entry == 'sample' else 'new', 'count': 1000}
    expect(page.locator('[aria-invalid=true]')).to_have_count(0)
    expect(page.locator('.count-note')).to_contain_text('990 generated rows' if entry == 'sample' else '1,000 generated rows')
    observations['atomic_save_retry'] = 'passed'

    # Import errors must preserve both drafts and the applied provenance.
    type_value(page, 'Maximum', '30')
    type_value(page, 'Field name', 'unfinished_name')
    applied_before = page.locator('.provenance').inner_text()
    oversized = new_config(entry)
    oversized['table']['fields'][-1]['settings']['maximum'] = 10**400
    oversized['table']['fields'][-1]['origins']['maximum'] = 'user override'
    oversized_path = out / f'{prefix}-oversized.json'
    oversized_path.write_text(json.dumps(oversized))
    reload_json(page, oversized_path)
    expect(page.locator('.load-dialog [role=alert]')).to_contain_text('Maximum must be a finite number supported')
    expect(page.locator('.load-dialog [role=alert]')).to_be_in_viewport(ratio=1)
    page.screenshot(path=out / f'{prefix}-import-error.png')
    activate(page, 'Cancel')
    expect(page.locator('.load-dialog')).to_be_hidden()
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('30')
    expect(page.get_by_label('Field name', exact=True)).to_have_value('unfinished_name')
    assert page.locator('.provenance').inner_text() == applied_before
    observations['oversized_import_preservation'] = 'passed'

    reload_json(page, saved_path)
    expect(page.locator('.status-line')).to_contain_text('Configuration reloaded')
    expect(page.locator('.load-dialog')).to_be_hidden()
    expect(page.get_by_label('Maximum', exact=True)).to_have_value(re.compile(r'20(?:\.0)?'))
    expect(page.get_by_label('Field name', exact=True)).to_have_value(name)
    again = save_json(page, out / f'{prefix}-reloaded.json')
    assert again == saved
    assert (out / f'{prefix}-reloaded.json').read_bytes() == saved_path.read_bytes()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=out / f'{prefix}-recovered.png')
    observations['round_trip'] = 'passed'
    observations['result'] = 'passed'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8080')
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/workbook-repair/browser')
    parser.add_argument('--channel', default='chrome')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    results = dict(started_utc=datetime.now(timezone.utc).isoformat(), base_url=args.base_url,
                   python=platform.python_version(), platform=platform.platform(),
                   playwright=version('playwright'),
                   cases=[], external_requests=[], external_websockets=[], page_errors=[])
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel=args.channel, headless=True)
            results['browser'] = browser.version
            for width, height in [(1366, 657), (1280, 800)]:
                for entry in ['scratch', 'sample']:
                    context = browser.new_context(viewport={'width': width, 'height': height}, accept_downloads=True)

                    def route(request):
                        if urlparse(request.request.url).hostname not in {'127.0.0.1', 'localhost'}:
                            results['external_requests'].append(request.request.url)
                            request.abort()
                        else:
                            request.continue_()

                    def websocket(ws):
                        if urlparse(ws.url).hostname not in {'127.0.0.1', 'localhost'}:
                            results['external_websockets'].append(ws.url)
                            ws.close()
                        else:
                            ws.connect_to_server()

                    context.route('**/*', route)
                    context.route_web_socket('**/*', websocket)
                    page = context.new_page()
                    page.on('pageerror', lambda e: results['page_errors'].append(str(e)))
                    try:
                        exercise(page, out, width, height, entry, results)
                    except Exception:
                        page.screenshot(path=out / 'failure.png')
                        raise
                    finally:
                        context.close()
                    print(f'PASS {width}x{height} {entry}', flush=True)
            browser.close()
        assert not results['external_requests'], results['external_requests']
        assert not results['external_websockets'], results['external_websockets']
        assert not results['page_errors'], results['page_errors']
        results['result'] = 'passed'
    except Exception:
        results['result'] = 'failed'
        results['failure'] = traceback.format_exc()
        raise
    finally:
        results['finished_utc'] = datetime.now(timezone.utc).isoformat()
        (out / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
