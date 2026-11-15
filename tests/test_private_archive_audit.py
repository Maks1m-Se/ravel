"""Invented archive boundaries; no private executable is run or redistributed."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.audit_private_archive import audit


def fixture(folder,tamper=False,version='source-b99a360a14c4eb8d'):
    contents={'analysis-components.json':b'[]','notices/python-components.json':b'[]',
              'dependency-sources/sources.json':b'{"records":[]}', 'payload.txt':b'invented'}
    manifest=dict(version=version,files={name:dict(sha256=sha256(value).hexdigest(),size=len(value)) for name,value in contents.items()})
    path=folder/'invented.zip'
    with zipfile.ZipFile(path,'w') as package:
        for name,value in contents.items():
            package.writestr('Ravel/'+name,b'tampered' if tamper and name=='payload.txt' else value)
        package.writestr('Ravel/manifest.json',json.dumps(manifest))
    return path,sha256(path.read_bytes()).hexdigest()


class PrivateArchiveTests(unittest.TestCase):
    def test_exact_archive_and_manifest_verified_without_mutating_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);path,digest=fixture(folder)
            report=audit(path,digest,folder/'audit')
            self.assertEqual(report['verified_manifest_files'],4)
            self.assertEqual(sha256(path.read_bytes()).hexdigest(),digest)
            self.assertIn('no binary changed',report['scope'])
            with self.assertRaises(FileExistsError):
                audit(path,digest,folder/'audit')

    def test_wrong_artifact_tampering_and_substitute_version_refused_before_output(self):
        for tamper,version,expected in [(False,'source-b99a360a14c4eb8d','SHA256'),
                                        (True,'source-b99a360a14c4eb8d','manifest'),
                                        (False,'older-version','substitute')]:
            with self.subTest(expected=expected),tempfile.TemporaryDirectory() as temporary:
                folder=Path(temporary);path,digest=fixture(folder,tamper,version)
                with self.assertRaisesRegex(ValueError,expected):
                    audit(path,'0'*64 if expected=='SHA256' else digest,folder/'audit')
                self.assertFalse((folder/'audit').exists())
