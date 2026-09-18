#!/usr/bin/env python3
"""Signed component updates for Aven on Fedora Kinoite. Python stdlib + OpenSSL."""
from __future__ import annotations

import argparse
import base64
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request

DEFAULT_CHANNEL = 'https://github.com/mechiland/aven/releases/download/aven-kinoite-44/channel.json'
COMPONENTS = {'integration', 'visual', 'typography', 'files', 'preview', 'browser', 'mail', 'photos', 'updates', 'verification'}
MAX_MANIFEST = 2 * 1024 * 1024
MAX_COMPONENT = 64 * 1024 * 1024


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def atomic(path, data, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(mode)
    temporary.replace(path)


def save(path, data):
    atomic(path, json.dumps(data, indent=2, ensure_ascii=False).encode() + b'\n')


def read_json(path, default=None):
    return json.loads(path.read_bytes()) if path.exists() else default


def run(*args, **kwargs):
    return subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def secure_url(url):
    parsed = urllib.parse.urlsplit(url)
    # Local feeds are useful for an offline mirror and the real VM test suite.
    if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password:
        return url
    if parsed.scheme == 'file' and parsed.netloc in ('', 'localhost'):
        return url
    raise ValueError('Update sources must use HTTPS (or an explicit local file:// mirror).')


class SecureRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme != 'https':
            raise ValueError('Refusing a non-HTTPS download redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, limit):
    secure_url(url)
    request = urllib.request.Request(url, headers={'User-Agent': 'Aven-Updater/1', 'Cache-Control': 'no-cache'})
    with urllib.request.build_opener(SecureRedirect()).open(request, timeout=60) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Download exceeds its allowed size')
    return data


def verify(envelope, key, *, allow_expired=False):
    if set(envelope) != {'payload', 'signature'}:
        raise ValueError('Invalid signed release envelope')
    data = canonical(envelope['payload'])
    signature = base64.b64decode(envelope['signature'], validate=True)
    with tempfile.TemporaryDirectory(prefix='aven-verify-') as temp:
        message, sig = Path(temp)/'message', Path(temp)/'signature'
        message.write_bytes(data)
        sig.write_bytes(signature)
        result = subprocess.run(['openssl', 'dgst', '-sha256', '-verify', str(key),
                                 '-signature', str(sig), str(message)], capture_output=True)
    if result.returncode:
        raise ValueError('Aven release signature verification failed')
    payload = envelope['payload']
    validate_manifest(payload, allow_expired=allow_expired)
    return payload


def validate_manifest(payload, *, allow_expired=False):
    if payload.get('schema') != 1 or type(payload.get('sequence')) is not int or payload['sequence'] < 1:
        raise ValueError('Unsupported release schema or sequence')
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.-]+)?', payload.get('version', '')):
        raise ValueError('Invalid release version')
    if payload.get('platform') != {'id': 'fedora', 'variant': 'kinoite', 'version': '44', 'arch': 'x86_64'}:
        raise ValueError('This client supports Fedora Kinoite 44 x86_64 only')
    if payload.get('style') not in ('union', 'breeze'):
        raise ValueError('Unknown Aven style')
    expires = dt.datetime.fromisoformat(payload['expires'])
    if expires.tzinfo is None or (not allow_expired and expires <= dt.datetime.now(dt.timezone.utc)):
        raise ValueError('The signed update channel has expired; ask the publisher to refresh it')
    if set(payload.get('components', {})) != COMPONENTS:
        raise ValueError('Release component set is incomplete')
    for item in payload['components'].values():
        if (not re.fullmatch('[0-9a-f]{64}', item.get('sha256', '')) or
                type(item.get('bytes')) is not int or not 0 < item['bytes'] <= MAX_COMPONENT or
                not re.fullmatch(r'[a-z]+-[0-9a-f]{64}\.tar\.gz', item.get('file', ''))):
            raise ValueError('Invalid component identity')


def unpack(archive, target, component):
    """No symlinks, hardlinks, devices, traversal, duplicates or unbounded expansion."""
    with tarfile.open(archive, 'r:gz') as tar:
        seen, size = set(), 0
        for member in tar:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or '..' in path.parts or not path.parts or
                    path.parts[0] != component or member.name != path.as_posix() or
                    member.name in seen or not member.isfile()):
                raise ValueError(f'Unsafe component member: {member.name}')
            seen.add(member.name)
            size += member.size
            if size > 256 * 1024 * 1024 or len(seen) > 10000:
                raise ValueError('Component expands beyond the allowed size')
            destination = target.joinpath(*path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as source:
                atomic(destination, source.read(), 0o755 if member.mode & 0o111 else 0o644)


def require_kinoite():
    release = {}
    for line in Path('/etc/os-release').read_text().splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            release[key] = value.strip('"')
    if (release.get('ID') != 'fedora' or release.get('VARIANT_ID') != 'kinoite' or
            release.get('VERSION_ID') != '44' or platform.machine() != 'x86_64' or
            not Path('/run/ostree-booted').exists()):
        raise ValueError('Aven currently supports an installed Fedora Kinoite 44 x86_64 system only')
    if os.getuid() == 0:
        raise ValueError('Run aven as your desktop user, without sudo; it requests sudo only for system dependencies')
    return json.loads(subprocess.check_output(['rpm-ostree', 'status', '--json']))


def require_closed():
    for app in ('dolphin', 'firefox', 'thunderbird', 'gwenview', 'aven-preview'):
        if subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', app], stdout=subprocess.DEVNULL).returncode == 0:
            raise ValueError(f'Close {app} before applying the update, then run the same command again')
    # Preview is a Python process; the comm name is usually python3.
    for path in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            if path.stat().st_uid == os.getuid() and b'/aven-preview\0' in path.read_bytes():
                raise ValueError('Close Aven Preview before updating')
        except (PermissionError, FileNotFoundError, ProcessLookupError):
            pass


def require_session():
    dbus = shutil.which('qdbus6') or shutil.which('qdbus-qt6') or shutil.which('qdbus')
    if not dbus or subprocess.run([dbus, 'org.kde.plasmashell', '/PlasmaShell'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        raise ValueError('Apply Aven updates from Konsole in your running Plasma desktop; downloads/checks can run without it')


class Client:
    def __init__(self, home=None):
        self.home = Path(home or Path.home())
        self.root = self.home/'.local/share/aven/updater'
        self.state = self.home/'.local/state/aven/updates'
        self.config = self.root/'config.json'
        self.key = self.root/'release.pub'
        self.receipt = self.state/'installed.json'
        self.journal = self.state/'pending.json'
        self.cache = self.root/'objects'

    @contextlib.contextmanager
    def lock(self):
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (self.state/'lock').open('a') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError('Another Aven update is already running')
            yield

    def bootstrap(self, channel, key):
        secure_url(channel)
        if self.config.exists():
            config = read_json(self.config)
            if config['channel'] != channel or self.key.read_bytes() != key.read_bytes():
                raise ValueError('An updater is already configured with another channel or signing key')
            return
        launcher = self.home/'.local/bin/aven'
        if launcher.exists() or launcher.is_symlink():
            raise ValueError(f'Refusing to replace an existing command: {launcher}')
        atomic(self.key, key.read_bytes(), 0o644)
        atomic(self.root/'aven.py', Path(__file__).read_bytes(), 0o755)
        atomic(launcher, ('#!/bin/sh\nexec /usr/bin/python3 ' +
                         shlex.quote(str(self.root/'aven.py')) + ' "$@"\n').encode(), 0o755)
        save(self.config, {'schema': 1, 'channel': channel})

    def release(self):
        if not self.config.exists():
            raise ValueError('Run the downloaded Aven installer first')
        channel = read_json(self.config)['channel']
        envelope = json.loads(fetch(channel, MAX_MANIFEST))
        payload = verify(envelope, self.key)
        high = read_json(self.state/'highest.json', {'sequence': 0})
        identity = hashlib.sha256(canonical(payload)).hexdigest()
        if payload['sequence'] < high['sequence']:
            raise ValueError('Refusing an older release from the update server (use aven rollback for local recovery)')
        if payload['sequence'] == high['sequence'] and identity != high.get('sha256'):
            raise ValueError('Release sequence was reused with different contents')
        save(self.state/'highest.json', {'sequence': payload['sequence'], 'sha256': identity})
        return payload, envelope, channel

    def plan(self, payload):
        installed = read_json(self.receipt, {})
        previous = installed.get('release', {}).get('components', {})
        changed = [name for name, entry in payload['components'].items()
                   if previous.get(name, {}).get('sha256') != entry['sha256']]
        needed = [name for name in changed if not self.cached(payload['components'][name])]
        return {'installed': installed.get('release', {}).get('version'), 'available': payload['version'],
                'changed_components': sorted(changed),
                'download_bytes': sum(payload['components'][name]['bytes'] for name in needed)}

    def cached(self, item):
        path = self.cache/item['file']
        return path.is_file() and path.stat().st_size == item['bytes'] and digest(path) == item['sha256']

    def stage(self, payload, envelope, channel):
        identity = hashlib.sha256(canonical(payload)).hexdigest()
        destination = self.root/'versions'/identity
        if destination.exists():
            # Reconstruct every time from verified archives; an interrupted or
            # locally edited staged tree is never executed on trust alone.
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        downloaded = 0
        try:
            for name, item in sorted(payload['components'].items()):
                path = self.cache/item['file']
                if not self.cached(item):
                    data = fetch(urllib.parse.urljoin(channel, item['file']), item['bytes'])
                    if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                        raise ValueError(f'Corrupt download: {name}')
                    atomic(path, data, 0o644)
                    downloaded += len(data)
                unpack(path, destination, name)
            save(destination/'release.json', envelope)
        except BaseException:
            shutil.rmtree(destination)
            raise
        return destination, downloaded

    def apply(self, payload, source, downloaded, reset_defaults=False):
        require_closed()
        require_session()
        if self.journal.exists():
            raise ValueError('An interrupted update needs recovery: run aven recover first')
        previous = read_json(self.receipt)
        legacy = (self.home/'.local/share/aven/firefox/.aven-profile').exists()
        mode = 'update' if previous or legacy else 'install'
        if reset_defaults:
            mode = 'install'
        if previous and previous['release']['style'] != payload['style']:
            raise ValueError('A style/platform switch requires a new explicit installation')
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        transaction = self.state/'transactions'/stamp
        transaction.mkdir(parents=True)
        helper = source/'updates/profile.py'
        run(sys.executable, helper, 'snapshot', '--destination', transaction/'before')
        # A receipt is committed only after every component and snapshot succeeds.
        pending = {'transaction': str(transaction), 'source': str(source), 'previous': previous,
                   'release': payload, 'mode': mode, 'downloaded_bytes': downloaded}
        save(self.journal, pending)
        try:
            options = ['--previous-source', previous['source']] if previous and previous.get('source') else []
            run(sys.executable, helper, 'apply', '--style', payload['style'], '--mode', mode, *options)
            run(sys.executable, helper, 'snapshot', '--destination', transaction/'after')
            receipt = {'release': payload, 'source': str(source), 'transaction': str(transaction),
                       'previous': previous, 'installed_at': stamp, 'downloaded_bytes': downloaded}
            save(self.receipt, receipt)
            # Update the client itself from the signed integration payload.
            atomic(self.root/'aven.py', (source/'updates/aven.py').read_bytes(), 0o755)
            self.journal.unlink()
        except BaseException:
            print('Update did not finish. The previous receipt is retained. Run aven recover.', file=sys.stderr)
            raise
        print(f'Aven {payload["version"]} installed. Downloaded {downloaded:,} bytes. Log out and back in to reload the desktop.')

    def recover(self):
        require_closed()
        pending = read_json(self.journal)
        if not pending:
            print('No interrupted Aven update.')
            return
        run(sys.executable, Path(pending['source'])/'updates/profile.py', 'restore',
            '--destination', Path(pending['transaction'])/'before')
        if pending['previous']:
            save(self.receipt, pending['previous'])
        else:
            self.receipt.unlink(missing_ok=True)
        self.journal.unlink()
        print('Restored the configuration and assets from before the interrupted update. Log out and back in.')

    def rollback(self):
        require_closed()
        if self.journal.exists():
            raise ValueError('Run aven recover before rolling back')
        current = read_json(self.receipt)
        if not current or not current.get('previous'):
            raise ValueError('No previous Aven release is available for rollback')
        transaction = Path(current['transaction'])
        # Protect settings edited since the update. Restore only files still
        # matching the post-update snapshot; report conflicts for explicit review.
        run(sys.executable, Path(current['source'])/'updates/profile.py', 'restore',
            '--destination', transaction/'before', '--expected', transaction/'after')
        save(self.receipt, current['previous'])
        print('Restored the previous Aven release. Fedora deployment and personal data are unchanged. Log out and back in.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['install', 'update', 'check', 'status', 'rollback', 'recover'])
    parser.add_argument('--channel', help='Signed HTTPS channel (first installation only)')
    parser.add_argument('--key', type=Path, help='Trusted release public key (first installation only)')
    parser.add_argument('--download-only', action='store_true')
    parser.add_argument('--reset-defaults', action='store_true', help='Explicitly reapply Aven layout and defaults')
    args = parser.parse_args()
    client = Client()
    try:
        status = require_kinoite()
        with client.lock():
            if args.command == 'status':
                installed = read_json(client.receipt, {})
                print(json.dumps({'version': installed.get('release', {}).get('version'),
                                  'style': installed.get('release', {}).get('style'),
                                  'installed_at': installed.get('installed_at'),
                                  'channel': read_json(client.config, {}).get('channel'),
                                  'recovery_required': client.journal.exists(),
                                  'rollback_available': bool(installed.get('previous'))}, indent=2))
                return 0
            if args.command == 'recover':
                client.recover()
                return 0
            if args.command == 'rollback':
                client.rollback()
                return 0
            if args.command == 'install' and not client.config.exists():
                key = args.key or Path(__file__).with_name('release.pub')
                client.bootstrap(args.channel or DEFAULT_CHANNEL, key)
            elif args.channel or args.key:
                raise ValueError('--channel and --key are only accepted during first installation')
            if client.journal.exists():
                raise ValueError('Run aven recover before another update')
            payload, envelope, channel = client.release()
            plan = client.plan(payload)
            print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
            if args.command == 'check':
                return 0
            installed = read_json(client.receipt)
            if installed and installed['release']['style'] != payload['style']:
                raise ValueError('This channel changed the desktop platform; a separate explicit installation is required')
            if installed and installed['release'] == payload and not args.reset_defaults:
                print('Aven is up to date.')
                return 0
            source, downloaded = client.stage(payload, envelope, channel)
            if args.download_only:
                print('Verified update downloaded. Run aven update to apply it.')
                return 0
            if any(item.get('staged') for item in status.get('deployments', [])):
                raise ValueError('A Fedora deployment is already staged. Reboot before continuing the Aven installation')
            result = subprocess.run([sys.executable, str(source/'updates/dependencies.py'),
                                     '--style', payload['style']])
            if result.returncode == 10:
                print('System dependencies staged with rpm-ostree. Reboot, then run ~/.local/bin/aven update to finish.')
                return 10
            result.check_returncode()
            client.apply(payload, source, downloaded, args.reset_defaults)
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError, KeyError) as error:
        print(f'Aven: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
