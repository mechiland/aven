#!/usr/bin/env python3
"""Seed scoped Gwenview defaults into an explicit guest home after baseline capture."""
import argparse
import configparser
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import time

from profile import preferences


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, encoding="utf-8", delete=False) as stream:
        stream.write(text)
        tmp = Path(stream.name)
    tmp.chmod(0o600)
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", required=True, type=Path)
    parser.add_argument("--refresh", action="store_true", help="Reapply managed defaults; close Gwenview first")
    parser.add_argument("--reduced-motion", action="store_true", help="Disable image fades")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    if not home.is_dir() or home.stat().st_uid != os.getuid():
        parser.error("--home must be an existing directory owned by the current user")
    marker = home / ".local/share/aven/photos-profile.json"
    target = home / ".config/gwenviewrc"
    if marker.exists() and not args.refresh:
        print(json.dumps({"seeded": False, "reason": "Profile already seeded; user preferences retained"}))
        return
    # KConfig stores its user files on application exit. Refuse an active process
    # for this target home, preventing a running viewer from losing preferences.
    for process in Path("/proc").glob("[0-9]*"):
        try:
            if process.stat().st_uid != os.getuid() or (process / "comm").read_text().strip() != "gwenview":
                continue
            env = (process / "environ").read_bytes().split(b"\0")
            if ("HOME=" + str(home)).encode() in env:
                parser.error("Close Gwenview before installing its defaults")
        except (PermissionError, FileNotFoundError, ProcessLookupError):
            continue
    values = preferences(args.reduced_motion)
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    if target.exists():
        config.read(target, encoding="utf-8")
    for section, settings in values.items():
        if not config.has_section(section):
            config.add_section(section)
        for key, value in settings.items():
            config.set(section, key, value)
    rendered = io.StringIO()
    config.write(rendered, space_around_delimiters=False)
    if target.exists():
        backup = target.with_name(f"gwenviewrc.pre-aven-{time.time_ns()}")
        shutil.copy2(target, backup)
    atomic_write(target, rendered.getvalue())
    manifest = {
        "schema_version": 1,
        "application": "org.kde.gwenview.desktop",
        "preferences": values,
        "reduced_motion": args.reduced_motion,
        "upstream_schema_versions_checked": ["25.12.3", "26.04.0"],
        "motion": "Upstream 250 ms software fade" if not args.reduced_motion else "No image animation",
        "visual_verified": False,
    }
    atomic_write(marker, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"seeded": True, "config": str(target), "manifest": str(marker)}))


if __name__ == "__main__":
    main()
