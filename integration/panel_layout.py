#!/usr/bin/env python3
"""Apply the native Aven panel layout to an existing Fedora Atomic session."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def apply_layout(dbus, style, wallpaper, *, stdout=None, stderr=None):
    def call(*args):
        return subprocess.run([dbus, *args], check=True, text=True,
                              stdout=stdout, stderr=stderr)

    if style == 'union':
        manager = ['org.kde.KWin', '/VirtualDesktopManager']
        interface = 'org.kde.KWin.VirtualDesktopManager'
        count = int(subprocess.check_output(
            [dbus, *manager, f'{interface}.count'], text=True).strip())
        # Make the pager useful on a fresh one-desktop profile. Retain all
        # existing desktop IDs, names and windows on repeat applications.
        if count < 2:
            call(*manager, f'{interface}.createDesktop', str(count), '')
    script = (ROOT / 'integration/plasma-layout.js.in').read_text()
    script = script.replace('@WALLPAPER@', wallpaper.as_uri()).replace(
        '@UNION_DOCK@', 'true' if style == 'union' else 'false')
    call('org.kde.plasmashell', '/PlasmaShell',
         'org.kde.PlasmaShell.evaluateScript', script)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--style', choices=['breeze', 'union'], default='union')
    args = parser.parse_args()
    if os.getuid() == 0 or not Path('/run/ostree-booted').exists():
        parser.error('Run as the desktop user inside the Aven Atomic guest')
    dbus = shutil.which('qdbus6') or shutil.which('qdbus-qt6') or shutil.which('qdbus')
    if not dbus:
        parser.error('Qt D-Bus client is required')
    subprocess.run([sys.executable, str(ROOT / 'verification/restore_profile.py'),
                    'snapshot', '--home', str(Path.home())], check=True)
    apply_layout(dbus, args.style, Path.home() /
                 '.local/share/wallpapers/AvenEstuary/contents/images/3840x2160.svg')


if __name__ == '__main__':
    main()
