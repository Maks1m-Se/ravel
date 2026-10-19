"""Linked workbench: structural reference, global state and complete export."""

from io import BytesIO
import json
import subprocess
import sys
import zipfile

from playwright.sync_api import expect

from ravel.dataset import payloads
from ravel.engine import generate,preview_rows
from ravel.recipe import loads
from scripts.check_workbook_browser import activate,assert_error,keyboard_to,properties_width,type_value


def exercise(page,base,out,viewport,theme):
    from scripts.check_generator_browser import ROOT,apply,cli_command,download,generate_table,layout_regressions,preview_cells,reload_recipe,state_snapshot
    prefix=f'{viewport["width"]}x{viewport["height"]}-{theme.lower()}-linked'
    if page.url.startswith(base) and page.evaluate('Boolean(window.ravelUnsaved)'):
        page.once('dialog',lambda dialog:dialog.accept())
    page.goto(base+'/?theme='+theme.lower())
    activate(page,'Use template')
    expect(page.get_by_role('button',name='Select table Devices',exact=True)).to_have_attribute('aria-pressed','true')
    expect(page.get_by_label('Rows',exact=True)).to_have_value('3')
    expect(page.get_by_label('Primary key',exact=True)).to_have_value('device_id')
    generate_table(page)
    assert [row[0] for row in preview_cells(page)]==['D01','D02','D03']
    package=download(page,'Export dataset ZIP',out/f'{prefix}-original.zip')
    with zipfile.ZipFile(BytesIO(package)) as archive:
        original_files={name:archive.read(name) for name in archive.namelist()}
    assert set(original_files)=={'devices.csv','measurements.csv','recipe.json','dictionary.json','run.json'}
    assert download(page,'Export CSV',out/f'{prefix}-devices.csv')==original_files['devices.csv']
    divider=page.get_by_role('separator',name='Properties',exact=True)
    keyboard_to(page,divider)
    page.keyboard.press('End')
    properties_width(page,560)
    activate(page,'Select table Measurements')
    expect(page.get_by_label('Column name',exact=True)).to_be_focused()
    properties_width(page,560)
    expect(page.get_by_role('button',name='Preview',exact=True)).to_have_attribute('aria-pressed','true')
    expected=json.loads((ROOT/'examples/linked/structural.expected.json').read_text())
    cells=preview_cells(page)
    assert [[row[1],int(row[2])] for row in cells]==expected['device_slot_pairs']
    assert download(page,'Export CSV',out/f'{prefix}-measurements.csv')==original_files['measurements.csv']
    activate(page,'Fields')
    type_value(page,'Rows','5')
    activate(page,'Apply changes')
    assert_error(page,'Rows','requires 6')
    activate(page,'Select table Devices')
    expect(page.get_by_role('button',name='Select table Measurements',exact=True)).to_have_attribute('aria-pressed','true')
    expect(page.locator('.status-line')).to_contain_text('Apply or discard')
    layout_regressions(page,viewport,theme)
    activate(page,'Discard edits')
    activate(page,'Relationship')
    dialog=page.locator('.relationship-dialog')
    expect(dialog).to_be_visible()
    expect(dialog.locator('.relationship-counts')).to_contain_text('Measurements: 6 rows')
    type_value(page,'Rows per parent','0')
    expect(dialog.get_by_role('alert')).to_contain_text('from 1')
    expect(page.get_by_role('button',name='Apply relationship and counts',exact=True)).to_be_disabled()
    type_value(page,'Rows per parent','3')
    expect(dialog.locator('.relationship-counts')).to_contain_text('Measurements: 9 rows')
    page.screenshot(path=out/f'{prefix}-relationship.png')
    activate(page,'Cancel relationship')
    expect(dialog).not_to_be_visible()
    expect(page.get_by_label('Rows',exact=True)).to_have_value('6')
    activate(page,'Relationship')
    type_value(page,'Rows per parent','3')
    expect(dialog.locator('.relationship-counts')).to_contain_text('Measurements: 9 rows')
    activate(page,'Apply relationship and counts')
    expect(dialog).not_to_be_visible()
    expect(page.get_by_label('Rows',exact=True)).to_have_value('9')
    expect(page.get_by_role('button',name='Export dataset ZIP',exact=True)).to_be_disabled()
    properties_width(page,312)
    generate_table(page)
    cells=preview_cells(page)
    assert [[row[1],int(row[2])] for row in cells]==[[device,slot] for device in ['D01','D02','D03'] for slot in [1,2,3]]
    old=cells
    activate(page,'Fields')
    activate(page,'Add column')
    expect(page.get_by_label('Column name',exact=True)).to_be_focused()
    type_value(page,'Column name','quality')
    apply(page)
    generate_table(page)
    assert [row[:-1] for row in preview_cells(page)]==old
    recipe_path=out/f'{prefix}.recipe.json'
    recipe=loads(download(page,'Save recipe',recipe_path))
    package=download(page,'Export dataset ZIP',out/f'{prefix}.zip')
    with zipfile.ZipFile(BytesIO(package)) as archive:
        actual={name:archive.read(name) for name in archive.namelist()}
    assert actual==payloads(generate(recipe))
    cli_folder=out/f'{prefix}-cli'
    run=subprocess.run(cli_command('generate',str(recipe_path),'--directory',str(cli_folder)),cwd=ROOT,capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    assert {path.name:path.read_bytes() for path in cli_folder.iterdir()}==actual
    expect(page.locator('.preview-view .preview-table tbody tr')).to_have_count(9)
    page.screenshot(path=out/f'{prefix}-generated.png')
    reload_recipe(page,recipe_path)
    expect(page.locator('.status-line')).to_contain_text('Recipe loaded')
    properties_width(page,312)
    expect(page.get_by_role('button',name='Export dataset ZIP',exact=True)).to_be_disabled()
    generate_table(page)
    activate(page,'Select table Measurements')
    expect(page.get_by_label('Column name',exact=True)).to_be_focused()
    assert preview_cells(page)==preview_rows(generate(recipe).table('measurements'))
    activate(page,'Fields')
    type_value(page,'Maximum','101')
    expect(page.locator('.draft-summary')).to_have_text('Unapplied edits')
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_disabled()
    before=state_snapshot(page)
    bad=json.loads(recipe_path.read_text(encoding='utf-8'))
    bad['tables'][1]['row_count']=5
    bad_path=out/f'{prefix}-invalid.json'
    bad_path.write_text(json.dumps(bad),encoding='utf-8')
    reload_recipe(page,bad_path)
    expect(page.locator('.load-dialog [role=alert]')).to_contain_text('Current table preserved')
    activate(page,'Cancel')
    expect(page.locator('.load-dialog')).not_to_be_visible()
    after=state_snapshot(page)
    assert after==before,{key:(before[key],after[key]) for key in before if before[key]!=after[key]}
    expect(page.get_by_role('button',name='Select table Measurements',exact=True)).to_have_attribute('aria-pressed','true')
    activate(page,'Discard edits')
    activate(page,'Select table Devices')
    expect(page.get_by_label('Column name',exact=True)).to_be_focused()
    type_value(page,'Constant value','invented-v2')
    apply(page)
    expect(page.get_by_role('button',name='Export dataset ZIP',exact=True)).to_be_disabled()
    activate(page,'Select table Measurements')
    expect(page.get_by_label('Column name',exact=True)).to_be_focused()
    expect(page.locator('.result-state')).to_contain_text('Out of date')
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_disabled()
    generate_table(page)
    assert preview_cells(page)==preview_rows(generate(recipe).table('measurements'))
    return dict(viewport=viewport,theme=theme,result='passed',workflow='linked',assertions='hand3+6 keys/slots; keyboard table switch and preserved Properties preference; drafts/count failure recovery; explicit relationship count preview/Cancel/apply;9child rows; independent field; completeZIP/dictionary/run/CLI; invalid-load atomicity; global stale/current state')
