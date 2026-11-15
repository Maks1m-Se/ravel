"""Read-only ZIP/manifest/source-notice audit; never redistribution clearance."""
import argparse
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path,PurePosixPath
import re
import tarfile
import zipfile


def audit(archive,expected_sha256,output):
    payload=Path(archive).read_bytes()
    actual=sha256(payload).hexdigest()
    if actual!=expected_sha256:
        raise ValueError('Exact artifact SHA256 mismatch; no substitute artifact was audited.')
    output=Path(output)
    if output.exists():
        raise FileExistsError('Use a new audit output folder.')
    with zipfile.ZipFile(BytesIO(payload)) as package:
        names=package.namelist()
        if len(names)!=len(set(names)):
            raise ValueError('Duplicate ZIP member.')
        prefix='Ravel/'
        read=lambda name:package.read(prefix+name)
        load=lambda name:json.loads(read(name))
        manifest=load('manifest.json')
        if manifest['version']!='source-b99a360a14c4eb8d':
            raise ValueError('This bounded audit targets source-b99a360a14c4eb8d; no substitute version.')
        verified={}
        for name,record in manifest['files'].items():
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name:
                raise ValueError('Unsafe manifest path: '+name)
            content=read(name)
            digest=sha256(content).hexdigest()
            if digest!=record['sha256'] or len(content)!=record['size']:
                raise ValueError('Actual manifest mismatch: '+name)
            verified[name]=digest
        analysis=load('analysis-components.json')
        components=load('notices/python-components.json')
        sources=load('dependency-sources/sources.json')['records']
        for record in sources:
            if sha256(read('dependency-sources/'+record['file'])).hexdigest()!=record['sha256']:
                raise ValueError('Retained source mismatch: '+record['file'])
        copied_notices=set()
        for component in components:
            for notice in component['supplied_notices']:
                if verified.get(notice['path'])!=notice['sha256']:
                    raise ValueError('Supplied notice mismatch: '+notice['path'])
                copied_notices.add(notice['sha256'])
        labels=Counter(row.get('component') or 'unmapped' for row in analysis)
        missing_inventory=[label for label in labels if '==' in label and label not in {r['name']+'=='+r['version'] for r in components}]
        native=[]
        for name,digest in verified.items():
            if Path(name).suffix.lower() not in ('.dll','.pyd'):
                continue
            matches=[row for row in analysis if row['destination'].replace('\\','/').casefold()==name.removeprefix('_internal/').casefold()]
            native.append(dict(path=name,sha256=digest,build_origins=matches,
                               recorded_origin_hash_match=any(row['source_sha256']==digest for row in matches)))
        by_source={(row.get('component'),row.get('version')):row for row in sources if 'component' in row}
        cache={}

        def tar_members(record):
            key=record['file']
            if key not in cache:
                with tarfile.open(fileobj=BytesIO(read('dependency-sources/'+key)),mode='r:*') as source:
                    cache[key]={member.name:source.extractfile(member).read() for member in source.getmembers()
                                if member.isfile() and member.size<8_000_000}
            return cache[key]

        fonts=[]
        if prefix+'dependency-sources/embedded-font-records.json' in names:
            recorded=load('dependency-sources/embedded-font-records.json')['fonts']
            nicegui=by_source.get(('nicegui','3.18.0'))
            upstream=tar_members(nicegui) if nicegui else {}
            for name,record in recorded.items():
                archive_member='nicegui-3.18.0/'+name.removeprefix('_internal/')
                fonts.append(dict(path=name,sha256=verified.get(name),metadata_hash_match=verified.get(name)==record['sha256'],
                    retained_nicegui_sdist_match=archive_member in upstream and sha256(upstream[archive_member]).hexdigest()==verified.get(name)))
        frontend=[]
        if prefix+'dependency-sources/frontend-correspondence.json' in names:
            for record in load('dependency-sources/frontend-correspondence.json')['exact_copies']:
                name=record['shipped_file']
                origin=by_source.get((record['component'],record['version']))
                member='package/'+record['upstream_file']
                upstream=tar_members(origin) if origin else {}
                upstream_digest=sha256(upstream[member]).hexdigest() if member in upstream else None
                frontend.append(dict(component=record['component'],version=record['version'],path=name,
                    shipped=name in verified,retained_archive=origin['file'] if origin else None,
                    upstream_member=member,upstream_hash_verified=upstream_digest==record['upstream_sha256'],
                    exact_match=name in verified and verified[name]==upstream_digest))
        retained=[]
        orjson=by_source.get(('orjson','3.13.0'))
        if orjson:
            for member,content in tar_members(orjson).items():
                if '/include/cargo/' not in member or not re.match(r'(?i)^(license|notice|copying|authors|unlicense)',Path(member).name):
                    continue
                digest=sha256(content).hexdigest()
                retained.append(dict(component='orjson',version='3.13.0',source_archive=orjson['file'],
                    upstream_url=orjson['url'],source_archive_sha256=orjson['sha256'],member=member,
                    sha256=digest,present_in_shipped_notice_texts=digest in copied_notices,
                    review_copy='texts/'+digest+'.txt'))
        vendor_material=[]
        for name,version in [('pydantic-core','2.50.0'),('watchfiles','1.3.0')]:
            origin=by_source.get((name,version))
            members=tar_members(origin) if origin else {}
            vendor_material.append(dict(component=name,version=version,source_archive=origin['file'] if origin else None,
                cargo_locks=[key for key in members if key.endswith('Cargo.lock')],
                vendored_license_members=[key for key in members if ('/vendor/' in key or '/include/cargo/' in key)
                    and re.match(r'(?i)^(license|notice|copying)',Path(key).name)]))
        sbom_name='dependency-sources/CPython-3.14.8-windows-x64.spdx.json'
        sbom_files=len(load(sbom_name).get('files',[])) if prefix+sbom_name in names else None
        output.mkdir(parents=True)
        (output/'texts').mkdir()
        if orjson:
            upstream=tar_members(orjson)
            for record in retained:
                (output/record['review_copy']).write_bytes(upstream[record['member']])
        report=dict(artifact_sha256=actual,version=manifest['version'],verified_manifest_files=len(verified),
            verified_source_records=len(sources),inventory_components=len(components),actual_analysis_components=dict(labels),
            missing_inventory_labels=missing_inventory,native_files=native,fonts=fonts,frontend=frontend,
            collected_vendor_notice_records=retained,
            additional_vendor_material=vendor_material,cpython_sbom_file_entries=sbom_files,
            vendor_texts_absent_from_notice_index=len({row['sha256'] for row in retained if not row['present_in_shipped_notice_texts']}),
            gaps=['Transformed Sass/Immutable/DOMPurify minifier correspondence is not established.',
                  'NiceGUI font-byte correspondence does not establish original font-variant source/license association.',
                  'Retained orjson vendor notices are source evidence, not proof of which crates entered the compiled wheel.',
                  'Complete pydantic-core/watchfiles compiled dependency-to-vendor mapping remains unavailable; source material counts are recorded.',
                  'Microsoft runtime terms and file-level vendor association remain unresolved; SBOM file count is supporting evidence only.'],
            scope='Exact private artifact read-only audit and review-side notice collection; no binary changed, license inferred or clearance granted.')
        (output/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=audit(args.archive,args.sha256,args.output)
    print(json.dumps({key:result[key] for key in ['version','verified_manifest_files','verified_source_records','inventory_components','vendor_texts_absent_from_notice_index']},indent=2))
