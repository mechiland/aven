#!/usr/bin/env python3
"""Stage the KDE SIG Plasma 6.8 Beta packages on the Fedora 44 Atomic guest."""
import argparse
import concurrent.futures
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

BASE = 'https://download.copr.fedorainfracloud.org/results/@kdesig/kde-beta/'
REPO = BASE + 'fedora-44-x86_64/'
VERSION = '6.7.90'
NS = {'r': 'http://linux.duke.edu/metadata/repo', 'c': 'http://linux.duke.edu/metadata/common'}


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def packages_from_metadata():
    repomd = fetch(REPO + 'repodata/repomd.xml')
    primary = ET.fromstring(repomd).find("r:data[@type='primary']", NS)
    packed = fetch(REPO + primary.find('r:location', NS).get('href'))
    checksum = primary.find('r:checksum', NS)
    if hashlib.new(checksum.get('type'), packed).hexdigest() != checksum.text:
        raise RuntimeError('Repository primary metadata checksum mismatch')
    raw = gzip.decompress(packed)
    result = []
    for item in ET.fromstring(raw):
        def value(name):
            return item.findtext('c:' + name, namespaces=NS)
        version = item.find('c:version', NS).attrib
        if value('arch') not in ['x86_64', 'noarch']:
            continue
        if version['ver'] != VERSION and value('name') not in ['cxx-rust-cssparser', 'kquickimageeditor-qt6']:
            continue
        check = item.find('c:checksum', NS)
        result.append({'name': value('name'), 'arch': value('arch'), **version,
                       'url': REPO + item.find('c:location', NS).get('href'),
                       'checksum_type': check.get('type'), 'checksum': check.text})
    return result, hashlib.sha256(repomd).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', action='store_true', help='Download, verify and create the Beta deployment')
    parser.add_argument('--cache', type=Path, default=Path.home()/'.cache/aven-union-platform')
    args = parser.parse_args()
    release = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    if release.get('ID', '').strip('"') != 'fedora' or release.get('VERSION_ID', '').strip('"') != '44':
        parser.error('This pinned package set is for Fedora 44')
    if not Path('/run/ostree-booted').exists() or platform.machine() != 'x86_64':
        parser.error('Run inside the x86_64 Fedora Atomic guest')
    installed = set(subprocess.check_output(['rpm', '-qa', '--qf', '%{NAME}\n'], text=True).splitlines())
    available, repo_hash = packages_from_metadata()
    selected = [p for p in available if p['name'] in installed or p['name'] in ['plasma-union', 'cxx-rust-cssparser']]
    for required in ['plasma-desktop', 'plasma-workspace', 'kwin', 'plasma-union']:
        if not any(p['name'] == required and p['ver'] == VERSION for p in selected):
            raise RuntimeError(f'The repository no longer contains the pinned {required} {VERSION}')
    args.cache.mkdir(parents=True, exist_ok=True)
    plan = {'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'source': REPO, 'repomd_sha256': repo_hash, 'plasma': '6.8 Beta (6.7.90)',
            'replace': [p for p in selected if p['name'] in installed],
            'install': [p for p in selected if p['name'] not in installed]}
    (args.cache/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    print(f"Plasma 6.8 Beta: {len(plan['replace'])} replacements, {len(plan['install'])} additions", flush=True)
    if not args.stage:
        print(args.cache/'plan.json')
        return
    def download(package):
        path = args.cache/Path(package['url']).name
        if not path.exists() or hashlib.new(package['checksum_type'], path.read_bytes()).hexdigest() != package['checksum']:
            data = fetch(package['url'])
            if hashlib.new(package['checksum_type'], data).hexdigest() != package['checksum']:
                raise RuntimeError(f"Package checksum mismatch: {package['name']}")
            path.write_bytes(data)
        return path
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        paths = list(pool.map(download, selected))
    key = args.cache/'kde-beta-pubkey.gpg'
    key.write_bytes(fetch(BASE+'pubkey.gpg'))
    keyring = args.cache/'rpm-keyring'
    keyring.mkdir(exist_ok=True)
    subprocess.run(['sudo', 'rpm', '--dbpath', str(keyring), '--import', str(key)], check=True)
    signatures = subprocess.run(['sudo', 'rpmkeys', '--dbpath', str(keyring), '--checksig', *map(str, paths)], check=True, capture_output=True, text=True)
    (args.cache/'signatures.txt').write_text(signatures.stdout)
    replacements = [str(path) for p, path in zip(selected, paths) if p['name'] in installed]
    additions = ['--install='+str(path) for p, path in zip(selected, paths) if p['name'] not in installed]
    command = ['sudo', 'rpm-ostree', 'override', 'replace', *replacements, *additions]
    print('Verified package hashes and RPM signatures; staging deployment.', flush=True)
    subprocess.run(command, check=True)
    (args.cache/'status-after-stage.json').write_text(subprocess.check_output(['rpm-ostree', 'status', '--json'], text=True))
    print('Plasma 6.8 Beta staged. Reboot, then apply the Union profile.', flush=True)


if __name__ == '__main__':
    main()
