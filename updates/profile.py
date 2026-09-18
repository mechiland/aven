#!/usr/bin/env python3
"""Apply Aven assets and journal the exact managed paths, excluding personal data."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from aven import atomic, digest, run, save

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('restore_profile', ROOT/'verification/restore_profile.py')
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)
FONT_NAMES = ('60-aven-families.conf', '99-aven-rendering.conf')
TREES = (
    ('preview/aven_preview', '.local/libexec/aven-preview/aven_preview'),
    ('browser/chrome', '.local/share/aven/firefox/chrome'),
    ('mail/chrome', '.local/share/aven/mail/default/chrome'),
    ('visual/wallpapers', '.local/share/wallpapers'),
    ('visual/color-schemes', '.local/share/color-schemes'),
    ('visual/union/aven-mist', '.local/share/union/styles/aven-mist'),
    ('visual/aurorae/Aven', '.local/share/aurorae/themes/Aven'),
    ('visual/plasma/aven-dock', '.local/share/plasma/desktoptheme/aven-dock'),
    ('visual/icons/Aven', '.local/share/icons/Aven'),
)
EXTRA = {
    '.local/libexec/aven-preview/aven-preview',
    '.local/share/aven/firefox/prefs.js', '.local/share/aven/firefox/.aven-profile',
    '.local/share/aven/firefox/aven-profile.json',
    '.local/share/aven/firefox/chrome/union-typography.css',
    '.local/share/aven/mail/default/prefs.js', '.local/share/aven/mail/default/aven-mail-profile.json',
    '.local/share/aven/mail/default/xulstore.json',
    '.local/share/aven/mail/default/chrome/union-typography.css',
}


def paths(home):
    result = set(restore.USER_PATHS) | EXTRA
    for source, relative in TREES:
        source = ROOT/source
        # Only the named Aven wallpaper/scheme is owned; don't collect other
        # packages from the shared color-schemes or wallpapers directories.
        result.update(str(Path(relative)/path.relative_to(source)) for path in source.rglob('*')
                      if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc')
    # Record obsolete files too so interrupted upgrades can restore them.
    for relative in ('.local/libexec/aven-preview', '.local/libexec/aven-union',
                     '.local/share/aven/firefox/chrome', '.local/share/aven/mail/default/chrome',
                     '.local/share/union/styles/aven-mist', '.local/share/aurorae/themes/Aven',
                     '.local/share/plasma/desktoptheme/aven-dock', '.local/share/icons/Aven'):
        directory = restore.checked(home, relative)
        if directory.is_symlink():
            raise ValueError(f'Refusing a symlinked Aven directory: {directory}')
        result.update(str(path.relative_to(home)) for path in directory.rglob('*')
                      if (path.is_file() or path.is_symlink()) and '__pycache__' not in path.parts)
    return result


def snapshot(home, destination):
    relatives = paths(home)
    for relative in relatives:
        target = restore.checked(home, relative)
        # The known command symlinks are installed intentionally. Asset and
        # preference symlinks could redirect a component installer elsewhere.
        if target.is_symlink() and relative not in ('.local/bin/aven-preview', '.local/bin/dolphin', '.local/bin/gwenview'):
            raise ValueError(f'Refusing a symlinked managed asset or setting: {target}')
    restore.snapshot(home, destination, relatives)
    restore.snapshot(Path('/'), destination/'system',
                     {'etc/fonts/conf.d/'+name for name in FONT_NAMES}, 'system-fonts')


def font_apply():
    for name in FONT_NAMES:
        source = ROOT/'typography/fontconfig'/name
        target = Path('/etc/fonts/conf.d')/name
        if target.is_symlink():
            raise ValueError(f'Refusing to replace symlink: {target}')
        if not target.exists() or target.read_bytes() != source.read_bytes():
            atomic(target, source.read_bytes(), 0o644)


def font_restore(destination, expected=None):
    manifest = json.loads((destination/'manifest.json').read_text())
    after = json.loads((expected/'manifest.json').read_text()) if expected else None
    for name in FONT_NAMES:
        relative = 'etc/fonts/conf.d/'+name
        original = manifest['entries'][relative]
        target = restore.checked(Path('/'), relative)
        if after and original == after['entries'][relative]:
            continue
        if after and restore.state(target) != after['entries'][relative]:
            raise ValueError(f'Font settings changed after update: {target}')
        put(target, original, destination/relative)


def put(target, entry, saved):
    if entry['kind'] == 'file':
        if digest(saved) != entry['sha256']:
            raise ValueError(f'Corrupt recovery file: {saved}')
        atomic(target, saved.read_bytes(), entry['mode'])
    elif entry['kind'] == 'absent':
        target.unlink(missing_ok=True)
    elif entry['kind'] == 'symlink':
        target.parent.mkdir(parents=True, exist_ok=True)
        target.unlink(missing_ok=True)
        target.symlink_to(entry['target'])
    else:
        raise ValueError('Unsupported snapshot entry')


def restore_snapshot(home, destination, expected=None):
    if subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'plasmashell'], stdout=subprocess.DEVNULL).returncode == 0:
        raise ValueError('Log out of Plasma first; run aven recover/rollback from a text console to avoid settings races')
    original = json.loads((destination/'manifest.json').read_text())['entries']
    after = json.loads((expected/'manifest.json').read_text())['entries'] if expected else None
    allowed = paths(home)
    # A new release may delete a formerly shipped file. Its recovery path must
    # remain valid even though it is absent from both the new source and home.
    historical_roots = (
        '.local/libexec/aven-preview/', '.local/libexec/aven-union/',
        '.local/share/aven/firefox/chrome/', '.local/share/aven/mail/default/chrome/',
        '.local/share/union/styles/aven-mist/', '.local/share/aurorae/themes/Aven/',
        '.local/share/plasma/desktoptheme/aven-dock/', '.local/share/icons/Aven/',
        '.local/share/wallpapers/AvenEstuary/',
    )
    allowed.update(relative for relative in original if relative.startswith(historical_roots))
    if not set(original) <= allowed:
        raise ValueError('Recovery snapshot contains paths outside the Aven scope')
    if after:
        original = {relative: entry for relative, entry in original.items()
                    if entry != after.get(relative, {'kind': 'absent'})}
    conflicts = []
    # Preflight the whole restore before any writes, including backup hashes.
    for relative, entry in original.items():
        target = restore.checked(home, relative)
        if after and restore.state(target) != after.get(relative, {'kind': 'absent'}):
            conflicts.append(relative)
        if entry['kind'] == 'file' and digest(destination/relative) != entry['sha256']:
            raise ValueError(f'Corrupt recovery file: {relative}')
    if conflicts:
        raise ValueError('Settings changed since the update; rollback has not modified them: ' + ', '.join(conflicts))
    arguments = ['--destination', destination/'system']
    if expected:
        arguments += ['--expected', expected/'system']
    run('sudo', sys.executable, Path(__file__), 'fonts-restore', *arguments)
    for relative, entry in original.items():
        put(restore.checked(home, relative), entry, destination/relative)
    run('fc-cache', '-f')
    run('update-desktop-database', home/'.local/share/applications')


def prune_obsolete(home, previous_source):
    """Remove deleted shipped assets only if the user has not edited them."""
    for source, relative in TREES:
        old = previous_source/source
        for path in old.rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
                continue
            suffix = path.relative_to(old)
            if (ROOT/source/suffix).exists():
                continue
            target = restore.checked(home, str(Path(relative)/suffix))
            if target.is_file() and not target.is_symlink() and target.read_bytes() == path.read_bytes():
                target.unlink()


def apply(home, style, mode, previous_source=None):
    for name in FONT_NAMES:
        target = Path('/etc/fonts/conf.d')/name
        source = ROOT/'typography/fontconfig'/name
        if target.is_symlink():
            raise ValueError(f'Refusing a symlinked font rule: {target}')
        if not target.exists() or target.read_bytes() != source.read_bytes():
            run('sudo', sys.executable, Path(__file__), 'fonts-apply')
            break
    if mode == 'install':
        run(sys.executable, ROOT/'integration/apply-profile.py', '--system-fonts-ready',
            '--style', style, '--decoration', 'aven')
    else:
        # Defaults belong to the user after installation. Never call --refresh
        # here: that resets toolbars, panel pins, density and folder preferences.
        run(sys.executable, ROOT/'files/install.py', '--assets-only')
        run(sys.executable, ROOT/'browser/install.py', '--home', home, '--update')
        run(sys.executable, ROOT/'mail/install.py', '--home', home, '--update')
        run(sys.executable, ROOT/'integration/apply.py', '--style', style, '--decoration', 'aven', '--assets-only')
        run('update-desktop-database', home/'.local/share/applications')
        run('fc-cache', '-f')
    run('kbuildsycoca6', '--noincremental')
    if previous_source:
        prune_obsolete(home, previous_source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['snapshot', 'apply', 'restore', 'fonts-apply', 'fonts-restore'])
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--expected', type=Path)
    parser.add_argument('--style', choices=['union', 'breeze'])
    parser.add_argument('--mode', choices=['install', 'update'])
    parser.add_argument('--previous-source', type=Path)
    args = parser.parse_args()
    if args.command.startswith('fonts-'):
        if os.getuid() != 0 or not Path('/run/ostree-booted').exists():
            parser.error('Font changes require sudo inside Fedora Atomic')
        if args.command == 'fonts-apply':
            font_apply()
        else:
            font_restore(args.destination, args.expected)
    elif args.command == 'snapshot':
        snapshot(Path.home(), args.destination)
    elif args.command == 'restore':
        restore_snapshot(Path.home(), args.destination, args.expected)
    else:
        apply(Path.home(), args.style, args.mode, args.previous_source)


if __name__ == '__main__':
    main()
