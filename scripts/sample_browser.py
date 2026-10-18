"""Keyboard and actual-output checks for sample import, shared by browser runs."""

import csv
from io import StringIO

from playwright.sync_api import expect

from ravel.engine import csv_text, generate, preview_rows
from ravel.recipe import loads
from scripts.check_workbook_browser import activate, assert_error, keyboard_to, popup_ready, type_value


def exercise(page, base, out, viewport, theme):
    from scripts.check_generator_browser import ROOT, apply, download, generate_table, layout_regressions, preview_cells, reload_recipe, state_snapshot
    prefix = f'{viewport["width"]}x{viewport["height"]}-{theme.lower()}-sample'
    previous_unsaved = page.url.startswith(base + '/table')
    dialogs = []
    if previous_unsaved:
        def accept_navigation(dialog):
            dialogs.append(dialog.type)
            dialog.accept()
        page.once('dialog', accept_navigation)
    page.goto(base + '/?theme=' + theme.lower())
    if previous_unsaved:
        assert dialogs == ['beforeunload'], dialogs
    activate(page, 'Start from sample')
    dialog = page.locator('.sample-dialog')
    expect(dialog).to_be_visible()
    upload = dialog.locator('input[type=file]')
    upload.set_input_files(ROOT / 'examples/sample-assisted/ten-rows.csv')
    expect(dialog.locator('.source-count')).to_contain_text('10 rows')
    expect(dialog.locator('.sample-source tbody tr')).to_have_count(10)
    expect(dialog).to_contain_text('excluded from fitting')
    checkbox = page.get_by_role('checkbox', name='Use the displayed sequential identifier rules', exact=True)
    keyboard_to(page, checkbox)
    page.keyboard.press('Space')
    expect(checkbox).to_be_checked()
    count_box = dialog.locator('.source-count').bounding_box()
    source_box = dialog.locator('.source-scroll').bounding_box()
    assert count_box['height'] >= 12 and count_box['y']+count_box['height'] <= source_box['y']
    assert checkbox.evaluate('(root) => {const r=root.getBoundingClientRect(); return root.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}')
    page.screenshot(path=out / f'{prefix}-import.png')
    activate(page, 'Use sample')
    expect(dialog).not_to_be_visible()
    expect(page.locator('.sample-summary')).to_contain_text('0 retained + 1,000 new = 1,000 output')
    generate_table(page)
    recipe_bytes = download(page, 'Save recipe', out / f'{prefix}.recipe.json')
    payload = download(page, 'Export CSV', out / f'{prefix}.csv')
    recipe = loads(recipe_bytes)
    result = generate(recipe)
    assert payload == csv_text(result).encode()
    actual_preview, expected_preview = preview_cells(page), preview_rows(result)
    assert actual_preview == expected_preview, (len(actual_preview), len(expected_preview), [(a,b) for a,b in zip(actual_preview, expected_preview) if a != b][:3])
    rows = list(csv.reader(StringIO(payload.decode())))[1:]
    assert len(rows) == 1000 and all(row[-1] == 'generated' for row in rows)
    assert rows[0][0] == '11' and rows[-1][0] == '1010'
    activate(page, 'Fields')
    keyboard_to(page, page.get_by_label('Sample mode', exact=True))
    page.keyboard.press('Enter')
    popup_ready(page, '.q-menu')
    page.get_by_role('option', name='Extend to total', exact=True).click()
    expect(page.get_by_role('button', name='Export CSV', exact=True)).to_be_disabled()
    apply(page)
    expect(page.locator('.sample-summary')).to_contain_text('10 retained + 990 new = 1,000 output')
    generate_table(page)
    extended = download(page, 'Export CSV', out / f'{prefix}-extended.csv')
    records = list(csv.reader(StringIO(extended.decode())))[1:]
    original = list(csv.reader(StringIO((ROOT / 'examples/sample-assisted/ten-rows.csv').read_text(encoding='utf-8'))))[1:]
    assert records[:10] == [row + ['retained'] for row in original]
    assert len(records) == 1000 and records[-1][0] == '1000'
    expect(page.locator('.preview-view .preview-table tbody tr')).to_have_count(100)
    page.screenshot(path=out / f'{prefix}-extended.png')
    activate(page, 'Fields')
    type_value(page, 'Rows', '9')
    activate(page, 'Apply changes')
    assert_error(page, 'Rows', 'never truncated')
    before = state_snapshot(page)
    activate(page, 'Import CSV')
    bad = out / 'invalid-sample.csv'
    bad.write_text('a,b\n1\n', encoding='utf-8')
    dialog.locator('input[type=file]').set_input_files(bad)
    expect(dialog.get_by_role('alert')).to_contain_text('Current table preserved')
    activate(page, 'Cancel import')
    expect(dialog).not_to_be_visible()
    assert state_snapshot(page) == before
    layout_regressions(page, viewport, theme)
    activate(page, 'Discard edits')
    type_value(page, 'Rows', '12')
    apply(page)
    activate(page, 'Select column length_mm')
    expect(page.get_by_label('Column name', exact=True)).to_be_focused()
    type_value(page, 'Minimum', '12.2')
    type_value(page, 'Maximum', '12.2')
    type_value(page, 'Missing probability', '0')
    apply(page)
    expect(page.locator('[data-setting=minimum] .setting-origin')).to_have_text('Edited')
    activate(page, 'Select column material')
    expect(page.get_by_label('Column name', exact=True)).to_be_focused()
    type_value(page, 'Categories and probabilities', 'C,1')
    apply(page)
    generate_table(page)
    tiny = download(page, 'Export CSV', out / f'{prefix}-twelve.csv')
    expected = list(csv.reader(StringIO((ROOT / 'examples/sample-assisted/extend-twelve.expected.csv').read_text(encoding='utf-8'))))
    assert list(csv.reader(StringIO(tiny.decode()))) == expected
    saved_path = out / f'{prefix}-twelve.recipe.json'
    download(page, 'Save recipe', saved_path)
    reload_recipe(page, saved_path)
    expect(page.locator('.status-line')).to_contain_text('Recipe loaded')
    generate_table(page)
    assert preview_cells(page) == expected[1:]
    record_path = out / f'{prefix}.run.json'
    download(page, 'Save run record', record_path)
    page.screenshot(path=out / f'{prefix}-override.png')
    return dict(viewport=viewport, theme=theme, result='passed', workflow='sample',
                assertions='keyboard import/review; 1000 new and retained+990; exact source cells/origin; edited assumptions; hand override; invalid import/count recovery; layout/theme; preview/CSV/recipe reload/run record')
