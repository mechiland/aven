#!/usr/bin/env python3
"""Build deterministic small component archives and one signed update envelope."""
from __future__ import annotations
import argparse
import base64
import datetime as dt
import gzip
import io
import json
from pathlib import Path
import subprocess
import tarfile

from aven import COMPONENTS, canonical, digest, save, validate_manifest

ROOT = Path(__file__).resolve().parents[1]


def files(root, component):
    for path in sorted((root/component).rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Release sources cannot contain symlinks: {path}')
        if (not path.is_file() or '__pycache__' in path.parts or 'tests' in path.parts
                or path.suffix in ('.pyc', '.md', '.log')
                or (component != 'visual' and path.suffix in ('.png', '.jpg'))):
            continue
        if component == 'verification' and path.name != 'restore_profile.py':
            continue
        if component == 'updates' and path.name in ('build.py', 'publish.py'):
            continue
        yield path


def archive(root, paths, overrides=None):
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', mtime=0, filename='') as compressed:
        with tarfile.open(fileobj=compressed, mode='w', format=tarfile.USTAR_FORMAT) as tar:
            for path in paths:
                entry = tarfile.TarInfo(path.relative_to(root).as_posix())
                data = (overrides or {}).get(path.relative_to(root).as_posix(), path.read_bytes())
                entry.size = len(data)
                entry.mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
                entry.mtime = 0
                tar.addfile(entry, io.BytesIO(data))
    return buffer.getvalue()


def build(root, output, key, version, sequence, style, lifetime=90, platform_cache=None, asset_base=None):
    output.mkdir(parents=True, exist_ok=True)
    payload = {'schema': 1, 'sequence': sequence, 'version': version, 'style': style,
               'platform': {'id': 'fedora', 'variant': 'kinoite', 'version': '44', 'arch': 'x86_64'},
               'expires': (dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=lifetime)).isoformat(),
               'components': {}}
    import hashlib
    overrides = {}
    if platform_cache:
        if not asset_base or not asset_base.startswith('https://'):
            raise ValueError('--platform-cache requires an HTTPS --asset-base')
        lock = json.loads((root/'updates/union-platform.json').read_text())
        for package in lock['packages']:
            path = platform_cache/Path(package['url']).name
            if digest(path) != package['checksum']:
                raise ValueError(f'Platform cache hash mismatch: {path}')
            name = 'platform-'+package['checksum']+'.rpm'
            target = output/name
            if not target.exists():
                import shutil
                shutil.copyfile(path, target)
            package['url'] = asset_base.rstrip('/')+'/'+name
        overrides['updates/union-platform.json'] = json.dumps(lock, indent=2).encode()+b'\n'
    for component in sorted(COMPONENTS):
        data = archive(root, files(root, component), overrides)
        checksum = hashlib.sha256(data).hexdigest()
        name = f'{component}-{checksum}.tar.gz'
        (output/name).write_bytes(data)
        payload['components'][component] = {'file': name, 'sha256': checksum, 'bytes': len(data)}
    validate_manifest(payload)
    message = output/'payload.json'
    message.write_bytes(canonical(payload))
    signature = subprocess.check_output(['openssl', 'dgst', '-sha256', '-sign', str(key), str(message)])
    message.unlink()
    save(output/'channel.json', {'payload': payload, 'signature': base64.b64encode(signature).decode()})
    public = output/'release.pub'
    subprocess.run(['openssl', 'pkey', '-in', str(key), '-pubout', '-out', str(public)], check=True)
    # Small standalone installer. The initial key is trusted through the
    # release download; subsequent payloads must match this pinned key.
    with tarfile.open(output/'Aven-Installer.tar.gz', 'w:gz') as tar:
        tar.add(root/'updates/aven.py', arcname='aven-installer/aven.py')
        tar.add(public, arcname='aven-installer/release.pub')
    artifacts = [output/'channel.json', public, output/'Aven-Installer.tar.gz']
    artifacts += [output/item['file'] for item in payload['components'].values()]
    artifacts += sorted(output.glob('platform-*.rpm'))
    (output/'SHA256SUMS').write_text(''.join(f'{digest(path)}  {path.name}\n' for path in sorted(artifacts)))
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--key', type=Path, required=True, help='Private signing key outside the repository')
    parser.add_argument('--version', required=True)
    parser.add_argument('--sequence', type=int, required=True, help='Strictly increasing channel sequence')
    parser.add_argument('--style', choices=['union', 'breeze'], default='union')
    parser.add_argument('--platform-cache', type=Path, help='Mirror the pinned Union RPMs into the release')
    parser.add_argument('--asset-base', help='HTTPS directory that will serve release assets')
    args = parser.parse_args()
    payload = build(args.source, args.output, args.key, args.version, args.sequence, args.style,
                    platform_cache=args.platform_cache, asset_base=args.asset_base)
    print(json.dumps({'version': payload['version'], 'profile_bytes': sum(p['bytes'] for p in payload['components'].values()),
                      'output': str(args.output)}, indent=2))


if __name__ == '__main__':
    main()
