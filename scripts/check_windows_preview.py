"""Verify actual frozen imports, complete manifests and current CLI workflows."""

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

from windows_preview_support import ROOT, verify_bundle, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    bundle=args.bundle.resolve()
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    manifest=verify_bundle(bundle)
    executable=bundle/'Ravel.exe'
    env=dict(os.environ,PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
    env.pop('PYTHONPATH',None)
    record=dict(started_utc=datetime.now(timezone.utc).isoformat(),version=manifest['version'],
        executable_sha256=sha256(executable.read_bytes()).hexdigest(),checks=[])
    def run(*arguments,expected=0):
        result=subprocess.run([str(executable),*map(str,arguments)],cwd=output,env=env,capture_output=True,text=True,timeout=60)
        record['checks'].append(dict(arguments=list(map(str,arguments)),exit_code=result.returncode,
                                     stdout=result.stdout,stderr=result.stderr))
        assert result.returncode==expected,result.stderr or result.stdout
        return result
    try:
        info=json.loads(run('--runtime-info').stdout)
        assert info['frozen'] is True and Path(info['root']).is_relative_to(bundle)
        assert all(Path(path).is_relative_to(bundle) for path in info['import_paths']),info
        record['runtime']=info
        run('ui','--port','0',expected=2)
        fixture=ROOT/'examples/three-rows.recipe.json'
        run('validate',fixture)
        path=output/'three.csv'
        run('generate',fixture,'--csv',path)
        with path.open(newline='',encoding='utf-8') as source:
            assert list(csv.reader(source))[1:]==[['1','demo','10'],['2','demo','12'],['3','demo','14']]
        before=path.read_bytes()
        run('generate',fixture,'--csv',path,expected=2)
        assert path.read_bytes()==before
        source=ROOT/'examples/sample-assisted/ten-rows.csv'
        with source.open(newline='',encoding='utf-8-sig') as stream:
            originals=list(csv.DictReader(stream))
        for mode in ['new','extend']:
            recipe=output/(mode+'.json')
            run('sample',source,'--recipe',recipe,'--mode',mode,'--rows','1000','--confirm-identifiers')
            run('validate',recipe)
            csv_path=output/(mode+'.csv')
            run('generate',recipe,'--csv',csv_path)
            with csv_path.open(newline='',encoding='utf-8') as stream:
                rows=list(csv.DictReader(stream))
            assert len(rows)==1000
            retained=rows[:10] if mode=='extend' else []
            if retained:
                assert [{key:row[key] for key in originals[0]} for row in retained]==originals
                assert all(row['row_origin']=='retained' for row in retained)
            assert all(row['row_origin']=='generated' for row in rows[len(retained):])
            replay=output/(mode+'-replayed.csv')
            run('generate',recipe,'--csv',replay)
            assert replay.read_bytes()==csv_path.read_bytes()
        linked=ROOT/'examples/linked/devices-measurements.recipe.json'
        directory=output/'linked'
        run('validate',linked)
        run('generate',linked,'--directory',directory)
        assert {path.name for path in directory.iterdir()}=={'devices.csv','measurements.csv','recipe.json','dictionary.json','run.json'}
        with (directory/'devices.csv').open(newline='',encoding='utf-8') as stream:
            assert [row['device_id'] for row in csv.DictReader(stream)]==['D01','D02','D03']
        with (directory/'measurements.csv').open(newline='',encoding='utf-8') as stream:
            rows=list(csv.DictReader(stream))
        assert [[row['device_id'],int(row['slot'])] for row in rows]==[[key,slot] for key in ['D01','D02','D03'] for slot in [1,2]]
        run('generate',linked,'--directory',directory,expected=2)
        run('generate',ROOT/'examples/extended-rules/three-days.recipe.json','--csv',output/'extended.csv')
        run('validate',ROOT/'examples/clinical-review/baseline-four-cases.json',expected=2)
        assert verify_bundle(bundle)==manifest
        assert record['executable_sha256']==sha256(executable.read_bytes()).hexdigest()
        record['result']='passed'
        print('Frozen imports, hand reference,1000new/extend,retention/origin/replay,linked exports,extended rules and no-overwrite passed.')
    except Exception as error:
        record['result']='failed'
        record['failure']=repr(error)
        raise
    finally:
        record['finished_utc']=datetime.now(timezone.utc).isoformat()
        write_json(output/'results.json',record)


if __name__=='__main__':
    main()
