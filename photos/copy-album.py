#!/usr/bin/env python3
"""Seed the same natural photo album in stock/Aven, without changing preferences."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", required=True, type=Path)
    parser.add_argument("--verify", action="store_true", help="Only verify the guest album against its source manifest")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    if not home.is_dir():
        parser.error("--home must already exist")
    source = Path(__file__).resolve().parents[1] / "fixtures/photos-album"
    manifest = json.loads((source / "manifest.json").read_text())
    destination = home / "Pictures" / manifest["album"]
    for asset in manifest["assets"]:
        original = source / asset["file"]
        target = destination / asset["file"]
        if sha256(original) != asset["sha256"]:
            parser.error(f"Source fixture checksum mismatch: {original}")
        if target.exists() and sha256(target) != asset["sha256"]:
            parser.error(f"Existing photo differs; preserved without overwriting: {target}")
        if args.verify and not target.is_file():
            parser.error(f"Album photo missing: {target}")
    if not args.verify:
        destination.mkdir(parents=True, exist_ok=True)
        for asset in manifest["assets"]:
            shutil.copy2(source / asset["file"], destination / asset["file"])
        # Keep source/rights documentation available without adding non-photo
        # items to the everyday album's visible file-manager contents.
        attribution = destination / ".attribution"
        attribution.mkdir(exist_ok=True)
        for filename in ("ATTRIBUTION.md", "LICENSE-CC0.txt", "manifest.json"):
            shutil.copy2(source / filename, attribution / filename)
    print(json.dumps({"album": str(destination), "photos": len(manifest["assets"]),
                      "bytes": sum(asset["bytes"] for asset in manifest["assets"]),
                      "hashes_verified": True, "copied": not args.verify}, ensure_ascii=False))


if __name__ == "__main__":
    main()
