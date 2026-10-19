"""Shared strict environment and content-manifest helpers for private previews."""

from hashlib import sha256
from importlib import metadata
import json
from pathlib import Path
import re
import struct
import sys
import sysconfig

ROOT = Path(__file__).resolve().parents[1]
LOCKS = ('requirements-ui.lock', 'requirements-windows-build.lock')


def normalized(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def expected_pins(root=ROOT):
    pins = {}
    for name in LOCKS:
        for line in (root/name).read_text(encoding='utf-8').splitlines():
            if not line or line.startswith('#'):
                continue
            match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)', line)
            if not match:
                raise ValueError('Expected an exact package==version pin: '+line)
            package, version = normalized(match[1]), match[2]
            if package in pins and pins[package] != version:
                raise ValueError('Conflicting lock pin: '+package)
            pins[package] = version
    return pins


def verify_environment(root=ROOT):
    if sys.platform != 'win32' or sys.version_info[:3] != (3,14,8) or struct.calcsize('P') != 8:
        raise ValueError('Use standard CPython3.14.8 Windows x64 for this private preview.')
    if sysconfig.get_config_var('Py_GIL_DISABLED') or sys.prefix == sys.base_prefix:
        raise ValueError('Use a fresh isolated GIL-enabled venv, not the base interpreter.')
    actual = {}
    for distribution in metadata.distributions():
        name = normalized(distribution.metadata['Name'])
        if name in actual:
            raise ValueError('Duplicate installed distribution: '+name)
        actual[name] = distribution.version
    validate_inventory(actual, expected_pins(root))
    return dict(python=sys.version, architecture='x64', gil_enabled=True,
                installed=dict(sorted(actual.items())))


def validate_inventory(actual, expected):
    if actual != expected:
        raise ValueError(json.dumps(dict(missing=sorted(expected.keys()-actual.keys()),
            unexpected=sorted(actual.keys()-expected.keys()),
            wrong={name:dict(expected=expected[name],actual=actual[name]) for name in expected.keys()&actual.keys() if expected[name]!=actual[name]})))


def file_manifest(folder, exclude=()):
    return {path.relative_to(folder).as_posix():dict(size=path.stat().st_size,sha256=sha256(path.read_bytes()).hexdigest())
            for path in sorted(folder.rglob('*')) if path.is_file()
            and path.relative_to(folder).as_posix() not in exclude}


def write_json(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')


def verify_bundle(bundle):
    manifest=json.loads((bundle/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('format')!='ravel-windows-preview/1':
        raise ValueError('Unsupported preview manifest format.')
    expected=manifest['files']
    actual=file_manifest(bundle,exclude=('manifest.json',))
    if actual!=expected:
        raise ValueError(json.dumps(dict(missing=sorted(expected.keys()-actual.keys()),
            unexpected=sorted(actual.keys()-expected.keys()),
            changed=[name for name in expected.keys()&actual.keys() if expected[name]!=actual[name]])))
    return manifest
