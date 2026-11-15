"""Retain upstream source/provenance and embedded font evidence for artifact review."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from urllib.error import HTTPError

from collect_windows_preview_sources import download
from windows_preview_support import write_json

URLS = {
    'CPython-3.14.8-windows-x64.spdx.json':'https://www.python.org/ftp/python/3.14.8/python-3.14.8-amd64.exe.spdx.json',
    'NiceGUI-3.18.0-extract_core_libraries.py.txt':'https://raw.githubusercontent.com/zauberzeug/nicegui/v3.18.0/extract_core_libraries.py',
    'NiceGUI-3.18.0-package-lock.json':'https://raw.githubusercontent.com/zauberzeug/nicegui/v3.18.0/package-lock.json',
    'Roboto-classic-OFL.txt':'https://raw.githubusercontent.com/googlefonts/roboto-classic/main/OFL.txt',
    'Material-design-icons-LICENSE.txt':'https://raw.githubusercontent.com/google/material-design-icons/master/LICENSE',
    'Material-design-icons-README.md':'https://raw.githubusercontent.com/google/material-design-icons/master/README.md',
    'Material-symbols-outlined-OFL.txt':'https://raw.githubusercontent.com/google/fonts/main/ofl/materialsymbolsoutlined/OFL.txt',
    'DOMPurify-3.4.16-LICENSE.txt':'https://raw.githubusercontent.com/cure53/DOMPurify/3.4.16/LICENSE',
    'DOMPurify-3.4.16-README.md':'https://raw.githubusercontent.com/cure53/DOMPurify/3.4.16/README.md',
}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--material',type=Path,required=True)
    parser.add_argument('--asset-audit',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    source=args.material.resolve()
    data=json.loads((source/'sources.json').read_text())
    for item in data['records']:
        path=source/item['file']
        if not path.resolve().is_relative_to(source) or sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Prepared source material changed: '+str(path))
    output=args.output.resolve()
    shutil.copytree(source,output)
    audit=json.loads(args.asset_audit.read_text(encoding='utf-8'))
    write_json(output/'embedded-font-records.json',dict(fonts=audit['fonts'],font_parser_version=audit['font_parser_version'],
        scope='Actual font hashes/name-table metadata. Upstream license files need source-correspondence review; no inference from family alone.'))
    missing=[]
    for filename,url in URLS.items():
        try:
            data['records'].append(download(url,output/filename))
            print(filename+' retrieved',flush=True)
        except HTTPError as error:
            if error.code!=404:
                raise
            missing.append(dict(file=filename,url=url,status=404))
            print(filename+' absent upstream; retained as explicit gap',flush=True)
    data['upstream_gaps']=missing
    write_json(output/'sources.json',data)


if __name__=='__main__':
    main()
