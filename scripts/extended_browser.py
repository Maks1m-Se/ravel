"""Actual editor/output checks for version-3 rules and source-aware quotas."""

from collections import Counter
import csv
from io import StringIO
import subprocess
import sys

from playwright.sync_api import expect

from ravel.engine import csv_text,generate,preview_rows
from ravel.recipe import dumps,loads
from ravel.sample import profile
from scripts.check_workbook_browser import activate,assert_error,keyboard_to,popup_ready,type_value


def exercise(page,base,out,viewport,theme):
    from scripts.check_generator_browser import ROOT,apply,choose_rule,cli_command,download,generate_table,preview_cells,reload_recipe
    prefix=f'{viewport["width"]}x{viewport["height"]}-{theme.lower()}-extended'
    if page.url.startswith(base) and page.evaluate('Boolean(window.ravelUnsaved)'):
        page.once('dialog',lambda dialog:dialog.accept())
    page.goto(base+'/table?theme='+theme.lower())
    reload_recipe(page,ROOT/'examples/extended-rules/three-days.recipe.json')
    expect(page.locator('.status-line')).to_contain_text('Recipe loaded')
    generate_table(page)
    cells=preview_cells(page)
    assert [row[1] for row in cells]==['2024-02-28','2024-02-29','2024-03-01']
    assert all(row[2]=='true' for row in cells)
    assert {row[3] for row in cells}=={'7','8','9'}
    assert Counter(row[4] for row in cells)=={'A':2,'B':1}
    activate(page,'Fields')
    activate(page,'Add column')
    expect(page.get_by_label('Column name',exact=True)).to_be_focused()
    choose_rule(page,'Normal numeric')
    type_value(page,'Standard deviation','0')
    activate(page,'Apply changes')
    assert_error(page,'Standard deviation','must be positive')
    type_value(page,'Standard deviation','1')
    apply(page)
    generate_table(page)
    expect(page.locator('.preview-view .preview-table tbody tr')).to_have_count(3)
    page.screenshot(path=out/f'{prefix}-normal.png')
    activate(page,'Fields')
    choose_rule(page,'Boolean')
    type_value(page,'True probability','1')
    apply(page)
    generate_table(page)
    assert all(row[-1]=='true' for row in preview_cells(page))
    activate(page,'Fields')
    choose_rule(page,'Calendar date')
    type_value(page,'Minimum','2024-02-29')
    type_value(page,'Maximum','2024-02-29')
    apply(page)
    generate_table(page)
    assert all(row[-1]=='2024-02-29' for row in preview_cells(page))
    activate(page,'Fields')
    choose_rule(page,'Date sequence')
    type_value(page,'Start','2023-02-29')
    activate(page,'Apply changes')
    assert_error(page,'Start','valid calendar date')
    type_value(page,'Start','2024-02-28')
    apply(page)
    generate_table(page)
    assert [row[-1] for row in preview_cells(page)]==['2024-02-28','2024-02-29','2024-03-01']
    activate(page,'Fields')
    choose_rule(page,'Random integer')
    type_value(page,'Minimum','7')
    type_value(page,'Maximum','9')
    unique=page.get_by_role('checkbox',name='Require unique values',exact=True)
    keyboard_to(page,unique)
    page.keyboard.press('Space')
    expect(unique).to_be_checked()
    apply(page)
    generate_table(page)
    assert {row[-1] for row in preview_cells(page)}=={'7','8','9'}
    activate(page,'Fields')
    type_value(page,'Rows','4')
    activate(page,'Apply changes')
    assert_error(page,'Rows','3 available')
    type_value(page,'Rows','3')
    expect(page.locator('.draft-summary')).to_have_text('All changes applied')
    expect(page.get_by_role('button',name='Apply changes',exact=True)).to_be_disabled()
    expect(page.locator('.output-panel [aria-invalid=true]')).to_have_count(0)
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_enabled()

    source=ROOT/'examples/sample-assisted/ten-rows.csv'
    source_recipe=out/f'{prefix}-source.recipe.json'
    source_recipe.write_text(dumps(profile(source.read_bytes(),mode='extend',count=12,confirm_identifiers=True)),encoding='utf-8')
    reload_recipe(page,source_recipe)
    expect(page.locator('.status-line')).to_contain_text('Recipe loaded')
    choose_rule(page,'Exact category counts')
    type_value(page,'Categories and exact counts','A,7\nB,5')
    keyboard_to(page,page.get_by_label('Quota scope',exact=True))
    page.keyboard.press('Enter')
    popup_ready(page,'.q-menu')
    page.get_by_role('option',name='Final output including originals',exact=True).click()
    apply(page)
    generate_table(page)
    expected_preview=preview_cells(page)
    expect(page.locator('[data-setting=quotas] .setting-origin')).to_have_text('Edited')
    assert Counter(row[2] for row in expected_preview)=={'A':7,'B':5}
    assert [row[-1] for row in expected_preview]==['retained']*10+['generated']*2
    activate(page,'Fields')
    expect(page.get_by_role('button',name='Fields',exact=True)).to_have_attribute('aria-pressed','true')
    expect(page.locator('.definition-table')).to_be_visible()
    applied=page.locator('.definition-table').text_content()
    type_value(page,'Categories and exact counts','A,5\nB,7')
    activate(page,'Apply changes')
    assert_error(page,'Categories and exact counts','already exceed')
    assert page.locator('.definition-table').text_content()==applied
    assert preview_cells(page)==expected_preview
    type_value(page,'Categories and exact counts','A,7\nB,5')
    expect(page.locator('.draft-summary')).to_have_text('All changes applied')
    expect(page.get_by_role('button',name='Apply changes',exact=True)).to_be_disabled()
    expect(page.locator('.properties [aria-invalid=true]')).to_have_count(0)
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_enabled()
    generate_table(page)
    recipe_path=out/f'{prefix}.recipe.json'
    recipe=loads(download(page,'Save recipe',recipe_path))
    payload=download(page,'Export CSV',out/f'{prefix}.csv')
    assert payload==csv_text(generate(recipe)).encode()
    assert preview_cells(page)==preview_rows(generate(recipe))
    cli_path=out/f'{prefix}-cli.csv'
    cli=subprocess.run(cli_command('generate',str(recipe_path),'--csv',str(cli_path)),cwd=ROOT,capture_output=True,text=True)
    assert cli.returncode==0,cli.stderr
    assert cli_path.read_bytes()==payload
    page.screenshot(path=out/f'{prefix}-final-quota.png')
    return dict(viewport=viewport,theme=theme,result='passed',workflow='extended',assertions='normal/SD recovery; Boolean1; inclusive/leap/date sequence/error; unique capacity failure/recovery; final source quotas/impossible retained counts; real preview/CSV/CLI/recipe agreement')
