#!/usr/bin/env python3
"""Layer required native packages through rpm-ostree, preserving Atomic updates."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--install',action='store_true',help='Create an rpm-ostree deployment; reboot before applying profiles')
    p.add_argument('--upgrade',action='store_true',help='Update to current stable Fedora and layer missing packages in one deployment')
    a=p.parse_args()
    if not Path('/run/ostree-booted').exists():p.error('Run inside the Fedora Atomic guest')
    packages={'firefox','thunderbird','gwenview','okular','glibc-langpack-zh','kde-gtk-config','qt6-qttools'}
    packages.update(json.loads((ROOT/'files/integration.json').read_text())['runtime_packages'])
    for manifest in ['typography/fedora-packages.txt','photos/fedora-packages.txt']:
        packages.update(line.strip() for line in (ROOT/manifest).read_text().splitlines() if line.strip() and not line.startswith('#'))
    missing=[]
    installed=[]
    for package in sorted(packages):
        r=subprocess.run(['rpm','-q',package],capture_output=True,text=True)
        if r.returncode:missing.append(package)
        else:installed.append(r.stdout.strip())
    print(json.dumps({'installed':installed,'to_layer':missing},indent=2),flush=True)
    if a.upgrade:
        subprocess.run(['sudo','rpm-ostree','upgrade',*[f'--install={package}' for package in missing]],check=True)
        print('Current stable Atomic deployment staged. Reboot before taking the matched stock baseline.')
    elif a.install and missing:
        subprocess.run(['sudo','rpm-ostree','install','-y',*missing],check=True)
        print('A new Atomic deployment is staged. Reboot before applying Aven preferences.')

if __name__=='__main__':main()
