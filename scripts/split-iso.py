#!/usr/bin/env python3
"""Prepare GitHub-sized ISO parts with per-part and whole-image checksums."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PART_BYTES = 1900 * 1024 * 1024


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'output/release-assets')
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('Choose a new or empty release assets directory')
    args.output.mkdir(parents=True, exist_ok=True)
    parts, whole, total = [], hashlib.sha256(), 0
    with args.iso.open('rb') as source:
        while True:
            data = source.read(min(8 * 1024 * 1024, PART_BYTES))
            if not data:
                break
            path = args.output / f'{args.iso.name}.part-{len(parts):03d}'
            digest, size = hashlib.sha256(), 0
            with path.open('xb') as target:
                while data:
                    target.write(data)
                    digest.update(data)
                    whole.update(data)
                    size += len(data)
                    total += len(data)
                    if size == PART_BYTES:
                        break
                    data = source.read(min(8 * 1024 * 1024, PART_BYTES - size))
            parts.append({'file': path.name, 'bytes': size, 'sha256': digest.hexdigest()})
    manifest = {'schema_version': 1, 'iso': {'file': args.iso.name, 'bytes': total, 'sha256': whole.hexdigest()}, 'parts': parts}
    (args.output / 'ISO-PARTS.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (args.output / 'ISO-SHA256SUMS').write_text(''.join(f'{item["sha256"]}  {item["file"]}\n' for item in [*parts, manifest['iso']]))
    shutil.copy2(ROOT / 'scripts/reassemble-iso.py', args.output / 'reassemble-iso.py')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
