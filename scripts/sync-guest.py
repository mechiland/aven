#!/usr/bin/env python3
"""Copy only this prototype's source/fixtures to the isolated guest over SSH."""
import argparse
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
VM=ROOT/'.cache/vm'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--guest',choices=['stock','aven'],default='stock')
    a=p.parse_args()
    ssh=['ssh','-i',str(VM/'id_ed25519'),'-p','2222' if a.guest=='stock' else '2223',
         '-o','BatchMode=yes','-o','StrictHostKeyChecking=accept-new','-o',f'UserKnownHostsFile={VM/"known_hosts"}', 'aven@127.0.0.1']
    folders=['typography','visual','files','preview','browser','mail','photos','fixtures','integration','scripts','verification']
    sources=[x for x in folders if (ROOT/x).exists()]
    pack=subprocess.Popen(['tar','--exclude=__pycache__','--exclude=*.pyc','-czf','-',*sources],cwd=ROOT,stdout=subprocess.PIPE)
    send=subprocess.run(ssh+['mkdir -p ~/aven && tar -xzf - -C ~/aven'],stdin=pack.stdout)
    pack.stdout.close()
    if pack.wait() or send.returncode:raise SystemExit('Source transfer failed')
    print(f'Copied source and fixtures to {a.guest}:~/aven (no profiles applied).')

if __name__=='__main__':main()
