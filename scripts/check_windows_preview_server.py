"""Run actual packaged UI checks on an isolated port and test console shutdown."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

from windows_preview_support import ROOT, verify_bundle, write_json


def console_event(pid, expected):
    import ctypes
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    process=kernel.OpenProcess(0x1000,False,pid)
    if not process:
        raise OSError('Owned server process is unavailable.')
    try:
        buffer=ctypes.create_unicode_buffer(32768)
        length=wintypes.DWORD(len(buffer))
        assert kernel.QueryFullProcessImageNameW(process,0,buffer,ctypes.byref(length))
        assert Path(buffer.value).resolve()==expected.resolve(),'Refuse another process.'
    finally:
        kernel.CloseHandle(process)
    kernel.FreeConsole()
    if not kernel.AttachConsole(pid):
        raise OSError(ctypes.get_last_error(),'Cannot attach to owned test console.')
    handler_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.DWORD)
    handler=handler_type(lambda event:True)
    assert kernel.SetConsoleCtrlHandler(handler,True)
    sent=bool(kernel.GenerateConsoleCtrlEvent(0,0))
    time.sleep(.5)
    kernel.FreeConsole()
    print(json.dumps(dict(ctrl_c_event_sent=sent,pid=pid)),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--port',type=int,default=8102)
    parser.add_argument('--send-console-event',type=int)
    parser.add_argument('--expected-executable',type=Path)
    parser.add_argument('--lifecycle-only',action='store_true',help='Focused start/console-shutdown diagnosis without browser cases.')
    args=parser.parse_args()
    if args.send_console_event:
        console_event(args.send_console_event,args.expected_executable)
        return
    if sys.platform!='win32' or not args.bundle or not args.output:
        parser.error('Use Windows with --bundle and a fresh --output.')
    if args.port in {8100,8101}:
        parser.error('Frozen manual-review ports must never be automated.')
    bundle=args.bundle.resolve()
    manifest=verify_bundle(bundle)
    executable=bundle/'Ravel.exe'
    for name,digest in manifest['source']['files'].items():
        if name.startswith('ravel/'):
            assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,'Local reference runtime differs: '+name
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',args.port))
    env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
             RAVEL_BROWSER_EXECUTABLE=str(executable))
    env.pop('PYTHONPATH',None)
    startup=subprocess.STARTUPINFO()
    startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow=0
    record=dict(started_utc=datetime.now(timezone.utc).isoformat(),version=manifest['version'],
        bundle=str(bundle),executable_sha256=sha256(executable.read_bytes()).hexdigest(),port=args.port)
    process=None
    try:
        with (output/'server.log').open('ab') as log:
            process=subprocess.Popen([str(executable),'ui','--port',str(args.port)],cwd=output,env=env,
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_CONSOLE,startupinfo=startup)
        record['pid']=process.pid
        url=f'http://127.0.0.1:{args.port}'
        for _ in range(80):
            if process.poll() is not None:
                raise RuntimeError('Packaged server exited; see server.log.')
            try:
                with urlopen(url+'/favicon.ico',timeout=.5) as response:
                    response.read()
                    if response.status==200:
                        break
            except OSError:
                time.sleep(.25)
        else:
            raise RuntimeError('Packaged server did not start.')
        print('Owned packaged server ready; '+('checking lifecycle only.' if args.lifecycle_only else 'running full Chrome matrix.'),flush=True)
        commands=[
            [sys.executable,str(ROOT/'scripts/check_generator_browser.py'),'--base-url',url,'--workflow','all','--channel','chrome','--output',str(output/'chrome')],
            [sys.executable,str(ROOT/'scripts/check_generator_browser.py'),'--base-url',url,'--workflow','linked','--channel','msedge','--smoke','--output',str(output/'edge')],
        ]
        for command in ([] if args.lifecycle_only else commands):
            subprocess.run(command,cwd=ROOT,env=env,check=True)
        record['lifecycle_only']=args.lifecycle_only
        if not args.lifecycle_only:
            record['chrome']=json.loads((output/'chrome/results.json').read_text())
            record['edge']=json.loads((output/'edge/results.json').read_text())
            assert len(record['chrome']['cases'])==16 and len(record['edge']['cases'])==1
        assert process.poll() is None
        print('Sending console Ctrl+C to the owned server.',flush=True)
        shutdown=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--send-console-event',str(process.pid),
                                 '--expected-executable',str(executable)],capture_output=True,text=True,check=True)
        record['console_shutdown']=json.loads(shutdown.stdout)
        process.wait(timeout=20)
        record['server_exit_code']=process.returncode
        assert process.returncode==0,'Normal console shutdown returned a failure exit code.'
        with socket.socket() as probe:
            assert probe.connect_ex(('127.0.0.1',args.port))!=0,'Server left the port open.'
        record['port_closed']=True
        assert 'Traceback (most recent call last)' not in (output/'server.log').read_text(encoding='utf-8',errors='replace'),'Server logged an unhandled traceback.'
        assert verify_bundle(bundle)==manifest
        record['result']='passed'
    except Exception as error:
        record['result']='failed'
        record['failure']=repr(error)
        raise
    finally:
        if process and process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
            record['forced_cleanup_of_owned_server']=True
        record['finished_utc']=datetime.now(timezone.utc).isoformat()
        log=(output/'server.log').read_text(encoding='utf-8',errors='replace') if (output/'server.log').exists() else ''
        record['server_traceback_count']=log.count('Traceback (most recent call last)')
        write_json(output/'results.json',record)


if __name__=='__main__':
    main()
