#!/usr/bin/env python3
"""Prepare disposable files; verify bytes after operations performed in Dolphin.

No copy/move/rename/trash operation is automated here. The file manager must do
those actions. A passing byte check alone does not establish UI usability.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil

MARKER = ".aven-operation-fixture.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() and not path.is_symlink() else None


def prepare(root, source):
    if root.exists():
        raise ValueError("Use a fresh destination; existing trees are never overwritten")
    if not source.is_file() or source.is_symlink():
        raise ValueError("Source must be one regular fixture file")
    root.mkdir(parents=True)
    for folder in ["01 原件", "02 复制", "03 移动"]:
        (root / folder).mkdir()
    name = "周末 清单 100% #1" + source.suffix
    shutil.copy2(source, root / "01 原件" / name)
    manifest = {"schema_version": 1, "name": name, "renamed": "已整理 · Weekend" + source.suffix,
                "sha256": digest(source), "prepared_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (root / MARKER).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return {"root": str(root), "fixture": manifest, "next": "Open this folder in Dolphin; follow docs/verification.md operations sequence"}


def verify(root, stage):
    marker = root / MARKER
    if not marker.is_file() or marker.is_symlink():
        raise ValueError("Destination is not an Aven operation fixture")
    data = json.loads(marker.read_text())
    name, renamed, expected = data["name"], data["renamed"], data["sha256"]
    # Marker names are data, not arbitrary file paths.
    if any(Path(value).name != value for value in [name, renamed]):
        raise ValueError("Invalid fixture names")
    present = ["01 原件/" + name]
    absent = []
    if stage == "copied":
        present += ["02 复制/" + name]
    elif stage == "moved":
        present += ["03 移动/" + name]
        absent += ["02 复制/" + name]
    elif stage in ["renamed", "restored"]:
        present += ["03 移动/" + renamed]
        absent += ["02 复制/" + name, "03 移动/" + name]
    elif stage == "trashed":
        absent += ["02 复制/" + name, "03 移动/" + name, "03 移动/" + renamed]
    checks = [{"path": relative, "expected": expected, "actual": digest(root / relative), "passed": digest(root / relative) == expected} for relative in present]
    checks += [{"path": relative, "expected": "absent", "passed": not (root / relative).exists() and not (root / relative).is_symlink()} for relative in absent]
    return {"schema_version": 1, "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "root": str(root), "stage": stage, "passed": all(x["passed"] for x in checks), "checks": checks,
            "ui_verified": False, "note": "Bytes and source preservation only; pair with witnessed Dolphin UI action evidence."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    prep = subs.add_parser("prepare")
    prep.add_argument("--root", type=Path, required=True)
    prep.add_argument("--source", type=Path, required=True)
    check = subs.add_parser("verify")
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--stage", required=True, choices=["copied", "moved", "renamed", "trashed", "restored"])
    args = parser.parse_args()
    try:
        result = prepare(args.root.resolve(), args.source.resolve()) if args.command == "prepare" else verify(args.root.resolve(), args.stage)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
