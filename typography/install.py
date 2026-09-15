#!/usr/bin/env python3
"""Stage Aven fontconfig into an explicit guest/image root, preserving previous files."""
import argparse
from pathlib import Path
import shutil
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", required=True, type=Path, help="Image root; use / only inside the intended Aven guest")
args = parser.parse_args()
destination = args.root.resolve() / "etc/fonts/conf.d"
destination.mkdir(parents=True, exist_ok=True)
for source in sorted((Path(__file__).parent / "fontconfig").glob("*.conf")):
    target = destination / source.name
    if target.exists() and target.read_bytes() != source.read_bytes():
        backup = target.with_name(target.name + f".pre-aven-{time.time_ns()}")
        shutil.copy2(target, backup)
        print(f"Saved {backup}")
    shutil.copy2(source, target)
    print(f"Installed {target}")
print("Install typography/fedora-packages.txt through the guest image's package workflow.")
print("In the guest: fc-cache -f; restart applications; python3 typography/audit.py --active")
