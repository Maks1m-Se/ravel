"""Prepare versioned upstream source archives and verified hashes for private review."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
from urllib.request import urlopen

from windows_preview_support import expected_pins, write_json


def download(url, destination, expected=None):
    digest=sha256()
    size=0
    with urlopen(url,timeout=60) as response, destination.open('xb') as output:
        while chunk:=response.read(1024*1024):
            size+=len(chunk)
            if size>200*1024*1024:
                raise ValueError('Source archive exceeds the200MiB review budget: '+url)
            digest.update(chunk)
            output.write(chunk)
    actual=digest.hexdigest()
    if expected and expected!=actual:
        raise ValueError('Upstream archive checksum mismatch: '+url)
    return dict(file=destination.name,url=url,sha256=actual,size=size,modifications='none; upstream archive retained intact')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    records=[]
    for name,version in sorted(expected_pins().items()):
        url=f'https://pypi.org/pypi/{name}/{version}/json'
        with urlopen(url,timeout=30) as response:
            package=json.load(response)
        candidates=[file for file in package['urls'] if file['packagetype']=='sdist']
        if not candidates:
            raise ValueError('No published corresponding source archive for '+name+'=='+version)
        selected=sorted(candidates,key=lambda item:item['filename'])[0]
        filename=selected['filename']
        if Path(filename).name!=filename:
            raise ValueError('Unexpected upstream filename')
        record=download(selected['url'],output/filename,selected['digests']['sha256'])
        record.update(component=name,version=version,metadata_url=url)
        records.append(record)
        write_json(output/'sources.json',dict(format='ravel-corresponding-source-review/1',records=records,
            scope='Pinned source archives, not a completed per-file redistribution determination.'))
        print(name+'=='+version+' source checked',flush=True)
    records.append(download('https://www.python.org/ftp/python/3.14.8/Python-3.14.8.tar.xz',output/'Python-3.14.8.tar.xz',
                            'c2215904f02b175596dc49351585104f4bc20341e1c47378b26a2c274360ce73'))
    write_json(output/'sources.json',dict(format='ravel-corresponding-source-review/1',records=records,
        scope='Pinned source archives, not a completed per-file redistribution determination.'))
    print(f'Prepared{len(records)} intact source archives with URL/hash records.',flush=True)


if __name__=='__main__':
    main()
