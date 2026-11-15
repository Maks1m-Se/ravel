"""Verify the tagged NiceGUI core lock's npm archives and retain supplied notices."""

import argparse
import base64
import difflib
from hashlib import sha256, sha512
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile

from collect_windows_preview_sources import download
from windows_preview_support import write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--material',type=Path,required=True)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--resume',action='store_true',help='Resume only after rechecking every cached archive against the immutable lock.')
    args=parser.parse_args()
    source=args.material.resolve()
    records=json.loads((source/'sources.json').read_text())
    for record in records['records']:
        path=(source/record['file']).resolve()
        if not path.is_relative_to(source) or sha256(path.read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Prepared source checksum mismatch: '+record['file'])
    output=args.output.resolve()
    if args.resume:
        previous=output/'sources.json'
        backup=output/('sources.previous-'+sha256(previous.read_bytes()).hexdigest()[:12]+'.json')
        if not backup.exists():
            shutil.copyfile(previous,backup)
        records=json.loads(previous.read_text())
        for record in json.loads((source/'sources.json').read_text())['records']:
            assert sha256((output/record['file']).read_bytes()).hexdigest()==record['sha256']
    else:
        shutil.copytree(source,output)
        (output/'npm').mkdir()
    lock=json.loads((source/'NiceGUI-3.18.0-package-lock.json').read_text())
    components=[]
    correspondence=[]
    comparisons={
        'vue':[('dist/vue.esm-browser.js','vue.esm-browser.js'),('dist/vue.esm-browser.prod.js','vue.esm-browser.prod.js')],
        'quasar':[('dist/quasar.umd.js','quasar.umd.js'),('dist/quasar.umd.prod.js','quasar.umd.prod.js')],
        '@tailwindcss/browser':[('dist/index.global.js','tailwindcss.min.js')],
        'socket.io':[('client-dist/socket.io.min.js','socket.io.min.js'),('client-dist/socket.io.min.js.map','socket.io.min.js.map')],
        '@unocss/runtime':[(name,'unocss/'+name) for name in ['core.global.js','preset-mini.global.js','preset-wind3.global.js','preset-wind4.global.js']],
    }
    for location,item in lock['packages'].items():
        if not location:
            continue
        name=location.split('node_modules/')[-1]
        version=item['version']
        filename=name.replace('@','').replace('/','__')+'-'+version+'.tgz'
        destination=output/'npm'/filename
        if not destination.exists():
            record=download(item['resolved'],destination)
        else:
            record=dict(url=item['resolved'],size=destination.stat().st_size,sha256=sha256(destination.read_bytes()).hexdigest(),modifications='none; upstream archive retained intact')
        integrity=item['integrity']
        algorithm,expected=integrity.split('-',1)
        if algorithm!='sha512' or base64.b64encode(sha512(destination.read_bytes()).digest()).decode()!=expected:
            raise ValueError('npm lock integrity mismatch: '+name)
        if not any(item['file']=='npm/'+filename for item in records['records']):
            record.update(file='npm/'+filename,component=name,version=version,lock_integrity=integrity,integrity_verified=True)
            records['records'].append(record)
        notices=[]
        with tarfile.open(destination,'r:gz') as archive:
            for member in archive.getmembers():
                path=PurePosixPath(member.name)
                if member.isfile() and path.name.lower().startswith(('license','copying','notice')):
                    if path.is_absolute() or '..' in path.parts:
                        raise ValueError('Unsafe archive notice path')
                    target=output/'npm-notices'/filename/path.as_posix()
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
                    notices.append(target.relative_to(output).as_posix())
            for original,shipped in comparisons.get(name,[]):
                content=archive.extractfile('package/'+original).read()
                actual=args.bundle.resolve()/'_internal/nicegui/static'/shipped
                match=actual.is_file() and actual.read_bytes()==content
                normalized_eol=actual.is_file() and actual.read_bytes().replace(b'\r\n',b'\n')==content.replace(b'\r\n',b'\n')
                trimmed_match=actual.is_file() and [line.rstrip() for line in actual.read_bytes().splitlines()]==[line.rstrip() for line in content.splitlines()]
                correspondence.append(dict(component=name,version=version,upstream_file=original,
                    shipped_file=actual.relative_to(args.bundle.resolve()).as_posix(),
                    upstream_sha256=sha256(content).hexdigest(),shipped=actual.is_file(),exact_bytes_match=match,normalized_eol_match=normalized_eol,trailing_whitespace_match=trimmed_match))
                if actual.is_file() and not match:
                    difference=''.join(difflib.unified_diff(content.decode().splitlines(keepends=True),actual.read_text(encoding='utf-8').splitlines(keepends=True),fromfile='npm/'+original,tofile='shipped/'+shipped))
                    (output/(shipped.replace('/','__')+'.diff')).write_text(difference,encoding='utf-8')
                    print('CORRESPONDENCE DIFFERENCE: '+shipped+'; trailing-whitespace match='+str(trimmed_match),flush=True)
        components.append(dict(name=name,version=version,lock_location=location,declared_license=item.get('license'),
            supplied_notices=notices,scope='Conservative tagged core-lock source inventory; not every dependency is necessarily embedded.'))
        write_json(output/'sources.json',records)
        print(name+'=='+version+' integrity/notices checked',flush=True)
    write_json(output/'frontend-components.json',components)
    write_json(output/'frontend-correspondence.json',dict(exact_copies=correspondence,
        compared_bundle_version=json.loads((args.bundle/'source-version.json').read_text())['id'],
        transformed=['Sass1.94.0,Immutable5.1.9,DOMPurify3.4.16 are minified by the tagged extraction script; minifier version is not locked. Quasar CSS is split/minified by that script.'],
        scope='Per-file comparison results for the named bootstrap artifact. The final artifact audit rechecks actual retained files; transformed assets require provenance review.'))
    print(f'Checked{len(components)} core-lock entries and{len(correspondence)} direct-copy asset hashes.',flush=True)


if __name__=='__main__':
    main()
