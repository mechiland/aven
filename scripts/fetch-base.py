#!/usr/bin/env python3
"""Fetch Fedora's signed stock image, resumably, without modifying the host OS."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '.cache/downloads'
NAME = 'Fedora-Kinoite-ostree-x86_64-44-1.7.iso'
CHECKSUM = 'Fedora-Kinoite-44-1.7-x86_64-CHECKSUM'
BASE = 'https://download.fedoraproject.org/pub/fedora/linux/releases/44/Kinoite/x86_64/iso/'
EXPECTED = '4a944312b4e861ab625fd9786957174ef122a8a406bbb54caba7665e0d9f0e92'

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for url, filename in [('https://fedoraproject.org/fedora.gpg', 'fedora.gpg'), (BASE + CHECKSUM, CHECKSUM)]:
        subprocess.run(['curl', '-fL', '--retry', '3', url, '-o', str(DEST / filename)], check=True)
    subprocess.run(['gpgv', '--keyring', str(DEST / 'fedora.gpg'), str(DEST / CHECKSUM)], check=True)
    subprocess.run(['curl', '-fL', '--retry', '5', '-C', '-', BASE + NAME, '-o', str(DEST / NAME)], check=True)
    digest = hashlib.file_digest((DEST / NAME).open('rb'), 'sha256').hexdigest()
    if digest != EXPECTED:
        raise SystemExit(f'ISO checksum mismatch: {digest}')
    print(f'Verified Fedora 44 signature and SHA-256: {digest}')

if __name__ == '__main__': main()
