"""Build and stage a private current-app Windows folder/ZIP with actual manifests."""

import argparse
import ast
from hashlib import sha256
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from windows_preview_support import ROOT, LOCKS, file_manifest, normalized, verify_environment, write_json

INPUTS = ('ravel', 'brand/svg', 'brand/favicon', 'examples',
          'experiments/workbook/workbook.css', 'LICENSE', *LOCKS,
          'scripts/windows_preview_entry.py', 'scripts/windows_preview_support.py',
          'scripts/build_windows_preview.py', 'docs/third-party-notices.txt',
          'docs/dependency-licenses.md',
          'scripts/prepare_windows_preview_environment.py', 'scripts/collect_windows_preview_sources.py',
          'scripts/enrich_windows_preview_sources.py',
          'scripts/collect_windows_frontend_sources.py',
          'scripts/windows_hooks',
          'scripts/check_windows_preview.py', 'scripts/compare_windows_previews.py', 'scripts/audit_windows_preview.py',
          'scripts/check_windows_preview_server.py',
          'requirements-license-review.lock', 'docs/windows-preview.md', 'docs/windows-preview-notices.md')

# Ravel does not use these lazy optional elements. Keep their libraries out of
# the private candidate and verify the actual narrowed artifact in the browser.
OPTIONAL_ELEMENT_DATA = frozenset({'aggrid','codemirror','echart','joystick','json_editor',
    'leaflet','mermaid','plotly','scene','sortable','xterm'})
NONPROD_CORE_DATA = frozenset({'vue.esm-browser.js','quasar.umd.js'})


def build_inputs():
    files = {}
    for name in INPUTS:
        path = ROOT/name
        if not path.exists():
            raise FileNotFoundError('Missing declared build input: '+name)
        candidates = path.rglob('*') if path.is_dir() else [path]
        for source in candidates:
            if source.is_file() and '__pycache__' not in source.parts:
                files[source.relative_to(ROOT).as_posix()] = source.read_bytes()
    return dict(sorted(files.items()))


def source_record(files):
    hashes = {name:sha256(content).hexdigest() for name,content in files.items()}
    digest = sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    git = ['git','-c','safe.directory='+ROOT.as_posix(),'-C',str(ROOT)]
    try:
        head = subprocess.check_output(git+['rev-parse','HEAD'],stderr=subprocess.DEVNULL,text=True).strip()
        dirty = bool(subprocess.check_output(git+['status','--porcelain'],stderr=subprocess.DEVNULL))
    except (subprocess.CalledProcessError, FileNotFoundError):
        head,dirty = None,None
    return dict(id='source-'+digest[:16],sha256=digest,files=hashes,git_head=head,git_dirty=dirty)


def collect_notices(bundle):
    records = []
    for dist in sorted(metadata.distributions(),key=lambda item:normalized(item.metadata['Name'])):
        name,version = normalized(dist.metadata['Name']),dist.version
        copied = []
        for path in dist.files or []:
            basename=path.name.lower()
            named_notice=basename.startswith(('license','copying','notice')) or basename=='authors'
            license_text='licenses' in [part.lower() for part in path.parts] and Path(basename).suffix in {'','.txt','.rst','.md','.html','.adoc'}
            if '__pycache__' in path.parts or Path(basename).suffix in {'.py','.pyc','.pyd','.so'} or not (named_notice or license_text):
                continue
            source = Path(dist.locate_file(path))
            if not source.is_file():
                continue
            content=source.read_bytes()
            digest=sha256(content).hexdigest()
            destination=bundle/'notices/texts'/(digest[:24]+'.txt')
            assert destination.resolve().is_relative_to((bundle/'notices/texts').resolve())
            destination.parent.mkdir(parents=True,exist_ok=True)
            if destination.exists():
                if destination.read_bytes()!=content:
                    raise ValueError('Notice content-address collision.')
            else:
                destination.write_bytes(content)
            copied.append(dict(path=destination.relative_to(bundle).as_posix(),
                source_path=path.as_posix(),sha256=digest))
        records.append(dict(name=name,version=version,
            license_expression=dist.metadata.get('License-Expression') or dist.metadata.get('License'),
            supplied_notices=copied,source_index=f'https://pypi.org/project/{name}/{version}/',
            scope='Installed build environment; actual collected modules are listed separately.'))
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    destination=bundle/'notices/CPython-3.14.8-LICENSE.txt'
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(python_license,destination)
    write_json(bundle/'notices/python-components.json',records)


def analysis_inventory(output):
    owners={}
    for dist in metadata.distributions():
        name=normalized(dist.metadata['Name'])+'=='+dist.version
        for path in dist.files or []:
            owners[str(Path(dist.locate_file(path)).resolve()).casefold()]=name
    entries=[]
    def walk(value):
        if isinstance(value,(list,tuple)):
            if len(value)==3 and isinstance(value[0],str) and isinstance(value[1],str) and value[2] in {'PYMODULE','PYSOURCE','BINARY','EXTENSION','DATA'}:
                destination=value[0].replace('\\','/')
                if destination=='base_library.zip' or (destination.endswith('/RECORD') and '.dist-info/' in destination):
                    return
                source=Path(value[1])
                if source.is_file():
                    resolved=source.resolve()
                    owner=owners.get(str(resolved).casefold())
                    if resolved.is_relative_to(ROOT):
                        origin='ravel-source/'+resolved.relative_to(ROOT).as_posix()
                        owner='Ravel'
                    elif resolved.is_relative_to(output/'nicegui-data'):
                        origin='nicegui-staged-data/'+resolved.relative_to(output/'nicegui-data').as_posix()
                        owner='nicegui==3.18.0'
                    elif resolved.is_relative_to(Path(sys.base_prefix)):
                        origin='python-runtime/'+resolved.relative_to(Path(sys.base_prefix)).as_posix()
                        owner=owner or 'CPython3.14.8/native-vendor-review'
                    elif resolved.is_relative_to(Path(sys.prefix)):
                        origin='build-environment/'+resolved.relative_to(Path(sys.prefix)).as_posix()
                    else:
                        origin='external-native/'+source.name
                    entries.append(dict(destination=value[0],kind=value[2],origin=origin,component=owner,
                                        source_sha256=sha256(source.read_bytes()).hexdigest()))
            else:
                for item in value:
                    walk(item)
    for path in sorted((output/'work').rglob('*-00.toc')):
        if path.name in {'Analysis-00.toc','PYZ-00.toc'}:
            walk(ast.literal_eval(path.read_text(encoding='utf-8')))
    # Exact input records are useful even where many bytecode modules share PYZ.
    unique={json.dumps(entry,sort_keys=True):entry for entry in entries}
    return [unique[key] for key in sorted(unique)]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='Fresh build/staging folder; never overwritten.')
    parser.add_argument('--source-material',type=Path,help='Prepared corresponding-source archives/URL+hash record.')
    args=parser.parse_args()
    environment=verify_environment()
    files=build_inputs()
    version=source_record(files)
    output=args.output.resolve()
    if output.exists():
        parser.error('Use a new output folder to preserve build evidence.')
    output.mkdir(parents=True)
    (output/'spec').mkdir()
    env=dict(os.environ,PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',
             PYINSTALLER_CONFIG_DIR=str(output/'cache'),PYTHONHASHSEED='0')
    env.pop('PYTHONPATH',None)
    command=[sys.executable,'-I','-m','PyInstaller','--onedir','--noupx','--name','Ravel',
        '--paths',str(ROOT),'--distpath',str(output/'dist'),'--workpath',str(output/'work'),
        '--additional-hooks-dir',str(ROOT/'scripts/windows_hooks'),
        '--specpath',str(output/'spec'),'--icon',str(ROOT/'brand/favicon/favicon.ico')]
    import nicegui
    nicegui_root=Path(nicegui.__file__).parent
    staged_nicegui=output/'nicegui-data'
    def unused_data(directory,names):
        relative=Path(directory).relative_to(nicegui_root)
        return [name for name in names if name=='__pycache__' or
                (relative==Path('static') and name in NONPROD_CORE_DATA) or
                (relative==Path('elements') and Path(name).stem in OPTIONAL_ELEMENT_DATA)]
    shutil.copytree(nicegui_root,staged_nicegui,ignore=unused_data)
    data=[(staged_nicegui,'nicegui'),(ROOT/'ravel/static','ravel/static'),
          (ROOT/'examples','examples'),(ROOT/'brand/svg','brand/svg'),(ROOT/'brand/favicon','brand/favicon'),
          (ROOT/'experiments/workbook/workbook.css','experiments/workbook')]
    for source,destination in data:
        command.extend(['--add-data',str(source)+os.pathsep+destination])
    for line in (ROOT/'requirements-ui.lock').read_text().splitlines():
        if line and not line.startswith('#'):
            command.extend(['--copy-metadata',line.split('==')[0]])
    command.append(str(ROOT/'scripts/windows_preview_entry.py'))
    write_json(output/'build-environment.json',environment)
    write_json(output/'source-version.json',version)
    print('Building '+version['id']+'; see '+str(output/'build.log'),flush=True)
    with (output/'build.log').open('w',encoding='utf-8') as log:
        subprocess.run(command,cwd=output,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    if build_inputs()!=files:
        raise RuntimeError('Declared source inputs changed during the build; preserve and rebuild from a fixed snapshot.')
    bundle=output/'dist/Ravel'
    unexpected_optional=[path.name for path in (bundle/'_internal/nicegui/elements').iterdir()
                         if path.stem in OPTIONAL_ELEMENT_DATA]
    if unexpected_optional:
        raise RuntimeError('Excluded optional element data was recollected: '+str(unexpected_optional))
    if any((bundle/'_internal/nicegui/static'/name).exists() for name in NONPROD_CORE_DATA):
        raise RuntimeError('Unused nonproduction core data was recollected.')
    removed_install_records=[]
    for path in (bundle/'_internal').rglob('RECORD'):
        if path.parent.name.endswith('.dist-info'):
            assert path.resolve().is_relative_to(bundle.resolve())
            removed_install_records.append(path.relative_to(bundle).as_posix())
            path.unlink()
    for required in ['Ravel.exe','_internal/ravel/static/generator.css',
                     '_internal/examples/linked/devices-measurements.recipe.json',
                     '_internal/experiments/workbook/workbook.css','_internal/brand/favicon/favicon.ico']:
        if not (bundle/required).is_file():
            raise RuntimeError('Incomplete bundle: '+required)
    shutil.copyfile(ROOT/'LICENSE',bundle/'LICENSE')
    shutil.copyfile(ROOT/'docs/third-party-notices.txt',bundle/'THIRD-PARTY-NOTICES.txt')
    shutil.copyfile(ROOT/'docs/windows-preview.md',bundle/'README.md')
    shutil.copyfile(ROOT/'docs/windows-preview-notices.md',bundle/'NOTICES-REVIEW.md')
    shutil.copyfile(ROOT/'docs/dependency-licenses.md',bundle/'dependency-licenses.md')
    collect_notices(bundle)
    write_json(bundle/'analysis-components.json',analysis_inventory(output))
    write_json(bundle/'omitted-assets.json',dict(optional_element_data=sorted(OPTIONAL_ELEMENT_DATA),
        nonproduction_core_data=sorted(NONPROD_CORE_DATA),
        environment_installation_records=sorted(removed_install_records),
        reason='Unused lazy element libraries; actual narrowed-artifact regression checks required.'))
    write_json(bundle/'build-environment.json',environment)
    write_json(bundle/'source-version.json',version)
    with zipfile.ZipFile(bundle/'ravel-corresponding-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name,content in files.items():
            archive.writestr(name,content)
    if args.source_material:
        material=args.source_material.resolve()
        if not material.is_dir() or not (material/'sources.json').is_file():
            raise ValueError('Source material must contain the prepared sources.json URL/hash record.')
        for item in json.loads((material/'sources.json').read_text())['records']:
            source=(material/item['file']).resolve()
            if not source.is_relative_to(material) or sha256(source.read_bytes()).hexdigest()!=item['sha256']:
                raise ValueError('Corresponding-source material changed: '+item['file'])
        shutil.copytree(material,bundle/'dependency-sources',ignore=shutil.ignore_patterns('sources.previous*.json'))
    write_json(bundle/'manifest.json',dict(format='ravel-windows-preview/1',version=version['id'],
        source=version,environment=environment,files=file_manifest(bundle,exclude=('manifest.json',)),
        status='private-unaccepted-preview',redistribution='Pending artifact-specific findings in NOTICES-REVIEW.md; no public distribution.'))
    archive=output/('Ravel-'+version['id']+'-windows-x64-private.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as package:
        for path in sorted(bundle.rglob('*')):
            if path.is_file():
                package.write(path,'Ravel/'+path.relative_to(bundle).as_posix())
    digest=sha256(archive.read_bytes()).hexdigest()
    (output/'SHA256SUMS.txt').write_text(digest+'  '+archive.name+'\n',encoding='utf-8')
    print(json.dumps(dict(bundle=str(bundle),zip=str(archive),sha256=digest,version=version['id']),indent=2),flush=True)


if __name__=='__main__':
    main()
