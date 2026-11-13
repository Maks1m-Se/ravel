"""Invented recipe-name/content checks with client/navigation/download diagnostics."""

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ravel.recipe import dumps,new_recipe
from scripts.check_personal_web import free_port,runtime_hashes
from scripts.check_workbook_browser import activate,keyboard_to,require_client,type_value
from playwright.sync_api import expect,sync_playwright


def client_id(page):
    return page.evaluate('window.clientId')


def save(page,path,expected_client=None):
    before=client_id(page)
    if expected_client is not None:require_client(page,expected_client)
    target=page.get_by_role('button',name='Save recipe',exact=True)
    keyboard_to(page,target)
    expect(target).to_be_focused()
    with page.expect_download() as pending:page.keyboard.press('Enter')
    download=pending.value
    download.save_as(path)
    payload=path.read_bytes();document=json.loads(payload)
    table=document.get('table',{})
    result=dict(client_before=before,client_after=client_id(page),filename=download.suggested_filename,
                table_name=table.get('name'),row_count=table.get('row_count'),seed=document['seed'],sha256=sha256(payload).hexdigest())
    if expected_client is not None:require_client(page,expected_client)
    return result


def export_csv(page,path,name,rows,expected_client):
    require_client(page,expected_client)
    activate(page,'Generate table')
    expect(page.locator('.result-state')).to_contain_text('Current',timeout=30000)
    expect(page.locator('.preview-view .preview-table tbody tr')).to_have_count(rows)
    target=page.get_by_role('button',name='Export CSV',exact=True)
    keyboard_to(page,target);expect(target).to_be_focused()
    with page.expect_download() as pending:page.keyboard.press('Enter')
    download=pending.value;download.save_as(path)
    cells=list(csv.reader(StringIO(path.read_text(encoding='utf-8'))))
    assert download.suggested_filename==name+'.csv' and len(cells)==rows+1
    assert cells[0]==['id','value'] and [row[0] for row in cells[1:]]==list(map(str,range(1,rows+1)))
    require_client(page,expected_client)
    return dict(filename=download.suggested_filename,row_count=rows,sha256=sha256(path.read_bytes()).hexdigest(),client=expected_client)


def load(page,path,name):
    activate(page,'Open recipe')
    expect(page.locator('.load-dialog')).to_be_visible()
    page.locator('.load-dialog input[type=file]').set_input_files(path)
    expect(page.locator('.load-dialog')).not_to_be_visible()
    if 'tables' in json.loads(path.read_bytes()):
        expect(page.get_by_role('button',name='Select table '+name,exact=True)).to_have_attribute('aria-pressed','true')
    else:
        expect(page.locator('.table-name-label')).to_have_text(name)
    expect(page.get_by_label('Table name',exact=True)).to_have_value(name)


def names_case(browser,base,out,theme):
    prefix='names-'+theme.lower();events=[];console=[];downloads=[]
    context=browser.new_context(viewport={'width':1366,'height':657},accept_downloads=True)
    context.add_init_script('''window.exportKeyEvents=[];
        for(const type of ['keydown','keyup','click','focusin'])document.addEventListener(type,e=>{
            window.exportKeyEvents.push({type,key:e.key,id:e.target.id,label:e.target.getAttribute('aria-label'),
                role:e.target.getAttribute('role'),time:performance.now()});
        },true);''')
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:console.append(m.text) if any(w in m.text.lower() for w in ['reload','reconnect','timed out']) else None)
    page.on('framenavigated',lambda f:events.append({'url':f.url,'utc':datetime.now(timezone.utc).isoformat()}) if f==page.main_frame else None)
    page.on('download',lambda d:downloads.append(d.suggested_filename))
    page.goto(base+'/table?theme='+theme.lower())
    expect(page.get_by_label('Table name',exact=True)).to_have_value('Untitled table')
    original_client=client_id(page);results=[];csv_results=[]
    for name,rows,seed in [('alpha_measurements',12,42),('beta_samples',7,17)]:
        recipe=new_recipe();recipe['table'].update(name=name,row_count=rows);recipe['seed']=seed
        path=out/f'{prefix}-{name}.input.json';path.write_text(dumps(recipe),encoding='utf-8')
        load(page,path,name)
        csv_results.append(export_csv(page,out/f'{prefix}-{name}.csv',name,rows,original_client))
        actual=save(page,out/f'{prefix}-{name}.download.json',original_client)
        assert (actual['filename'],actual['table_name'],actual['row_count'],actual['seed'])==(name+'.recipe.json',name,rows,seed),actual
        assert json.loads((out/f'{prefix}-{name}.download.json').read_bytes())==recipe
        results.append({'expected_name':name+'.recipe.json',**actual})
    type_value(page,'Table name','renamed_beta')
    activate(page,'Apply changes')
    expect(page.locator('.table-name-label')).to_have_text('renamed_beta')
    expect(page.locator('.draft-summary')).to_have_text('All changes applied')
    csv_results.append(export_csv(page,out/f'{prefix}-renamed.csv','renamed_beta',7,original_client))
    actual=save(page,out/f'{prefix}-renamed.download.json',original_client)
    assert actual['filename']=='renamed_beta.recipe.json' and actual['table_name']=='renamed_beta',actual
    results.append({'expected_name':'renamed_beta.recipe.json',**actual})
    type_value(page,'Table name','unapplied_gamma')
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_disabled()
    count=len(downloads);activate(page,'Save recipe')
    expect(page.locator('.status-line')).to_contain_text('Apply or discard')
    assert len(downloads)==count
    expect(page.locator('.table-name-label')).to_have_text('renamed_beta')
    activate(page,'Discard edits')
    expect(page.get_by_label('Table name',exact=True)).to_have_value('renamed_beta')
    actual=save(page,out/f'{prefix}-discard.download.json',original_client)
    assert actual['filename']=='renamed_beta.recipe.json' and actual['table_name']=='renamed_beta',actual
    results.append({'expected_name':'renamed_beta.recipe.json',**actual})
    assert len(events)==1,events

    # An old success status cannot acknowledge a new, still pending upload.
    load(page,out/f'{prefix}-alpha_measurements.input.json','alpha_measurements')
    held=[];page.route('**/upload/**',lambda route:held.append(route))
    activate(page,'Open recipe')
    with page.expect_request('**/upload/**'):
        page.locator('.load-dialog input[type=file]').set_input_files(out/f'{prefix}-beta_samples.input.json')
    page.wait_for_timeout(100)
    assert held
    expect(page.locator('.status-line')).to_contain_text('Recipe loaded')
    expect(page.locator('.table-name-label')).to_have_text('alpha_measurements')
    expect(page.locator('.load-dialog')).to_be_visible()
    stale_barrier_reproduced=True
    for route in held:route.continue_()
    page.unroute('**/upload/**')
    expect(page.locator('.load-dialog')).not_to_be_visible()
    expect(page.locator('.table-name-label')).to_have_text('beta_samples')
    actual=save(page,out/f'{prefix}-synchronized.download.json',original_client)
    assert actual['filename']=='beta_samples.recipe.json' and actual['table_name']=='beta_samples',actual
    results.append({'expected_name':'beta_samples.recipe.json',**actual})
    csv_results.append(export_csv(page,out/f'{prefix}-before-reset.csv','beta_samples',7,original_client))
    key_events=page.evaluate('window.exportKeyEvents')
    assert len(events)==1,events
    page.screenshot(path=out/f'{prefix}-before-reset.png')

    # A controlled document reload reproduces the old screenshot/name pattern.
    # This is a negative test, not proof of why the original document changed.
    page.once('dialog',lambda d:d.accept())
    page.reload()
    expect(page.get_by_label('Table name',exact=True)).to_have_value('Untitled table')
    reset=save(page,out/f'{prefix}-controlled-reset.download.json')
    assert reset['filename']=='untitled_table.recipe.json' and reset['table_name']=='Untitled table',reset
    assert reset['client_after']!=original_client
    count=len(downloads)
    try:
        save(page,out/f'{prefix}-guarded-must-not-exist.json',original_client)
        raise AssertionError('Missing client identity guard')
    except AssertionError as error:
        assert str(error).startswith('Workspace changed:'),str(error)
        guard_message=str(error)
    assert len(downloads)==count and not (out/f'{prefix}-guarded-must-not-exist.json').exists()
    assert not errors,errors
    record=dict(theme=theme,result='passed',sequential_downloads=results,csv_downloads=csv_results,unapplied_download_blocked=True,
                stale_load_status_barrier_reproduced=stale_barrier_reproduced,controlled_reset=reset,
                guard_message=guard_message,navigations=events,console=console,key_events=key_events,page_errors=errors)
    page.screenshot(path=out/f'{prefix}-controlled-reset.png')
    context.close();return record


def refusal_case(browser,base,out,theme):
    context=browser.new_context(viewport={'width':1366,'height':657},accept_downloads=True)
    page=context.new_page();downloads=[];errors=[];cases=[]
    page.on('download',lambda d:downloads.append(d.suggested_filename))
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base+'/table?theme='+theme.lower())
    expect(page.get_by_label('Table name',exact=True)).to_have_value('Untitled table')
    expected_client=client_id(page)
    for name,fragment in [('casefold','collide on Windows'),('reserved','Reserved Windows filename')]:
        load(page,ROOT/f'tests/fixtures/exports/{name}.recipe.json','Devices')
        activate(page,'Generate table')
        expect(page.locator('.result-state')).to_contain_text('Current',timeout=30000)
        expect(page.locator('.preview-view .preview-table tbody tr')).to_have_count(3)
        messages=[];source=json.loads((ROOT/f'tests/fixtures/exports/{name}.recipe.json').read_bytes())
        for table,rows in [('Devices',3),('Measurements',6)]:
            activate(page,'Select table '+table)
            expect(page.locator('.preview-view .preview-table tbody tr')).to_have_count(rows)
            recipe_path=out/f'refusal-{theme.lower()}-{name}-{table}.recipe.json'
            saved=save(page,recipe_path,expected_client)
            assert saved['filename']=='dataset.recipe.json' and json.loads(recipe_path.read_bytes())==source
            expect(page.locator('.status-line')).to_contain_text('Recipe saved')
            before=list(downloads)
            activate(page,'Export CSV')
            expect(page.locator('.status-line')).to_contain_text(fragment)
            expect(page.locator('.status-line')).to_be_in_viewport(ratio=1)
            messages.append(page.locator('.status-line').inner_text())
            assert downloads==before,downloads
        saved=save(page,out/f'refusal-{theme.lower()}-{name}-before-zip.recipe.json',expected_client)
        expect(page.locator('.status-line')).to_contain_text('Recipe saved')
        before=list(downloads)
        activate(page,'Export dataset ZIP')
        expect(page.locator('.status-line')).to_contain_text(fragment)
        messages.append(page.locator('.status-line').inner_text())
        assert downloads==before,downloads
        require_client(page,expected_client)
        expect(page.locator('.result-state')).to_contain_text('Current')
        page.screenshot(path=out/f'refusal-{theme.lower()}-{name}.png')
        cases.append(dict(fixture=name,csv_downloads_blocked=2,zip_download_blocked=True,messages=messages,recipe_preserved=True))
    assert not errors,errors
    context.close();return dict(theme=theme,result='passed',workflow='portable-refusal',cases=cases,page_errors=errors)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--channel',default='msedge')
    parser.add_argument('--serve',type=int,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.serve:
        from ravel.ui import app,launch
        from nicegui.client import Client
        trace=[];original_download=Client.download
        def audited_download(client,src,filename=None,media_type=''):
            item=dict(utc=datetime.now(timezone.utc).isoformat(),client=client.id,filename=filename,media_type=media_type)
            if isinstance(src,(str,bytes)):
                try:
                    document=json.loads(src)
                    item.update(table_name=document.get('table',{}).get('name'),seed=document.get('seed'))
                except (ValueError,UnicodeDecodeError):pass
            trace.append(item)
            return original_download(client,src,filename,media_type)
        Client.download=audited_download
        app.get('/__ravel_test/identity')(lambda:{'source_sha256':runtime_hashes()})
        app.get('/__ravel_test/download-trace')(lambda:trace)
        launch(port=args.serve);return
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    record=dict(started_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),channel=args.channel,runtime_sha256=runtime_hashes(),cases=[])
    base=f'http://127.0.0.1:{free_port()}'
    log=(out/'server.log').open('w',encoding='utf-8')
    process=subprocess.Popen([sys.executable,__file__,'--serve',base.rsplit(':',1)[1],'--output',str(out)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            if process.poll() is not None:raise RuntimeError('Owned server stopped; inspect server.log')
            try:
                with urlopen(base+'/__ravel_test/identity',timeout=1) as response:running=json.load(response)
                assert running['source_sha256']==record['runtime_sha256'];break
            except OSError:time.sleep(.2)
        else:raise RuntimeError('Owned server did not start')
        with sync_playwright() as p:
            browser=p.chromium.launch(channel=args.channel,headless=True);record['browser']=browser.version
            try:
                for theme in ['Light','Dark']:
                    record['cases'].append(names_case(browser,base,out,theme))
                    record['cases'].append(refusal_case(browser,base,out,theme))
            except Exception:
                for context in browser.contexts:
                    for page in context.pages:
                        page.screenshot(path=out/'failure.png')
                        (out/'failure-state.json').write_text(json.dumps(page.evaluate('''() => ({client:window.clientId,
                            name:document.querySelector('.table-name-label')?.textContent,status:document.querySelector('.status-line')?.textContent,
                            key_events:window.exportKeyEvents})'''),indent=2),encoding='utf-8')
                raise
            browser.close()
        with urlopen(base+'/__ravel_test/download-trace',timeout=3) as response:record['server_download_trace']=json.load(response)
        assert runtime_hashes()==record['runtime_sha256'];record['result']='passed'
    except Exception:
        record['result']='failed';record['failure']=traceback.format_exc()
        raise
    finally:
        process.terminate();process.wait(timeout=15);log.close()
        record['finished_utc']=datetime.now(timezone.utc).isoformat()
        (out/'results.json').write_text(json.dumps(record,indent=2),encoding='utf-8')


if __name__=='__main__':main()
