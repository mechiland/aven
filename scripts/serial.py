#!/usr/bin/env python3
"""Send a command to the VM installation/recovery console and read its response."""
import argparse
from pathlib import Path
import socket
import time
import sys
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--socket',default='install-console.sock')
p.add_argument('--wait',type=float,default=2)
p.add_argument('command')
a=p.parse_args()
with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
    s.connect(str(ROOT/'.cache/vm'/a.socket))
    s.sendall(a.command.encode()+b'\n')
    s.settimeout(a.wait)
    while True:
        try:
            data=s.recv(65536)
            if not data:break
            sys.stdout.write(data.decode(errors='replace'));sys.stdout.flush()
        except TimeoutError:break
