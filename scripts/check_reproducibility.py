"""Bounded local R3/R4 evidence using supported generic generation only."""
import argparse
from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime,timezone
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ravel.dataset import DatasetResult,template
from ravel.engine import csv_text,generate,run_metadata
from ravel.recipe import ValidationError,dumps,loads,new_field,new_recipe
from ravel.sample import profile
from scripts.check_rule_statistics import SEEDS


def hashes(result):
    tables=result.tables if isinstance(result,DatasetResult) else [('main',result)]
    by_table={identity:sha256(csv_text(table).encode('utf-8')).hexdigest() for identity,table in tables}
    canonical=sha256(json.dumps(by_table,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(dataset=canonical,tables=by_table)


def independent(recipe,result):
    changed=deepcopy(recipe)
    table=changed['tables'][0] if 'tables' in changed else changed['table']
    field=new_field('integer',table['fields'])
    field.update(id='independent_probe',name='independent_probe')
    table['fields'].append(field)
    candidate=generate(changed)
    original_tables=result.tables if isinstance(result,DatasetResult) else [('main',result)]
    for identity,original in original_tables:
        actual=candidate.table(identity) if isinstance(candidate,DatasetResult) else candidate
        indices=[actual.headers.index(name) for name in original.headers]
        assert tuple(tuple(row[index] for index in indices) for row in actual.rows)==original.rows
    return hashes(candidate)


def expected_failure(recipe,fragment):
    before=deepcopy(recipe)
    try:
        generate(recipe)
    except ValidationError as error:
        assert fragment in str(error),str(error)
        assert recipe==before
        return str(error)
    raise AssertionError('Infeasible request unexpectedly generated a successful result.')


def check_sample(recipe,result,source_rows):
    rows=list(csv.reader(StringIO(csv_text(result))))
    assert len(rows)==1001
    count=10 if recipe['sample']['mode']=='extend' else 0
    assert rows[1:count+1]==[row+['retained'] for row in source_rows[:count]]
    assert [row[-1] for row in rows[1:]]==['retained']*count+['generated']*(1000-count)
    assert [row[0] for row in rows[count+1:]]==list(map(str,range(11,11+1000-count)))
    metadata=run_metadata(result)
    assert (metadata['retained_rows'],metadata['generated_rows'])==(count,1000-count)
    assert metadata['source_sha256']==recipe['sample']['sha256']
    assert sha256(recipe['sample']['csv_utf8'].encode()).hexdigest()==metadata['source_sha256']


def sample_variants(recipe,source_rows):
    mode=recipe['sample']['mode']
    retained=10 if mode=='extend' else 0
    edited=deepcopy(recipe)
    edited['table']['fields'][1].update(minimum='12.2',maximum='12.2',missing_probability='0')
    edited['table']['fields'][2].update(values=['C'],probabilities=['1'])
    rows=list(csv.reader(StringIO(csv_text(generate(edited)))))[1:]
    assert all(row[1:3]==['12.2','C'] for row in rows[retained:])
    assert rows[:retained]==[row+['retained'] for row in source_rows[:retained]]
    quota=deepcopy(recipe)
    quota['format']='ravel-single-table/3'
    quota['table']['fields'][2]=dict(id='sample_2',name='material',kind='category_quota',
        values=['A','B','C'],counts=[400,400,200],missing_count=0,missing_probability='0',
        scope='final' if retained else 'generated')
    rows=list(csv.reader(StringIO(csv_text(generate(quota)))))[1:]
    assert Counter(row[2] for row in rows)=={'A':400,'B':400,'C':200}
    assert rows[:retained]==[row+['retained'] for row in source_rows[:retained]]
    failures=[]
    if retained:
        quota['table']['fields'][2]['counts']=[0,800,200]
        failures.append(expected_failure(quota,'already exceed'))
    unconfirmed=deepcopy(recipe)
    unconfirmed['sample']['confirmed']=[]
    failures.append(expected_failure(unconfirmed,'Confirm'))
    collision=deepcopy(recipe)
    collision['table']['fields'][0]['start']=1
    failures.append(expected_failure(collision,'collide'))
    return dict(override='passed',quota_counts={'A':400,'B':400,'C':200},expected_failures=failures)


def run():
    payload=(ROOT/'examples/sample-assisted/ten-rows.csv').read_bytes()
    source_rows=list(csv.reader(StringIO(payload.decode())))[1:]
    assert len(source_rows)==10
    cases=[]
    for seed in SEEDS:
        explicit=new_recipe()
        explicit.update(seed=seed)
        recipes={'explicit':explicit,
                 'sample-new':profile(payload,mode='new',count=1000,seed=seed,confirm_identifiers=True),
                 'sample-extend':profile(payload,mode='extend',count=1000,seed=seed,confirm_identifiers=True),
                 'linked':template()}
        recipes['linked']['seed']=seed
        for name,recipe in recipes.items():
            runs=[generate(loads(dumps(recipe))) for _ in range(3)]
            fingerprints=[hashes(result) for result in runs]
            assert len({value['dataset'] for value in fingerprints})==1,(name,seed)
            case=dict(recipe=name,seed=seed,recipe_sha256=sha256(dumps(recipe).encode()).hexdigest(),
                      repeats=fingerprints,independent_field=independent(recipe,runs[0]),result='passed')
            if name.startswith('sample-'):
                for result in runs:
                    check_sample(recipe,result,source_rows)
                case['sample']=sample_variants(recipe,source_rows)
            cases.append(case)
    files=[path for path in (ROOT/'ravel').rglob('*.py') if '__pycache__' not in path.parts]
    files += [ROOT/'scripts/check_reproducibility.py',ROOT/'scripts/check_rule_statistics.py',ROOT/'requirements-ui.lock',ROOT/'requirements-review.lock']
    files += [ROOT/'examples/sample-assisted/ten-rows.csv',ROOT/'examples/linked/devices-measurements.recipe.json']
    source_hashes={path.relative_to(ROOT).as_posix():sha256(path.read_bytes()).hexdigest() for path in files}
    git=['git','-c',f'safe.directory={ROOT.as_posix()}','-C',str(ROOT)]
    revision=subprocess.run(git+['rev-parse','HEAD'],capture_output=True,text=True)
    try:
        profile('text\n'+'\n'.join('category_'+str(i) for i in range(101))+'\n')
    except ValidationError as error:
        assert '100 text categories' in str(error)
        unsupported=str(error)
    else:
        raise AssertionError('Unsupported 101-category profile was accepted.')
    return dict(result='passed',cases=cases,seeds=list(SEEDS),repeats=3,primary_generations=60,
        python=sys.version,platform=platform.platform(),source_commit=revision.stdout.strip(),
        source_state='HEAD plus the exact declared source_sha256 map; evidence script locally prepared at execution',
        unsupported_profile_rejection=unsupported,
        source_sha256=source_hashes,scope='local pinned environment; not cross-platform or performance acceptance',
        R3='partial: local generic evidence',R4='partial: supported generic sample evidence',R5='incomplete: Gaussian-pair correlation unimplemented')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    started=datetime.now(timezone.utc).isoformat()
    record=run()
    record.update(started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(f'PASS {len(record["cases"])} seed/recipe cases;60 primary generations, independent fields, both10-to1000 modes, overrides/quotas/rejections.')
