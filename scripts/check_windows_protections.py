"""Record actual Windows protection state and run the official native custom scan."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from windows_preview_support import verify_bundle, write_json

STATUS = r'''
$ErrorActionPreference='Stop'
$bundle=$env:RAVEL_VERIFY_BUNDLE
$signature=Get-AuthenticodeSignature -LiteralPath (Join-Path $bundle 'Ravel.exe')
$status=Get-MpComputerStatus | Select-Object AMProductVersion,AMEngineVersion,AntivirusSignatureVersion,AntivirusSignatureLastUpdated,AntivirusEnabled,RealTimeProtectionEnabled,SmartAppControlState
$os=Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture
$windows=Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' | Select-Object DisplayVersion,EditionID,UBR
$native=Get-ChildItem -LiteralPath (Join-Path $bundle '_internal') -Recurse -File | Where-Object { $_.Extension -in '.dll','.pyd' } | ForEach-Object { [ordered]@{file=$_.FullName.Substring($bundle.Length+1);file_version=$_.VersionInfo.FileVersion;product_version=$_.VersionInfo.ProductVersion;company=$_.VersionInfo.CompanyName} }
[ordered]@{defender=$status;os=$os;windows=$windows;signature_status=$signature.Status.ToString();execution_policy=(Get-ExecutionPolicy);native_versions=@($native)} | ConvertTo-Json -Depth 6 -Compress
'''

DETECTIONS = r'''
$ErrorActionPreference='Stop'
$bundle=$env:RAVEL_VERIFY_BUNDLE
$items=@(Get-MpThreatDetection | Where-Object { ($_.Resources -join ' ').IndexOf($bundle,[StringComparison]::OrdinalIgnoreCase) -ge 0 } | Select-Object ThreatID,InitialDetectionTime,LastThreatStatusChangeTime,ActionSuccess,Resources)
[ordered]@{candidate_detection_count=$items.Count;candidate_detections=$items} | ConvertTo-Json -Depth 6 -Compress
'''


def query(script,env):
    # Static read-only commands; the path is data in a task-specific environment variable.
    result=subprocess.run(['powershell','-NoProfile','-Command',script],env=env,capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout.lstrip('\ufeff'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if sys.platform!='win32':
        parser.error('Use the Windows candidate host.')
    bundle=args.bundle.resolve()
    output=args.output.resolve()
    if output.exists():
        parser.error('Choose a fresh report path to preserve prior evidence.')
    manifest=verify_bundle(bundle)
    executable=bundle/'Ravel.exe'
    env=dict(os.environ,RAVEL_VERIFY_BUNDLE=str(bundle))
    record=dict(started_utc=datetime.now(timezone.utc).isoformat(),version=manifest['version'],bundle=str(bundle),
        executable_sha256=sha256(executable.read_bytes()).hexdigest(),settings_changed=False,
        smartscreen='Local unsigned launch tested separately; a real downloaded-file reputation prompt is not tested.',
        scan_documentation='https://learn.microsoft.com/en-us/defender-endpoint/command-line-arguments-microsoft-defender-antivirus')
    try:
        record['before']=query(STATUS,env)
        platform=Path(os.environ['ProgramData'])/'Microsoft/Windows Defender/Platform'
        candidates=[path for path in platform.glob('*/MpCmdRun.exe') if re.fullmatch(r'[\d.]+-\d+',path.parent.name)]
        candidates.sort(key=lambda path:tuple(map(int,re.findall(r'\d+',path.parent.name))))
        scanner=candidates[-1] if candidates else Path(os.environ['ProgramFiles'])/'Windows Defender/MpCmdRun.exe'
        command=[str(scanner),'-Scan','-ScanType','3','-File',str(bundle)]
        record['scan_command']=command
        print('Running native Defender custom scan of '+manifest['version'],flush=True)
        scan=subprocess.run(command,env=env,capture_output=True,text=True)
        record['scan_exit_code']=scan.returncode
        record['scan_stdout']=scan.stdout
        record['scan_stderr']=scan.stderr
        record['scan_completed_utc']=datetime.now(timezone.utc).isoformat()
        record['after']=query(STATUS,env)
        record.update(query(DETECTIONS,env))
        record['manifest_unchanged']=verify_bundle(bundle)==manifest
        # Exit0 can also mean successful remediation; inspect detection history and actual file preservation.
        record['result']='passed' if scan.returncode==0 and record['candidate_detection_count']==0 and record['manifest_unchanged'] else 'review-required'
    except Exception as error:
        record['result']='incomplete'
        record['error']=repr(error)
        raise
    finally:
        record['finished_utc']=datetime.now(timezone.utc).isoformat()
        write_json(output,record)
        print(json.dumps({key:record[key] for key in ['version','result','scan_exit_code','candidate_detection_count','manifest_unchanged'] if key in record}),flush=True)


if __name__=='__main__':
    main()
