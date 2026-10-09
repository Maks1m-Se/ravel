"""Run the workbook with a process-local non-loopback socket/DNS guard."""

import argparse
import ipaddress
import json
from pathlib import Path
import runpy
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/workbook-repair/server-network.json')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    attempts = []
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_sendto = socket.socket.sendto
    original_dns = socket.getaddrinfo

    def check(address):
        if isinstance(address, tuple):
            host = address[0]
            try:
                allowed = ipaddress.ip_address(host).is_loopback
            except ValueError:
                allowed = host == 'localhost'
            if not allowed:
                attempts.append(str(address))
                args.output.write_text(json.dumps(attempts), encoding='utf-8')
                raise OSError('Review blocks non-loopback destinations')

    def connect(self, address):
        check(address)
        return original_connect(self, address)

    def connect_ex(self, address):
        check(address)
        return original_connect_ex(self, address)

    def sendto(self, data, *args):
        check(args[-1])
        return original_sendto(self, data, *args)

    def dns(host, *args, **kwargs):
        check((host, 0))
        return original_dns(host, *args, **kwargs)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.socket.sendto = sendto
    socket.getaddrinfo = dns
    args.output.write_text('[]', encoding='utf-8')
    runpy.run_module('experiments.workbook.app', run_name='__main__')


if __name__ == '__main__':
    main()
