#!/usr/bin/python3
"""Seed Aven once per user before Plasma, then configure its native panel."""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
STATE = Path.home() / '.local/state/aven'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['seed', 'layout'])
    args = parser.parse_args()
    if os.getuid() == 0 or not Path('/run/ostree-booted').exists():
        parser.error('Only a desktop user on the installed Atomic system may run this')
    STATE.mkdir(parents=True, exist_ok=True)
    marker = STATE / f'iso-{args.phase}-v1.json'
    with (STATE / 'iso-first-login.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if marker.exists():
            return
        with (STATE / f'iso-{args.phase}.log').open('a') as log:
            if args.phase == 'seed':
                env = os.environ | {'QT_QPA_PLATFORM': 'offscreen'}
                subprocess.run([sys.executable, str(ROOT / 'integration/apply-profile.py'),
                                '--system-fonts-ready', '--without-shell-reload', '--decoration', 'aven'],
                               env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            else:
                if not (STATE / 'iso-seed-v1.json').exists():
                    raise RuntimeError('Pre-session profile seed failed; inspect iso-seed.log')
                dbus = shutil.which('qdbus6') or shutil.which('qdbus-qt6') or shutil.which('qdbus')
                if not dbus:
                    raise RuntimeError('Qt D-Bus client is required')
                for attempt in range(30):
                    probe = subprocess.run([dbus, 'org.kde.plasmashell', '/PlasmaShell'],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if probe.returncode == 0:
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError('Plasma did not become ready')
                wallpaper = Path.home() / '.local/share/wallpapers/AvenEstuary/contents/images/3840x2160.svg'
                script = (ROOT / 'integration/plasma-layout.js.in').read_text().replace('@WALLPAPER@', wallpaper.as_uri())
                subprocess.run([dbus, 'org.kde.plasmashell', '/PlasmaShell',
                                'org.kde.PlasmaShell.evaluateScript', script], stdout=log, stderr=subprocess.STDOUT, check=True)
                subprocess.run([dbus, 'org.kde.KWin', '/KWin', 'reconfigure'],
                               stdout=log, stderr=subprocess.STDOUT, check=True)
            marker.write_text(json.dumps({'schema_version': 1, 'phase': args.phase,
                                         'completed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                         'source': str(ROOT), 'home': str(Path.home())}, indent=2) + '\n')


if __name__ == '__main__':
    main()
