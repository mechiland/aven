#!/usr/bin/env python3
"""Verify the public update channel without applying anything to the host."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'updates'))
from aven import Client, DEFAULT_CHANNEL, fetch, save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--largest-platform-package', action='store_true')
    parser.add_argument('--github-metadata', type=Path, help='Saved gh api release JSON when the unauthenticated API is rate-limited')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='aven-public-verification-') as temp:
        client = Client(Path(temp))
        client.bootstrap(DEFAULT_CHANNEL, ROOT/'updates/release.pub')
        payload, envelope, channel = client.release()
        source, downloaded = client.stage(payload, envelope, channel)
        print(f'Public signature and all components verified: {downloaded} bytes', flush=True)
        source, repeated = client.stage(payload, envelope, channel)
        lock = json.loads((source/'updates/union-platform.json').read_text())
        api = json.loads(args.github_metadata.read_bytes() if args.github_metadata else
                         fetch('https://api.github.com/repos/mechiland/aven/releases/tags/aven-kinoite-44', 2*1024*1024))
        assets = {asset['name']: asset for asset in api['assets']}
        for package in lock['packages']:
            name = package['url'].rsplit('/', 1)[-1]
            asset = assets[name]
            if asset['size'] != package['bytes'] or asset['digest'] != 'sha256:'+package['checksum']:
                raise ValueError(f'Published platform metadata mismatch: {name}')
        installer = fetch(channel.rsplit('/', 1)[0]+'/Aven-Installer.tar.gz', 1024*1024)
        if 'sha256:'+hashlib.sha256(installer).hexdigest() != assets['Aven-Installer.tar.gz']['digest']:
            raise ValueError('Installer readback checksum mismatch')
        with tarfile.open(fileobj=io.BytesIO(installer), mode='r:gz') as tar:
            if set(tar.getnames()) != {'aven-installer/aven.py', 'aven-installer/release.pub'}:
                raise ValueError('Unexpected installer contents')
            if (tar.extractfile('aven-installer/aven.py').read() != (source/'updates/aven.py').read_bytes()
                    or tar.extractfile('aven-installer/release.pub').read() != (ROOT/'updates/release.pub').read_bytes()):
                raise ValueError('Bootstrap differs from the signed client or trusted public key')
        report = {'version': payload['version'], 'channel': channel, 'signature_verified': True,
                  'all_components_downloaded_and_hashed': True, 'download_bytes': downloaded,
                  'repeat_download_bytes': repeated, 'platform_server_digests_verified': len(lock['packages']),
                  'installer_bytes': len(installer), 'installer_sha256': hashlib.sha256(installer).hexdigest(),
                  'installer_matches_signed_client_and_trusted_key': True,
                  'release_draft': api['draft'], 'release_prerelease': api['prerelease']}
        report['server_metadata_source'] = 'saved GitHub API response' if args.github_metadata else 'public GitHub API'
        if args.largest_platform_package:
            package = max(lock['packages'], key=lambda item: item['bytes'])
            print(f'Checking full download of largest dependency: {package["name"]} ({package["bytes"]} bytes)', flush=True)
            data = fetch(package['url'], package['bytes'])
            if len(data) != package['bytes'] or hashlib.sha256(data).hexdigest() != package['checksum']:
                raise ValueError('Largest platform package full-download checksum mismatch')
            report['largest_platform_full_download'] = {'name': package['name'], 'bytes': len(data), 'sha256_verified': True}
        save(args.output, report)
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
