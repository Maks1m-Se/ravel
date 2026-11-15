"""Inventory actual frontend/font/native contents; never infer complete license approval."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from windows_preview_support import verify_bundle, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    bundle=args.bundle.resolve()
    manifest=verify_bundle(bundle)
    nicegui=bundle/'_internal/nicegui'
    fonts={}
    for block in re.findall(r'@font-face\s*\{([^}]+)\}',(nicegui/'static/fonts.css').read_text()):
        family=re.search(r'font-family:\s*["\']([^"\']+)',block)
        source=re.search(r'url\(([^)]+)\)',block)
        if family and source:
            path=nicegui/'static'/source[1].strip('"\'')
            item=fonts.setdefault(path.relative_to(bundle).as_posix(),dict(families=[],sha256=sha256(path.read_bytes()).hexdigest()))
            if family[1] not in item['families']:
                item['families'].append(family[1])
    font_parser=None
    try:
        import fontTools
        from fontTools.ttLib import TTFont
        font_parser=fontTools.__version__
        for name,item in fonts.items():
            try:
                with TTFont(bundle/name) as font:
                    names={}
                    for entry in font['name'].names:
                        if entry.nameID in {0,1,2,3,4,5,8,9,13,14}:
                            value=entry.toUnicode()
                            if value not in names.setdefault(str(entry.nameID),[]):
                                names[str(entry.nameID)].append(value)
                    item['embedded_name_records']=names
            except Exception as error:
                item['metadata_error']=str(error)
    except ImportError:
        for item in fonts.values():
            item['metadata_error']='Optional fontTools/WOFF2 decoder unavailable; family only is not a license conclusion.'
    locks=[]
    for path in sorted(nicegui.rglob('package-lock.json')):
        data=json.loads(path.read_text(encoding='utf-8'))
        packages={name:{key:value[key] for key in ['version','license','resolved','integrity'] if key in value}
                  for name,value in data.get('packages',{}).items() if name}
        locks.append(dict(path=path.relative_to(bundle).as_posix(),sha256=sha256(path.read_bytes()).hexdigest(),packages=packages,
            scope='Lock contents; compiled bundle correspondence still requires evidence.'))
    javascript=[]
    for path in sorted(nicegui.rglob('*')):
        if path.is_file() and path.suffix in {'.js','.mjs','.cjs'}:
            content=path.read_text(encoding='utf-8',errors='replace')
            versions=[]
            for match in re.finditer(r'(?:dart-sass|Sass|UnoCSS|unocss|DOMPurify|Immutable|Vue|Quasar|Socket\.IO|Tailwind)[^\n]{0,85}',content):
                snippet=match[0]
                if snippet not in versions:
                    versions.append(snippet)
                if len(versions)==8:
                    break
            javascript.append(dict(path=path.relative_to(bundle).as_posix(),size=path.stat().st_size,
                sha256=sha256(path.read_bytes()).hexdigest(),header=content[:450],version_evidence=versions))
    natives=[name for name in manifest['files'] if Path(name).suffix.lower() in {'.dll','.pyd','.exe'}]
    docutils=[name for name in manifest['files'] if '/docutils/' in name and not name.startswith('notices/')]
    analysis=json.loads((bundle/'analysis-components.json').read_text())
    correspondence=[]
    comparison=bundle/'dependency-sources/frontend-correspondence.json'
    if comparison.exists():
        for item in json.loads(comparison.read_text())['exact_copies']:
            actual=bundle/item['shipped_file']
            correspondence.append(dict(component=item['component'],version=item['version'],path=item['shipped_file'],
                shipped=actual.is_file(),exact_upstream_match=actual.is_file() and sha256(actual.read_bytes()).hexdigest()==item['upstream_sha256']))
    recorded_fonts=bundle/'dependency-sources/embedded-font-records.json'
    font_hashes_match=None
    if recorded_fonts.exists():
        recorded=json.loads(recorded_fonts.read_text())['fonts']
        font_hashes_match={name:item['sha256'] for name,item in fonts.items()}=={name:item['sha256'] for name,item in recorded.items()}
    record=dict(version=manifest['version'],verified_actual_manifest=True,font_parser_version=font_parser,
        fonts=fonts,frontend_locks=locks,javascript=javascript,native_files=natives,
        docutils_loose_files=docutils,analysis_components=dict(Counter(item['component'] or 'unmapped' for item in analysis)),
        actual_frontend_correspondence=correspondence,font_hashes_match_recorded_metadata=font_hashes_match,
        scope='Actual paths/hashes and supplied evidence. Unresolved correspondence/terms require review; this inventory is not approval.')
    write_json(args.output,record)
    print(json.dumps(dict(version=record['version'],fonts=len(fonts),fonts_with_metadata=sum('embedded_name_records' in item for item in fonts.values()),
                         frontend_locks=len(locks),javascript=len(javascript),native_files=len(natives),docutils_loose_files=len(docutils)),indent=2))


if __name__=='__main__':
    main()
