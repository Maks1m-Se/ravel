"""Maintained Windows/Chrome checks for the explicit-rule table builder."""

import argparse
import csv
from datetime import datetime, timezone
from importlib.metadata import version
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import platform
import sys
import traceback
from urllib.parse import urlparse
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ravel.engine import csv_text, generate, preview_rows  # noqa: E402
from ravel.recipe import MAX_BYTES, loads, new_recipe  # noqa: E402
from scripts.check_workbook_browser import (  # noqa: E402
    activate, assert_branding, assert_error, assert_focus_style, check_help, contrast,
    keyboard_to, popup_ready, properties_width, set_theme, type_value,
)


def cli_command(*arguments):
    executable=os.environ.get('RAVEL_BROWSER_EXECUTABLE')
    return ([executable] if executable else [sys.executable,'-m','ravel'])+list(arguments)


def download(page, label, path):
    keyboard_to(page, page.get_by_role('button', name=label, exact=True))
    with page.expect_download() as pending:
        page.keyboard.press('Enter')
    pending.value.save_as(path)
    return path.read_bytes()


def reload_recipe(page, path):
    activate(page, 'Open recipe')
    expect(page.locator('.load-dialog')).to_be_visible()
    page.locator('.load-dialog input[type=file]').set_input_files(path)


def choose_rule(page, label):
    keyboard_to(page, page.get_by_label('Rule', exact=True))
    page.keyboard.press('Enter')
    popup_ready(page, '.q-menu')
    page.get_by_role('option', name=label, exact=True).click()
    expect(page.locator('.q-menu')).to_have_count(0)
    expect(page.get_by_label('Rule', exact=True)).to_have_value(label)
    expect(page.get_by_label('Rule', exact=True)).to_be_focused()


def apply(page):
    activate(page, 'Apply changes')
    expect(page.locator('.status-line')).to_contain_text('Changes applied')
    expect(page.locator('.draft-summary')).to_have_text('All changes applied')
    expect(page.locator('.properties [aria-invalid=true], .output-panel [aria-invalid=true]')).to_have_count(0)


def generate_table(page):
    activate(page, 'Generate table')
    expect(page.locator('.result-state')).to_contain_text('Current', timeout=30000)
    expect(page.get_by_role('button', name='Preview', exact=True)).to_have_attribute('aria-pressed', 'true')
    expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_enabled()


def preview_cells(page):
    return page.locator('.preview-view .preview-table tbody tr').evaluate_all('(rows) => rows.map(r => [...r.children].map(c => c.textContent))')


def state_snapshot(page):
    return page.evaluate('''() => ({
        inputs: [...document.querySelectorAll('.properties input, .properties textarea, .output-panel input')]
            .map(e => [e.id, e.value, e.getAttribute('aria-invalid'), e.getAttribute('aria-describedby')]),
        errors: [...document.querySelectorAll('.properties [role=alert], .output-panel [role=alert]')].map(e => e.textContent),
        applied: document.querySelector('.definition-table').textContent,
        selected: document.querySelector('.selected-row').dataset.fieldId,
        result: document.querySelector('.result-state').textContent,
        drafts: document.querySelector('.draft-summary').textContent
    })''')


def layout_regressions(page, viewport, theme):
    before = state_snapshot(page)
    divider = page.get_by_role('separator', name='Properties', exact=True)
    keyboard_to(page, divider)
    focus = assert_focus_style(page, divider)
    page.keyboard.press('End')
    properties_width(page, 560)
    page.set_viewport_size({'width': 900, 'height': 657})
    properties_width(page, 446, 446)
    page.set_viewport_size(viewport)
    properties_width(page, 560)
    for cancel in ['Escape', 'pointercancel']:
        page.set_viewport_size({'width': 900, 'height': 657})
        properties_width(page, 446, 446)
        box = divider.bounding_box()
        x, y = box['x'] + 5, box['y'] + box['height']/2
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x+70, y, steps=5)
        properties_width(page, 376, 446)
        if cancel == 'Escape':
            page.keyboard.press('Escape')
        else:
            divider.dispatch_event('pointercancel')
        page.mouse.up()
        page.set_viewport_size(viewport)
        properties_width(page, 560)
    set_theme(page, 'Dark' if theme == 'Light' else 'Light')
    set_theme(page, theme)
    for name in ['Preview', 'Fields']:
        activate(page, name)
        properties_width(page, 560)
    assert state_snapshot(page) == before
    page.set_viewport_size({'width': 760, 'height': 657})
    properties_width(page, 306, 306)
    activate(page, 'Reset layout')
    properties_width(page, 306, 306)
    page.set_viewport_size(viewport)
    properties_width(page, 312)
    assert state_snapshot(page) == before
    return focus


def exercise(page, base, out, viewport, theme):
    prefix = f'{viewport["width"]}x{viewport["height"]}-{theme.lower()}'
    page.set_viewport_size({'width': 760, 'height': 657})
    page.goto(base + '/table?theme=' + theme.lower())
    properties_width(page, 306, 306)
    expect(page.get_by_role('separator', name='Properties', exact=True)).not_to_be_focused()
    page.set_viewport_size(viewport)
    properties_width(page, 312)
    home_link = page.get_by_role('link', name='Home', exact=True)
    keyboard_to(page, home_link)
    page.keyboard.press('Enter')
    expect(page).to_have_url(base + '/?theme=' + theme.lower())
    assert_branding(page, theme)
    page.screenshot(path=out / f'{prefix}-start.png')
    activate(page, 'Create table')
    expect(page.get_by_label('Column name', exact=True)).to_have_value('value')
    check_help(page, 'Properties')
    check_help(page, 'Preview')
    expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_disabled()
    generate_table(page)
    expect(page.locator('.preview-table tbody tr')).to_have_count(100)
    original_csv = download(page, 'Export CSV', out / f'{prefix}-original.csv')
    original_recipe = download(page, 'Save recipe', out / f'{prefix}-original.recipe.json')
    expected = generate(loads(original_recipe))
    assert original_csv == csv_text(expected).encode()
    assert preview_cells(page) == preview_rows(expected)
    activate(page, 'Fields')

    type_value(page, 'Maximum', '20')
    type_value(page, 'Minimum', '200')
    activate(page, 'Apply changes')
    assert_error(page, 'Minimum', 'Minimum must not exceed maximum')
    before = state_snapshot(page)
    blocked_downloads = []
    recorder = lambda d: blocked_downloads.append(d)
    page.on('download', recorder)
    activate(page, 'Save recipe')
    expect(page.locator('.status-line')).to_contain_text('Apply or discard')
    activate(page, 'Generate table')
    expect(page.locator('.status-line')).to_contain_text('Apply or discard')
    expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_disabled()
    activate(page, 'Select column id')
    expect(page.get_by_label('Column name', exact=True)).to_have_value('value')
    assert state_snapshot(page) == before
    focus = layout_regressions(page, viewport, theme)
    assert not blocked_downloads
    page.remove_listener('download', recorder)
    page.screenshot(path=out / f'{prefix}-error.png')
    type_value(page, 'Minimum', '5')
    apply(page)
    expect(page.locator('.result-state')).to_contain_text('Out of date')
    type_value(page, 'Rows', '0')
    activate(page, 'Apply changes')
    assert_error(page, 'Rows', 'from 1 to 100,000')
    type_value(page, 'Rows', '1000')
    type_value(page, 'Seed', '42')
    type_value(page, 'Table name', 'Demo table')
    apply(page)
    expect(page.locator('.table-name-label')).to_have_text('Demo table')
    generate_table(page)
    base_csv = download(page, 'Export CSV', out / f'{prefix}-base.csv')
    base_values = [r[1] for r in list(csv.reader(StringIO(base_csv.decode())))[1:]]

    activate(page, 'Fields')
    activate(page, 'Add column')
    expect(page.get_by_label('Column name', exact=True)).to_be_focused()
    choose_rule(page, 'Constant text')
    type_value(page, 'Column name', 'group')
    type_value(page, 'Constant value', 'demo')
    apply(page)
    activate(page, 'Add column')
    expect(page.get_by_label('Column name', exact=True)).to_be_focused()
    choose_rule(page, 'Random decimal')
    type_value(page, 'Column name', 'measure')
    type_value(page, 'Minimum', '-1.20')
    type_value(page, 'Maximum', '2.30')
    apply(page)
    activate(page, 'Add column')
    expect(page.get_by_label('Column name', exact=True)).to_be_focused()
    choose_rule(page, 'Category')
    type_value(page, 'Column name', 'arm')
    type_value(page, 'Categories and probabilities', 'A,0.2\nB,0.3')
    activate(page, 'Apply changes')
    assert_error(page, 'Categories and probabilities', 'sum exactly to 1')
    type_value(page, 'Categories and probabilities', 'A,0.25\nB,0.75')
    type_value(page, 'Missing probability', '0.1')
    apply(page)
    activate(page, 'Select column value')
    expect(page.get_by_label('Column name', exact=True)).to_be_focused()
    type_value(page, 'Column name', 'score')
    apply(page)
    activate(page, 'Duplicate column')
    expect(page.get_by_label('Column name', exact=True)).to_be_focused()
    expect(page.get_by_label('Column name', exact=True)).to_have_value('score_copy')
    saved = download(page, 'Save recipe', out / f'{prefix}-built.recipe.json')
    recipe = loads(saved)
    assert len(recipe['table']['fields']) == 6
    assert len({f['id'] for f in recipe['table']['fields']}) == 6
    assert recipe['table']['fields'][1]['id'] == 'value'
    assert recipe['table']['fields'][-1]['id'] != 'value'
    generate_table(page)
    built = download(page, 'Export CSV', out / f'{prefix}-built.csv')
    expected = generate(recipe)
    assert built == csv_text(expected).encode()
    assert preview_cells(page) == preview_rows(expected)
    parsed = list(csv.reader(StringIO(built.decode())))
    assert [r[1] for r in parsed[1:]] == base_values
    assert [r[1] for r in parsed[1:]] != [r[-1] for r in parsed[1:]]
    record = json.loads(download(page, 'Save run record', out / f'{prefix}-run.json'))
    assert record['recipe'] == recipe and record['row_count'] == 1000
    activate(page, 'Fields')
    divider = page.get_by_role('separator', name='Properties', exact=True)
    keyboard_to(page, divider)
    page.keyboard.press('End')
    properties_width(page, 560)
    assert download(page, 'Save recipe', out / f'{prefix}-layout.recipe.json') == saved
    page.screenshot(path=out / f'{prefix}-fields.png')
    readings = contrast(page, '.properties input, .q-field__label, .setting-origin, .result-state, .action-toolbar button:not(:disabled)')
    activate(page, 'Preview')
    expect(page.get_by_role('button', name='Preview', exact=True)).to_have_attribute('aria-pressed', 'true')
    expect(page.locator('.preview-table')).to_be_visible()
    expect(page.locator('.preview-table tbody tr')).to_have_count(100)
    page.screenshot(path=out / f'{prefix}-generated.png')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')

    activate(page, 'Remove selected column')
    expect(page.locator('.remove-dialog')).to_be_visible()
    activate(page, 'Cancel removal')
    expect(page.locator('.remove-dialog')).to_be_hidden()
    expect(page.locator('.definition-table tbody tr')).to_have_count(6)
    activate(page, 'Remove selected column')
    expect(page.locator('.remove-dialog')).to_be_visible()
    activate(page, 'Remove column')
    expect(page.locator('.remove-dialog')).to_be_hidden()
    expect(page.locator('.definition-table tbody tr')).to_have_count(5)
    expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_disabled()

    type_value(page, 'Column name', 'unfinished')
    expect(page.locator('.draft-summary')).to_have_text('Unapplied edits')
    before = state_snapshot(page)
    old = out / f'{prefix}-old.json'
    old.write_text('{"format":"ravel-workbook-experiment/1"}')
    large = new_recipe()
    large['table']['row_count'] = 1
    large['table']['fields'] = [dict(id=f'field{i}', name=f'column{i}', kind='category',
        missing_probability='0', values=[str(j).zfill(3) + 'x' * 197 for j in range(100)],
        probabilities=['0.01'] * 100) for i in range(49)]
    compact = json.dumps(large, separators=(',', ':')).encode('utf-8')
    assert len(compact) < MAX_BYTES
    large_path = out / f'{prefix}-too-large-when-saved.json'
    large_path.write_bytes(compact)
    for path, message in [(old, 'Old workbook experiment'), (large_path, '1 MiB when saved')]:
        reload_recipe(page, path)
        expect(page.locator('.load-dialog [role=alert]')).to_contain_text(message)
        expect(page.locator('.load-dialog [role=alert]')).to_be_in_viewport(ratio=1)
        activate(page, 'Cancel')
        expect(page.locator('.load-dialog')).to_be_hidden()
        after = state_snapshot(page)
        assert after == before, {key: [before[key], after[key]] for key in before if before[key] != after[key]}
    reload_recipe(page, out / f'{prefix}-built.recipe.json')
    expect(page.locator('.status-line')).to_contain_text('Recipe loaded')
    expect(page.locator('.load-dialog')).to_be_hidden()
    properties_width(page, 312)
    expect(page.locator('.preview-table')).to_have_count(0)
    expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_disabled()
    assert download(page, 'Save recipe', out / f'{prefix}-reloaded.recipe.json') == saved
    generate_table(page)
    assert download(page, 'Export CSV', out / f'{prefix}-reloaded.csv') == built
    reload_recipe(page, ROOT / 'examples/three-rows.recipe.json')
    expect(page.locator('.status-line')).to_contain_text('Recipe loaded')
    generate_table(page)
    assert preview_cells(page) == [['1','demo','10'], ['2','demo','12'], ['3','demo','14']]
    page.screenshot(path=out / f'{prefix}-reference.png')
    activate(page, 'Fields')
    activate(page, 'Select column id')
    expect(page.get_by_label('Column name', exact=True)).to_be_focused()
    expect(page.get_by_label('Start', exact=True)).to_have_value('1')
    type_value(page, 'Start', '10')
    apply(page)
    generate_table(page)
    assert preview_cells(page) == [['10','demo','10'], ['11','demo','12'], ['12','demo','14']]
    activate(page, 'Fields')
    activate(page, 'Select column value')
    expect(page.get_by_label('Column name', exact=True)).to_be_focused()
    type_value(page, 'Step', '-2')
    apply(page)
    generate_table(page)
    assert preview_cells(page) == [['10','demo','10'], ['11','demo','8'], ['12','demo','6']]
    home_theme = 'Dark' if theme == 'Light' else 'Light'
    set_theme(page, home_theme)
    home_link = page.get_by_role('link', name='Home', exact=True)
    expect(home_link).to_have_attribute('href', '/?theme=' + home_theme.lower())
    keyboard_to(page, home_link)
    page.keyboard.press('Enter')
    expect(page.locator('.leave-dialog')).to_be_visible()
    before = state_snapshot(page)
    activate(page, 'Keep editing')
    expect(page.locator('.leave-dialog')).not_to_be_visible()
    assert state_snapshot(page) == before
    keyboard_to(page, home_link)
    page.keyboard.press('Enter')
    expect(page.locator('.leave-dialog')).to_be_visible()
    activate(page, 'Leave table')
    expect(page).to_have_url(base + '/?theme=' + home_theme.lower())
    assert_branding(page, home_theme)
    activate(page, 'Open recipe')
    expect(page.locator('.load-dialog')).to_be_visible()
    page.locator('.load-dialog input[type=file]').set_input_files(ROOT / 'examples/three-rows.recipe.json')
    expect(page.locator('.status-line')).to_contain_text('Recipe loaded')
    generate_table(page)
    assert preview_cells(page) == [['1','demo','10'], ['2','demo','12'], ['3','demo','14']]
    return dict(viewport=viewport, theme=theme, result='passed', focus=focus,
                contrast_min=min(r['ratio'] for r in readings),
                assertions='1000 rows; hand reference; all rule editors; add/duplicate/rename/remove; independent streams; preview/CSV; save/reload; drafts/errors/stale export; PR8 layout/ARIA/theme/view regressions')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8090')
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/generator-browser')
    parser.add_argument('--channel', default='chrome')
    parser.add_argument('--workflow', choices=['rules', 'sample', 'extended', 'linked', 'pending', 'recovery', 'all'], default='rules')
    parser.add_argument('--smoke', action='store_true', help='One Light laptop case instead of the full theme/viewport matrix.')
    parser.add_argument('--verify-source', action='store_true', help='Require a dedicated test server identity matching the current runtime files.')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    results = dict(started_utc=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
                   platform=platform.platform(), playwright=version('playwright'), cases=[],
                   external_requests=[], external_websockets=[], page_errors=[])
    results['cli_command']=cli_command()
    def runtime_hashes():
        return {p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest()
                for p in (ROOT/'ravel').rglob('*') if p.is_file() and p.suffix in {'.py','.css','.js'} and '__pycache__' not in p.parts}
    results['local_runtime_sha256'] = runtime_hashes()
    try:
        if args.verify_source:
            assert urlparse(args.base_url).hostname in {'127.0.0.1','localhost'}
            with urlopen(args.base_url.rstrip('/')+'/__ravel_test/identity', timeout=3) as response:
                running = json.load(response)
            assert running['source_sha256'] == results['local_runtime_sha256'], 'Running app differs from the local runtime files.'
            results['running_source'] = running
        with sync_playwright() as p:
            browser = p.chromium.launch(channel=args.channel, headless=True)
            results['browser'] = browser.version
            for width, height in ([(1366,657)] if args.smoke else [(1366,657), (1280,800)]):
                for theme in (['Light'] if args.smoke else ['Light','Dark']):
                    viewport = dict(width=width, height=height)
                    context = browser.new_context(viewport=viewport, accept_downloads=True, has_touch=True)
                    def route(r):
                        if urlparse(r.request.url).hostname not in {'localhost','127.0.0.1'}:
                            results['external_requests'].append(r.request.url)
                            r.abort()
                        else:
                            r.continue_()
                    def websocket(ws):
                        if urlparse(ws.url).hostname not in {'localhost','127.0.0.1'}:
                            results['external_websockets'].append(ws.url)
                            ws.close()
                        else:
                            ws.connect_to_server()
                    context.route('**/*', route)
                    context.route_web_socket('**/*', websocket)
                    page = context.new_page()
                    page.on('pageerror', lambda e: results['page_errors'].append(str(e)))
                    try:
                        if args.workflow in {'rules','all'}:
                            results['cases'].append(exercise(page, args.base_url, out, viewport, theme))
                        if args.workflow in {'sample','all'}:
                            from scripts.sample_browser import exercise as sample_exercise
                            results['cases'].append(sample_exercise(page, args.base_url, out, viewport, theme))
                        if args.workflow in {'extended','all'}:
                            from scripts.extended_browser import exercise as extended_exercise
                            results['cases'].append(extended_exercise(page, args.base_url, out, viewport, theme))
                        if args.workflow in {'linked','all'}:
                            from scripts.linked_browser import exercise as linked_exercise
                            results['cases'].append(linked_exercise(page, args.base_url, out, viewport, theme))
                        if args.workflow in {'pending','all'}:
                            from scripts.pending_browser import exercise as pending_exercise
                            results['cases'].append(pending_exercise(page, args.base_url, out, viewport, theme))
                        if args.workflow in {'recovery','all'}:
                            from scripts.edit_recovery_browser import exercise as recovery_exercise
                            results['cases'].append(recovery_exercise(page, args.base_url, out, viewport, theme))
                    except Exception:
                        page.screenshot(path=out / 'failure.png')
                        raise
                    finally:
                        context.close()
                    print(f'PASS {width}x{height} {theme}', flush=True)
            browser.close()
        assert not results['external_requests'] and not results['external_websockets'] and not results['page_errors'], results
        assert runtime_hashes() == results['local_runtime_sha256'], 'Runtime files changed during this browser run.'
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
