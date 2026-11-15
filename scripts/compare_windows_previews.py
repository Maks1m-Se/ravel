"""Compare actual candidate contents honestly; report byte differences separately."""

import argparse
import json
from pathlib import Path
import zipfile

from windows_preview_support import verify_bundle, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('first',type=Path)
    parser.add_argument('second',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    first,second=verify_bundle(args.first.resolve()),verify_bundle(args.second.resolve())
    same_inputs=first['source']['files']==second['source']['files']
    same_environment=first['environment']==second['environment']
    same_paths=first['files'].keys()==second['files'].keys()
    changed=[name for name in first['files'].keys()&second['files'].keys() if first['files'][name]!=second['files'][name]]
    volatile={'Ravel.exe','ravel-corresponding-source.zip','_internal/base_library.zip'}
    stable_changes=sorted(set(changed)-volatile)
    def zip_contents(bundle,name):
        with zipfile.ZipFile(bundle/name) as archive:
            return {name:archive.read(name) for name in archive.namelist()}
    same_source_zip=zip_contents(args.first,'ravel-corresponding-source.zip')==zip_contents(args.second,'ravel-corresponding-source.zip')
    same_base_library=zip_contents(args.first,'_internal/base_library.zip')==zip_contents(args.second,'_internal/base_library.zip')
    result=dict(same_declared_inputs=same_inputs,same_environment=same_environment,same_output_paths=same_paths,
        missing=sorted(first['files'].keys()-second['files'].keys()),added=sorted(second['files'].keys()-first['files'].keys()),
        changed_bytes=sorted(changed),bit_identical=not changed and same_paths,
        unexpected_stable_content_changes=stable_changes,same_source_archive_contents=same_source_zip,
        same_base_library_contents=same_base_library,
        result='passed' if same_inputs and same_environment and same_paths and not stable_changes and same_source_zip and same_base_library else 'failed',
        scope='Both actual manifests verified; equal declared content contract does not assert bit-identical PE/ZIP output.')
    write_json(args.output,result)
    print(json.dumps({key:value for key,value in result.items() if key!='changed_bytes'},indent=2))
    print(f'{len(changed)} paths have changed bytes; exact list retained in '+str(args.output))
    if result['result']!='passed':
        raise SystemExit(1)


if __name__=='__main__':
    main()
