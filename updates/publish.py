#!/usr/bin/env python3
"""Publish verified component objects first, then the signed channel pointer."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from aven import canonical, digest, verify

REPOSITORY = 'mechiland/aven'
TAG = 'aven-kinoite-44'


def gh(*args, **kwargs):
    return subprocess.run(['gh', *map(str, args), '--repo', REPOSITORY], check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--publish', action='store_true', help='Upload and activate; otherwise print the publication plan')
    parser.add_argument('--notes', type=Path, help='Release notes (required for first publication)')
    parser.add_argument('--target', help='Pushed source commit/branch for a new channel tag (defaults to HEAD)')
    args = parser.parse_args()
    directory = args.directory.resolve()
    envelope = json.loads((directory/'channel.json').read_text())
    payload = verify(envelope, directory/'release.pub')
    objects = []
    for entry in payload['components'].values():
        path = directory/entry['file']
        if path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError(f'Invalid release artifact: {path}')
        objects.append(path)
    # Mirrored runtime dependencies retain their exact authenticated checksums.
    for path in sorted(directory.glob('platform-*.rpm')):
        if path.name != 'platform-'+digest(path)+'.rpm':
            raise ValueError(f'Invalid mirrored dependency: {path}')
        objects.append(path)
    print(json.dumps({'repository': REPOSITORY, 'tag': TAG, 'version': payload['version'],
                      'sequence': payload['sequence'], 'objects': len(objects),
                      'bytes': sum(path.stat().st_size for path in objects),
                      'activation': 'channel.json uploaded last', 'publish': args.publish}, indent=2))
    if not args.publish:
        return
    target = args.target or subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    result = subprocess.run(['gh', 'release', 'view', TAG, '--repo', REPOSITORY,
                             '--json', 'assets,isDraft'], capture_output=True, text=True)
    created = bool(result.returncode)
    if created:
        if not args.notes:
            raise ValueError('--notes is required for a new update channel')
        gh('release', 'create', TAG, '--draft', '--prerelease', '--title', 'Aven — Kinoite 44 update channel',
           '--notes-file', args.notes, '--target', target)
        remote = {'assets': [], 'isDraft': True}
    else:
        remote = json.loads(result.stdout)
    existing = {item['name']: item for item in remote['assets']}
    with tempfile.TemporaryDirectory(prefix='aven-publish-') as temporary:
        temp = Path(temporary)
        if 'release.pub' in existing:
            gh('release', 'download', TAG, '--pattern', 'release.pub', '--dir', temp)
            if (temp/'release.pub').read_bytes() != (directory/'release.pub').read_bytes():
                raise ValueError('The channel signing key cannot be replaced silently')
        if 'channel.json' in existing:
            gh('release', 'download', TAG, '--pattern', 'channel.json', '--dir', temp)
            prior = verify(json.loads((temp/'channel.json').read_text()), directory/'release.pub', allow_expired=True)
            if (payload['sequence'] < prior['sequence'] or
                    (payload['sequence'] == prior['sequence'] and canonical(payload) != canonical(prior))):
                raise ValueError('The new channel sequence must be greater than the published one')
        for path in objects:
            if path.name in existing:
                # GitHub's asset digest is authoritative when present. Otherwise
                # fetch and hash the immutable object before reusing its name.
                entry = existing[path.name]
                if entry.get('digest') == 'sha256:'+digest(path):
                    continue
                gh('release', 'download', TAG, '--pattern', path.name, '--dir', temp)
                if digest(temp/path.name) != digest(path):
                    raise ValueError(f'Refusing to overwrite a different immutable object: {path.name}')
                (temp/path.name).unlink()
            else:
                gh('release', 'upload', TAG, path)
        # Keep an immutable copy of each manifest for audits and disaster recovery.
        versioned = temp/f'release-{payload["sequence"]}-{payload["version"]}.json'
        versioned.write_bytes((directory/'channel.json').read_bytes())
        if versioned.name in existing:
            check = temp/'existing'
            check.mkdir()
            gh('release', 'download', TAG, '--pattern', versioned.name, '--dir', check)
            if digest(check/versioned.name) != digest(versioned):
                raise ValueError('An immutable release manifest already exists with different contents')
        else:
            gh('release', 'upload', TAG, versioned)
        for name in ('release.pub', 'Aven-Installer.tar.gz', 'SHA256SUMS'):
            gh('release', 'upload', TAG, directory/name, '--clobber')
        gh('release', 'upload', TAG, directory/'channel.json', '--clobber')
        # Read the activated manifest back before announcing success.
        (temp/'channel.json').unlink(missing_ok=True)
        gh('release', 'download', TAG, '--pattern', 'channel.json', '--dir', temp)
        if (temp/'channel.json').read_bytes() != (directory/'channel.json').read_bytes():
            raise ValueError('Published channel readback mismatch')
        if remote['isDraft']:
            gh('release', 'edit', TAG, '--draft=false', '--prerelease')
    print('Published https://github.com/mechiland/aven/releases/tag/'+TAG)


if __name__ == '__main__':
    main()
