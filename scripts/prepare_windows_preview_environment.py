"""Create a fresh, offline pinned private-build venv; never reuse an existing one."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from windows_preview_support import ROOT, LOCKS


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--wheelhouse',type=Path,action='append',required=True)
    args=parser.parse_args()
    output=args.output.resolve()
    if output.exists():
        parser.error('Use a new environment directory to preserve prior evidence.')
    env=dict(os.environ,PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
    env.pop('PYTHONPATH',None)
    subprocess.run([sys.executable,'-I','-m','venv','--without-pip',str(output)],env=env,check=True)
    python=output/'Scripts/python.exe'
    command=[sys.executable,'-I','-m','pip','--python',str(python),'install','--no-index','--no-deps']
    for folder in args.wheelhouse:
        command.extend(['--find-links',str(folder.resolve())])
    for lock in LOCKS:
        command.extend(['-r',str(ROOT/lock)])
    subprocess.run(command,env=env,check=True)
    subprocess.run([sys.executable,'-I','-m','pip','--python',str(python),'check'],env=env,check=True)
    code='import sys,json;sys.path.insert(0,sys.argv[1]);from windows_preview_support import verify_environment;print(json.dumps(verify_environment()))'
    checked=subprocess.check_output([str(python),'-I','-c',code,str(ROOT/'scripts')],env=env,text=True)
    (output/'verified-environment.json').write_text(checked,encoding='utf-8')
    print(json.dumps(dict(environment=str(output),verified=json.loads(checked)),indent=2))


if __name__=='__main__':
    main()
