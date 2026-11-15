"""Console entry for the current application, not the historical workbook."""

import json
import multiprocessing
from pathlib import Path
import sys

from ravel.__main__ import main


if __name__=='__main__':
    multiprocessing.freeze_support()
    if sys.platform=='win32':
        import ctypes
        # A process group may inherit Ctrl+C-ignore from its launcher.
        ctypes.windll.kernel32.SetConsoleCtrlHandler(None,False)
    if sys.argv[1:]==['--runtime-info']:
        import ravel
        print(json.dumps(dict(frozen=bool(getattr(sys,'frozen',False)),python=sys.version,
            executable=sys.executable,root=str(Path(ravel.__file__).resolve().parents[1]),
            import_paths=sys.path)),flush=True)
    else:
        raise SystemExit(main(sys.argv[1:] or ['ui']))
