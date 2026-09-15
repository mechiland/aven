#!/usr/bin/env python3
"""Select the native KDE apps after their Atomic deployment has been booted.

Fedora's exported Flatpak desktop IDs precede /usr/share/applications. Keeping
both variants installed can silently launch the older Flatpak from Dolphin.
This removes only those duplicate app installations; it retains their user data.
Run identically on the stock baseline before cloning the Aven candidate.
"""
import argparse
from pathlib import Path
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    if not Path('/run/ostree-booted').exists():
        p.error('Run inside the Fedora Atomic guest')
    duplicates = []
    for package, app in [('gwenview','org.kde.gwenview'), ('okular','org.kde.okular')]:
        subprocess.run(['rpm','-q',package], check=True)
        if not Path(f'/usr/share/applications/{app}.desktop').is_file():
            raise SystemExit(f'Native desktop entry missing: {app}')
        for scope in ['--system','--user']:
            result = subprocess.run(['flatpak','info',scope,app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                duplicates.append((scope,app))
    print('Duplicate Flatpak apps:', duplicates)
    if args.apply:
        for scope, app in duplicates:
            command = ['flatpak','uninstall',scope,'--noninteractive',app]
            if scope == '--system':
                command.insert(0,'sudo')
            subprocess.run(command, check=True)
        subprocess.run(['kbuildsycoca6','--noincremental'], check=True)


if __name__ == '__main__': main()
