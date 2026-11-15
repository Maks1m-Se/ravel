"""Mouse row hit targets and an end-to-end keyboard-only workbench workflow."""

import csv
from io import StringIO
import json

from playwright.sync_api import expect

from scripts.check_generator_browser import generate_table
from scripts.check_workbook_browser import activate, assert_error, contrast, keyboard_to, require_client, type_value


def option(page, name):
    return page.get_by_role('option', name='Select column ' + name, exact=True)


def pending(page, label, value=True):
    checkbox = page.get_by_role('checkbox', name=label, exact=True)
    target = checkbox if checkbox.count() else page.get_by_label(label, exact=True)
    expect(target.locator('xpath=ancestor::*[@data-editor][1]') if not target.get_attribute('data-editor') else target).to_have_attribute('data-draft', str(value).lower())


def key_download(page, label, path, expected_name=None, expected_client=None):
    if expected_client is not None:
        require_client(page, expected_client)
    before = page.evaluate('window.clientId')
    target = page.get_by_role('button', name=label, exact=True)
    keyboard_to(page, target)
    expect(target).to_be_focused()
    with page.expect_download() as download:
        page.keyboard.press('Enter')
    download.value.save_as(path)
    after = page.evaluate('window.clientId')
    diagnostic = dict(expected_name=expected_name, actual_name=download.value.suggested_filename,
                      client_before=before, client_after=after, url=page.url)
    if label == 'Save recipe':
        saved = json.loads(path.read_bytes())
        diagnostic['recipe_table'] = saved.get('table')
        diagnostic['recipe_seed'] = saved['seed']
    path.with_name(path.name + '.download.json').write_text(json.dumps(diagnostic, indent=2), encoding='utf-8')
    if expected_client is not None:
        require_client(page, expected_client)
    if expected_name:
        assert download.value.suggested_filename == expected_name, download.value.suggested_filename
    return path.read_bytes()


def key_upload(page, label, path):
    button = page.get_by_role('button', name=label, exact=True)
    keyboard_to(page, button)
    with page.expect_file_chooser() as chooser:
        page.keyboard.press('Enter')
    chooser.value.set_files(path)


def exercise(page, base, out, viewport, theme):
    prefix = f'{viewport["width"]}x{viewport["height"]}-{theme.lower()}-ux'
    page.goto(base + '/table?theme=' + theme.lower())
    expect(page.get_by_label('Column name', exact=True)).to_have_value('value')
    expected_client = page.evaluate('window.clientId')
    # Real pointer hits cover all four row surfaces; selection does not move into Properties.
    for selector in ['.field-name', 'td:nth-child(2)', 'td:nth-child(3)', None]:
        for identity, name in [('row_id', 'id'), ('value', 'value')]:
            row = page.locator(f'[data-field-id="{identity}"]')
            if selector:
                row.locator(selector).click()
            else:
                box = row.bounding_box()
                page.mouse.click(box['x'] + box['width'] - 4, box['y'] + box['height'] - 4)
            expect(page.get_by_label('Column name', exact=True)).to_have_value(name)
            expect(row).to_have_attribute('aria-selected', 'true')
            expect(row).to_be_focused()

    # Everything below uses Tab/arrows/text keys/Enter/Space. The native chooser
    # is opened by Enter; Playwright supplies only the invented path to that chooser.
    page.evaluate("window.uxPointers=0; document.addEventListener('pointerdown',()=>window.uxPointers++);")
    type_value(page, 'Table name', 'test_measurements')
    type_value(page, 'Rows', '12')
    type_value(page, 'Seed', '42')
    type_value(page, 'Maximum', '20')
    for label in ['Table name', 'Rows', 'Seed', 'Maximum']:
        pending(page, label)
    pending(page, 'Minimum', False)
    type_value(page, 'Seed', '17')
    pending(page, 'Seed', False)
    type_value(page, 'Seed', '42')

    keyboard_to(page, option(page, 'value'))
    page.keyboard.press('ArrowUp')
    expect(option(page, 'id')).to_be_focused()
    expect(page.get_by_label('Column name', exact=True)).to_have_value('value')
    page.keyboard.press('Enter')
    expect(page.get_by_label('Column name', exact=True)).to_have_value('id')
    type_value(page, 'Start', '2')
    keyboard_to(page, option(page, 'id'))
    page.keyboard.press('ArrowDown')
    page.keyboard.press('Space')
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('20')
    expect(page.locator('.draft-row')).to_have_count(2)
    expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_disabled()

    # Selection and text editing keep independent error/draft state.
    type_value(page, 'Minimum', '200')
    activate(page, 'Apply changes')
    assert_error(page, 'Minimum', 'Minimum must not exceed maximum')
    page.keyboard.press('Escape')
    expect(page.locator('.edit-actions')).to_have_attribute('data-pending', 'true')
    activate(page, 'Select column id')
    expect(page.get_by_label('Start', exact=True)).to_have_value('2')
    activate(page, 'Select column value')
    expect(page.get_by_label('Minimum', exact=True)).to_have_attribute('aria-invalid', 'true')
    activate(page, 'Select column id')
    activate(page, 'Apply changes')
    assert_error(page, 'Minimum', 'Minimum must not exceed maximum')
    expect(option(page, 'value')).to_have_attribute('aria-selected', 'true')
    type_value(page, 'Seed', '43')
    expect(page.get_by_label('Minimum', exact=True)).to_have_attribute('aria-invalid', 'true')
    type_value(page, 'Seed', '42')
    type_value(page, 'Maximum', '250')
    expect(page.get_by_label('Minimum', exact=True)).to_have_attribute('aria-invalid', 'false')
    type_value(page, 'Minimum', '0')
    type_value(page, 'Maximum', '20')
    # Cursor and OS/browser modifier chords are not intercepted by navigation.
    maximum = page.get_by_label('Maximum', exact=True)
    page.keyboard.press('Home')
    page.keyboard.press('Shift+End')
    assert maximum.evaluate('(e)=>e.selectionStart===0 && e.selectionEnd===2')
    page.keyboard.press('End')
    page.keyboard.press('Control+Enter')
    expect(page.locator('.edit-actions')).to_have_attribute('data-pending', 'true')
    styles = maximum.evaluate('''e => {
        const root=e.closest('.q-field');
        return {inputWeight:getComputedStyle(e).fontWeight,
                labelWeight:getComputedStyle(root.querySelector('.q-field__label')).fontWeight,
                markerWidth:getComputedStyle(root.querySelector('.q-field__label'),'::after').width,
                background:getComputedStyle(root.querySelector('.q-field__control')).backgroundColor,
                unchanged:getComputedStyle(document.querySelector('[data-setting=minimum] .q-field__control')).backgroundColor};
    }''')
    assert int(styles['inputWeight']) <= 500 and int(styles['labelWeight']) >= 600 and styles['markerWidth'] == '5px', styles
    assert styles['background'] != styles['unchanged'], styles
    styles['text_contrast_min'] = min(r['ratio'] for r in contrast(page, '.has-draft .q-field__label, .has-draft input'))
    page.screenshot(path=out / f'{prefix}-pending.png')
    activate(page, 'Apply changes')
    expect(page.get_by_label('Maximum', exact=True)).to_be_focused()
    expect(page.locator('[data-draft=true]')).to_have_count(0)
    expect(page.locator('.draft-row')).to_have_count(0)
    generate_table(page)
    expect(page.locator('.preview-view .preview-table tbody tr')).to_have_count(12)
    expect(page.get_by_role('tab', name='Preview', exact=True)).to_be_focused()
    csv_path, recipe_path = out / f'{prefix}.csv', out / f'{prefix}.recipe.json'
    expect(page.locator('.table-name-label')).to_have_text('test_measurements')
    payload = key_download(page, 'Export CSV', csv_path, 'test_measurements.csv', expected_client)
    key_download(page, 'Save recipe', recipe_path, 'test_measurements.recipe.json', expected_client)
    rows = list(csv.reader(StringIO(payload.decode())))
    assert rows[0] == ['id', 'value'] and len(rows) == 13
    assert [row[0] for row in rows[1:]] == list(map(str, range(2, 14)))
    assert all(0 <= int(row[1]) <= 20 for row in rows[1:])
    saved = json.loads(recipe_path.read_bytes())
    assert saved['table']['name'] == 'test_measurements' and saved['seed'] == 42
    expect(page.locator('.sheet-heading')).to_be_in_viewport(ratio=1)
    assert page.locator('.sheet').evaluate('(e)=>e.scrollTop') == 0
    page.screenshot(path=out / f'{prefix}-generated.png')

    # Tabs activate explicitly and arrows never steal text-caret navigation.
    keyboard_to(page, page.get_by_role('tab', name='Preview', exact=True))
    page.keyboard.press('ArrowLeft')
    expect(page.get_by_role('tab', name='Fields', exact=True)).to_be_focused()
    expect(page.get_by_role('tab', name='Preview', exact=True)).to_have_attribute('aria-selected', 'true')
    page.keyboard.press('Space')
    expect(page.get_by_role('tab', name='Fields', exact=True)).to_have_attribute('aria-selected', 'true')
    type_value(page, 'Maximum', '30')
    activate(page, 'Discard edits')
    expect(page.get_by_label('Maximum', exact=True)).to_have_value('20')
    expect(page.get_by_label('Maximum', exact=True)).to_be_focused()
    type_value(page, 'Maximum', '30')
    expect(page.locator('.status-line')).not_to_contain_text('discarded')
    type_value(page, 'Maximum', '20')
    pending(page, 'Maximum', False)
    expect(page.locator('.edit-actions')).to_have_attribute('data-pending', 'false')
    unique = page.get_by_role('checkbox', name='Require unique values', exact=True)
    keyboard_to(page, unique)
    page.keyboard.press('Space')
    pending(page, 'Require unique values')
    page.keyboard.press('Space')
    pending(page, 'Require unique values', False)
    expect(page.locator('.edit-actions')).to_have_attribute('data-pending', 'false')
    activate(page, 'Remove selected column')
    expect(page.locator('.remove-dialog')).to_be_visible()
    page.keyboard.press('Escape')
    expect(page.get_by_role('button', name='Remove selected column', exact=True)).to_be_focused()
    activate(page, 'Open recipe')
    key_upload(page, 'Choose recipe JSON', recipe_path)
    expect(page.locator('.load-dialog')).not_to_be_visible()
    expect(page.locator('.table-name-label')).to_have_text('test_measurements')
    expect(page.locator('.status-line')).to_contain_text('Recipe loaded')
    expect(page.get_by_label('Column name', exact=True)).to_be_focused()
    generate_table(page)
    assert key_download(page, 'Export CSV', out / f'{prefix}-replay.csv', expected_client=expected_client) == payload

    # Import the downloaded invented12 rows and extend to20 without changing any source cell.
    activate(page, 'Import CSV')
    key_upload(page, 'Choose sample CSV', csv_path)
    expect(page.locator('.sample-dialog .source-count')).to_contain_text('12 rows')
    check = page.get_by_role('checkbox', name='Use the displayed sequential identifier rules', exact=True)
    keyboard_to(page, check)
    page.keyboard.press('Space')
    activate(page, 'Use sample')
    expect(page.locator('.status-line')).to_contain_text('Sample imported')
    mode = page.get_by_label('Sample mode', exact=True)
    keyboard_to(page, mode)
    page.keyboard.press('Enter')
    page.keyboard.press('ArrowDown')
    page.keyboard.press('Enter')
    expect(mode).to_have_value('Extend to total')
    pending(page, 'Sample mode')
    type_value(page, 'Rows', '20')
    activate(page, 'Apply changes')
    generate_table(page)
    expect(page.locator('.preview-view .preview-table tbody tr')).to_have_count(20)
    extended = key_download(page, 'Export CSV', out / f'{prefix}-extended.csv', expected_client=expected_client)
    extension = list(csv.reader(StringIO(extended.decode())))
    assert extension[0] == rows[0] + ['row_origin']
    assert extension[1:13] == [row + ['retained'] for row in rows[1:]]
    assert len(extension[13:]) == 8 and all(row[-1] == 'generated' for row in extension[13:])
    assert [row[0] for row in extension[13:]] == list(map(str, range(14,22)))
    expect(page.locator('.sheet-heading')).to_be_in_viewport(ratio=1)
    assert page.locator('.sheet').evaluate('(e)=>e.scrollTop') == 0
    page.screenshot(path=out / f'{prefix}-extended.png')
    assert page.evaluate('window.uxPointers') == 0, 'Pointer event during keyboard-only workflow'
    return dict(workflow='ux', viewport=viewport, theme=theme, result='passed', marker_styles=styles,
                assertions='four mouse row targets; retained multiple drafts/atomic Apply; markers/exact revert; hidden-field errors; status freshness; Tab/arrows/manual selection/caret/modifier/Escape; unassisted Apply/Discard/dialog focus;12-row seed42 0-20 named downloads/keyboard chooser/replay;12 original+8 generated extension; zero keyboard-workflow pointer events; native OS chooser path supplied by Playwright, not native-dialog acceptance')
