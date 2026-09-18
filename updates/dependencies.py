#!/usr/bin/env python3
"""Prepare Kinoite dependencies as an Atomic deployment; never write to /usr."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from aven import atomic, digest, fetch, require_kinoite, run

ROOT = Path(__file__).resolve().parents[1]
MAX_PACKAGE = 512 * 1024 * 1024


def installed():
    output = subprocess.check_output(['rpm', '-qa', '--qf', '%{NAME} %{VERSION}-%{RELEASE}\n'], text=True)
    return dict(line.split(' ', 1) for line in output.splitlines())


def required_packages():
    packages = {'firefox', 'thunderbird', 'gwenview', 'okular', 'glibc-langpack-zh',
                'kde-gtk-config', 'qt6-qttools', 'python3-gobject', 'openssl'}
    packages.update(json.loads((ROOT/'files/integration.json').read_text())['runtime_packages'])
    for name in ('typography/fedora-packages.txt', 'photos/fedora-packages.txt'):
        packages.update(line.strip() for line in (ROOT/name).read_text().splitlines()
                        if line.strip() and not line.startswith('#'))
    return packages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--style', choices=['breeze', 'union'], required=True)
    args = parser.parse_args()
    status = require_kinoite()
    if any(item.get('staged') for item in status['deployments']):
        raise ValueError('Reboot into the pending Fedora deployment first')
    current = installed()
    missing = sorted(required_packages() - current.keys())
    # Reject an untested ABI before changing the machine. Normal Fedora patch
    # updates remain possible within these application/platform series.
    for name, prefixes in {'dolphin': ('26.04.', '26.08.'), 'firefox': ('155.',),
                           'thunderbird': ('153.',), 'gwenview': ('26.08.',),
                           'qt6-qtbase': ('6.11.',)}.items():
        if name in current and not current[name].startswith(prefixes):
            raise ValueError(f'Untested {name} version {current[name]}; a compatible Aven release is required')
    if args.style == 'union':
        lock = json.loads((ROOT/'updates/union-platform.json').read_text())
        selected = [p for p in lock['packages'] if p['name'] in current or p['name'] in ('plasma-union', 'cxx-rust-cssparser')]
        needed = [p for p in selected if current.get(p['name']) != p['ver']+'-'+p['rel']]
        if needed:
            if not current.get('plasma-desktop', '').startswith(('6.7.5-', '6.7.90-')):
                raise ValueError('This Union platform transition is tested from Plasma 6.7.5/6.7.90 only')
            print(f'Preparing {len(needed)} pinned Union dependencies; this first installation may download about 440 MB.', flush=True)
            cache = Path.home()/'.cache/aven-platform'
            cache.mkdir(parents=True, exist_ok=True)
            replacements, additions = [], []
            # All hashes and upstream URLs are inside the signed Aven release.
            # The download cache is never trusted without checking the hash.
            for package in needed:
                path = cache/Path(package['url']).name
                if not path.is_file() or digest(path) != package['checksum']:
                    size = package['bytes']
                    if type(size) is not int or not 0 < size <= MAX_PACKAGE:
                        raise ValueError('Invalid platform package size')
                    data = fetch(package['url'], size)
                    if len(data) != size:
                        raise ValueError(f'Truncated platform package: {path.name}')
                    atomic(path, data, 0o644)
                if digest(path) != package['checksum']:
                    raise ValueError(f'Platform package checksum mismatch: {path.name}')
                if package['name'] in current:
                    replacements.append(path)
                else:
                    additions.append('--install='+str(path))
            run('sudo', 'rpm-ostree', 'override', 'replace', *replacements, *additions,
                *('--install='+name for name in missing))
            return 10
    elif not current.get('plasma-desktop', '').startswith('6.7.5-'):
        raise ValueError('This Breeze profile is tested with Plasma 6.7.5 only')
    if missing:
        run('sudo', 'rpm-ostree', 'install', *missing)
        return 10
    print('Fedora Kinoite dependencies are ready; no system deployment change needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
