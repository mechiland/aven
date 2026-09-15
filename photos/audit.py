#!/usr/bin/env python3
"""Read-only audit of Aven Gwenview settings, fixture integrity and native package."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from profile import ROOT


def normalize(value, schema):
    if value is None:
        value = schema["default"]
    if schema["type"] == "Enum":
        if value.isdecimal() and int(value) < len(schema["choices"]):
            return schema["choices"][int(value)]
        # The schema default sometimes qualifies the enclosing namespace too.
        return next((choice for choice in schema["choices"] if value.endswith(choice)), value)
    if schema["type"] == "Double":
        return float(value)
    if schema["type"] == "IntList":
        return [int(item) for item in value.split(",")]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, help="Explicit guest home to inspect")
    parser.add_argument("--active", action="store_true", help="Read native package and image associations")
    args = parser.parse_args()
    fixture_root = ROOT / "fixtures/photos"
    fixture_manifest = json.loads((fixture_root / "manifest.json").read_text())
    fixtures = []
    for asset in fixture_manifest["assets"]:
        path = fixture_root / asset["file"]
        fixtures.append({"file": asset["file"], "matches": path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == asset["sha256"]})
    report = {"fixtures": fixtures, "settings": None, "visual_verified": False, "motion_verified": False}
    if args.home:
        home = args.home.expanduser().resolve()
        marker = home / ".local/share/aven/photos-profile.json"
        target = home / ".config/gwenviewrc"
        report["settings"] = []
        if marker.is_file():
            schema = json.loads((ROOT / "photos/schema.json").read_text())["groups"]
            config = configparser.ConfigParser(interpolation=None, strict=False)
            config.optionxform = str
            config.read(target, encoding="utf-8")
            for section, settings in json.loads(marker.read_text())["preferences"].items():
                for key, expected in settings.items():
                    actual = config.get(section, key, fallback=None)
                    effective = normalize(actual, schema[section][key])
                    mutable = schema[section][key].get("mutable_layout", False)
                    matches = (len(effective) == 2 and min(effective) >= 0 and sum(effective) > 0) if mutable else normalize(expected, schema[section][key]) == effective
                    report["settings"].append({"group": section, "key": key, "expected": expected, "actual": actual, "effective": effective, "mutable_layout": mutable, "matches": matches})
        else:
            report["settings"].append({"matches": False, "error": "No Aven photos profile marker"})
    if args.active:
        report["native_package"] = subprocess.run(["rpm", "-q", "gwenview", "qt6-qtimageformats"], capture_output=True, text=True).stdout.strip() if shutil.which("rpm") else None
        if shutil.which("xdg-mime"):
            report["associations"] = {mime: subprocess.run(["xdg-mime", "query", "default", mime], capture_output=True, text=True).stdout.strip() for mime in ("image/jpeg", "image/png", "image/webp")}
    report["config_and_fixtures_ok"] = all(item["matches"] for item in fixtures + (report["settings"] or []))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["config_and_fixtures_ok"] else 1)


if __name__ == "__main__":
    main()
