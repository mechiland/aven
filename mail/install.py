#!/usr/bin/env python3
"""Install normal online Aven mail without touching existing Thunderbird profiles."""
from __future__ import annotations
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import shlex
import tempfile

from profile import MARKER, create, refresh

LAUNCHER_MARKER = '# Aven managed mail launcher v1'
DESKTOP_MARKER = 'X-Aven-Managed=mail-v1'


def atomic_write(path: Path, text: str, mode: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(text)
    temporary.chmod(mode)
    temporary.replace(path)


def desktop_quote(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'


def require_owned_or_new(path: Path, marker: str):
    if path.is_symlink():
        raise SystemExit(f'Refusing to replace symlink: {path}')
    if path.exists() and (not path.is_file() or marker not in path.read_text(encoding='utf-8')):
        raise SystemExit(f'Refusing to replace unmarked file: {path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, required=True, help='Explicit guest user home, owned by current user')
    parser.add_argument('--refresh', action='store_true', help='Refresh appearance in the closed managed profile, preserving accounts and mail')
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    if not home.is_dir() or home.stat().st_uid != os.getuid():
        parser.error('--home must be an existing directory owned by the current user')
    profile = home / '.local/share/aven/mail/default'
    launcher = home / '.local/bin/aven-mail'
    desktop = home / '.local/share/applications/net.thunderbird.Thunderbird.desktop'
    require_owned_or_new(launcher, LAUNCHER_MARKER)
    require_owned_or_new(desktop, DESKTOP_MARKER)
    if profile.is_symlink():
        parser.error('Refusing to adopt a symlink as the Aven mail profile')
    seeded = not profile.exists()
    if not seeded:
        marker_path = profile / MARKER
        if not marker_path.is_file() or marker_path.is_symlink():
            parser.error(f'Refusing to adopt existing unmarked profile: {profile}')
        try:
            marker = json.loads(marker_path.read_text(encoding='utf-8'))
        except (OSError, ValueError) as error:
            parser.error(f'Invalid Aven mail profile marker: {error}')
        if marker.get('schema_version') != 1 or marker.get('variant') != 'aven' or marker.get('local_fixtures') is not False:
            parser.error('Only a normal Aven profile without demo fixtures can become the mail launcher profile')
        if args.refresh:
            with contextlib.redirect_stdout(io.StringIO()):
                refresh(profile)
        # Without --refresh retain the existing profile and user customizations.
    else:
        with contextlib.redirect_stdout(io.StringIO()):
            create(profile, 'aven', False)
    # Remote requests stay enabled, so mailto links and .eml files reach a
    # running mail window. Forward argv unchanged; never add -offline/-compose.
    script = '\n'.join([
        '#!/bin/sh', LAUNCHER_MARKER,
        'exec /usr/bin/thunderbird -profile ' + shlex.quote(str(profile)) + ' "$@"', '',
    ])
    entry = '\n'.join([
        '[Desktop Entry]', DESKTOP_MARKER, 'Type=Application',
        'Name=Thunderbird', 'Name[zh_CN]=Thunderbird 邮件', 'Name[zh_TW]=Thunderbird 郵件',
        'GenericName=Mail Client', 'Comment=Read and write email',
        'Exec=' + desktop_quote(str(launcher)) + ' %u',
        'Icon=thunderbird', 'Terminal=false', 'Categories=Network;Email;',
        'MimeType=message/rfc822;x-scheme-handler/mailto;application/x-extension-eml;',
        # Match the native Wayland app ID / KWin resource_class rather than
        # resource_name, so the canonical pinned desktop ID owns its windows.
        'StartupNotify=true', 'StartupWMClass=net.thunderbird.Thunderbird', '',
    ])
    atomic_write(launcher, script, 0o755)
    atomic_write(desktop, entry, 0o644)
    # Keep old URI associations usable without advertising a second matching
    # window identity through this hidden compatibility desktop entry.
    compatibility = entry.replace('StartupWMClass=net.thunderbird.Thunderbird\n', '')
    atomic_write(home / '.local/share/applications/aven-mail.desktop', compatibility + 'NoDisplay=true\n', 0o644)
    print(json.dumps({
        'profile': str(profile), 'profile_seeded': seeded,
        'appearance_refreshed': args.refresh and not seeded,
        'launcher': str(launcher), 'desktop': desktop.name,
        'mode': 'normal-online', 'demo_fixtures': False,
    }, indent=2))


if __name__ == '__main__':
    main()
