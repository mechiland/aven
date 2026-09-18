#!/usr/bin/env python3
"""Integrate the focused Aven candidate after stock captures and package reboot."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]

def run(*args):
    subprocess.run([str(x) for x in args],check=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decoration',choices=['breeze','aven'],default='aven')
    p.add_argument('--system-fonts-ready',action='store_true',help='Verify fontconfig installed by the ISO; do not invoke sudo')
    p.add_argument('--without-shell-reload',action='store_true',help='Seed before Plasma starts; apply the panel after shell startup')
    p.add_argument('--style', choices=['breeze', 'union'], default='breeze')
    p.add_argument('--refresh', action='store_true', help='Refresh managed app appearance and layout; retain accounts and user data')
    a=p.parse_args()
    if os.getuid()==0 or not Path('/run/ostree-booted').exists():
        p.error('Run as the desktop user inside the Aven Atomic guest')
    # Every app must be closed so native settings do not overwrite installation.
    for name in ['dolphin','gwenview','firefox','thunderbird']:
        if subprocess.run(['pgrep','-u',str(os.getuid()),'-x',name],stdout=subprocess.DEVNULL).returncode==0:
            p.error(f'Close {name} before applying the Aven profile')
    run(sys.executable,ROOT/'verification/restore_profile.py','snapshot','--home',Path.home())
    backup = Path.home()/'.local/state/aven'/('profile-defaults-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True)
    saved, absent, hashes = [], [], {}
    for name in ['.config/mimeapps.list', '.config/kde-mimeapps.list', '.local/share/applications/mimeapps.list']:
        src = Path.home()/name
        if src.exists():
            dst = backup/name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src,dst)
            saved.append(name)
            hashes[name] = hashlib.sha256(dst.read_bytes()).hexdigest()
        else:
            absent.append(name)
    (backup/'manifest.json').write_text(json.dumps({'backed_up':saved,'absent':absent,'sha256':hashes,'scope':'profile-defaults','profile':'Aven Mist v1'},indent=2))
    if a.system_fonts_ready:
        for source in sorted((ROOT/'typography/fontconfig').glob('*.conf')):
            target = Path('/etc/fonts/conf.d')/source.name
            if not target.is_file() or target.read_bytes() != source.read_bytes():
                raise RuntimeError(f'ISO font configuration missing or changed: {target}')
    else:
        run('sudo',sys.executable,ROOT/'typography/install.py','--root','/')
    run('fc-cache','-f')
    run(sys.executable,ROOT/'typography/audit.py','--active')
    refresh = ['--refresh'] if a.refresh else []
    run(sys.executable,ROOT/'files/install.py',*(['--refresh-layout'] if a.refresh else []))
    run(sys.executable,ROOT/'browser/install.py','--home',Path.home(),*refresh)
    run(sys.executable,ROOT/'mail/install.py','--home',Path.home(),*refresh)
    run(sys.executable,ROOT/'photos/install.py','--home',Path.home(),*refresh)
    run('update-desktop-database',Path.home()/'.local/share/applications')
    # Fedora's xdg-settings KDE path still invokes unversioned qtpaths.
    # GIO writes the standard user MIME associations without that legacy shim.
    from gi.repository import Gio
    for desktop,mimes in {
        'org.mozilla.firefox.desktop':['x-scheme-handler/http','x-scheme-handler/https','text/html'],
        'net.thunderbird.Thunderbird.desktop':['x-scheme-handler/mailto','message/rfc822'],
        'org.kde.gwenview.desktop':['image/jpeg','image/png','image/webp','image/avif','image/tiff'],
        'org.kde.okular.desktop':['application/pdf'],
        'org.kde.dolphin.desktop':['inode/directory']}.items():
        app = Gio.DesktopAppInfo.new(desktop)
        if app is None:
            raise RuntimeError(f'Desktop entry unavailable: {desktop}')
        for mime in mimes:
            if not app.set_as_default_for_type(mime):
                raise RuntimeError(f'Cannot associate {mime} with {desktop}')
            actual = Gio.AppInfo.get_default_for_type(mime, False)
            if actual is None or actual.get_id() != desktop:
                raise RuntimeError(f'Association did not persist: {mime}')
    options = ['--without-shell-reload'] if a.without_shell_reload else []
    run(sys.executable,ROOT/'integration/apply.py','--decoration',a.decoration,'--style',a.style,*options)
    print('Profile integrated. Reboot the guest for a clean comparison round.')

if __name__=='__main__':main()
