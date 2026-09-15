#!/usr/bin/env python3
"""Copy photo/media evidence fixtures identically to stock and Aven; no preferences."""
import argparse
from pathlib import Path
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--home", required=True, type=Path)
args = parser.parse_args()
home = args.home.expanduser().resolve()
if not home.is_dir():
    parser.error("--home must already exist")
destination = home / "Pictures/日常影像"
shutil.copytree(Path(__file__).resolve().parents[1] / "fixtures/photos", destination, dirs_exist_ok=True)
print(destination)
