#!/usr/bin/env python3
"""Verify and reconstruct the Aven ISO parts downloaded from one GitHub release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('ISO-PARTS.json'))
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    directory = args.manifest.resolve().parent
    names = [manifest['iso']['file']] + [part['file'] for part in manifest['parts']]
    if any(Path(name).name != name or name in ['', '.', '..'] or '/' in name or '\\' in name for name in names):
        parser.error('Manifest filenames must be simple names in the download directory')
    output = directory / manifest['iso']['file']
    if output.exists():
        parser.error(f'Refusing to overwrite {output}')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=output.name + '.', suffix='.partial', dir=directory, delete=False) as assembled:
            temporary = Path(assembled.name)
            whole = hashlib.sha256()
            size = 0
            for part in manifest['parts']:
                source = directory / part['file']
                if source.stat().st_size != part['bytes']:
                    raise ValueError(f'Part size mismatch: {source.name}')
                print(f'Verifying {source.name}', flush=True)
                digest = hashlib.sha256()
                with source.open('rb') as stream:
                    while data := stream.read(8 * 1024 * 1024):
                        digest.update(data)
                        whole.update(data)
                        size += len(data)
                        assembled.write(data)
                if digest.hexdigest() != part['sha256']:
                    raise ValueError(f'Part checksum mismatch: {source.name}')
            if size != manifest['iso']['bytes'] or whole.hexdigest() != manifest['iso']['sha256']:
                raise ValueError('Reconstructed ISO checksum mismatch')
            assembled.flush()
            os.fsync(assembled.fileno())
        # Same-directory hard link provides no-overwrite publication, including on Windows.
        os.link(temporary, output)
        print(f'Verified ISO: {output}\nSHA-256: {whole.hexdigest()}')
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
