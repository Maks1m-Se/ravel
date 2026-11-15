"""The fixed normal/Bernoulli subset of R5; correlation remains unimplemented."""

import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ravel.engine import generate
from ravel.recipe import loads

SEEDS=(17,42,101,2026,65537)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    recipe=loads((ROOT/'examples/extended-rules/statistical-reference.json').read_bytes())
    record=dict(started_utc=datetime.now(timezone.utc).isoformat(),seeds=list(SEEDS),n=100000,python=sys.version,cases=[],overall_R5='incomplete: Gaussian-pair correlation not implemented')
    for seed in SEEDS:
        recipe['seed']=seed
        result=generate(recipe)
        normal=[float(row[0]) for row in result.rows]
        mean,sd=statistics.fmean(normal),statistics.stdev(normal)
        proportion=sum(row[1] for row in result.rows)/len(result.rows)
        passed=abs(mean)<=.02 and .98<=sd<=1.02 and .29<=proportion<=.31
        case=dict(seed=seed,mean=mean,sample_sd=sd,bernoulli_proportion=proportion,result='passed' if passed else 'failed')
        record['cases'].append(case)
        print(json.dumps(case),flush=True)
    record['result']='passed' if all(case['result']=='passed' for case in record['cases']) else 'failed'
    record['finished_utc']=datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    return 0 if record['result']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
