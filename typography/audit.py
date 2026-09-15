#!/usr/bin/env python3
"""Check actual font resolution; this is not a visual quality test.

Default: test candidate rules in an isolated fontconfig configuration, appended
to the current host's fonts. --active: inspect the current environment verbatim.
The latter must run inside the booted guest after installation.
"""

import argparse
import datetime
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
FIELDS = ["family", "style", "file", "index", "weight", "antialias", "hinting",
          "hintstyle", "rgba", "autohint", "embeddedbitmap", "embolden", "color"]
REGIONS = {"en": "SC", "zh-cn": "SC", "zh-sg": "SC", "zh-tw": "TC",
           "zh-hk": "HK", "zh-mo": "HK", "ja": "JP", "ko": "KR"}


def run(args, env):
    result = subprocess.run(args, env=env, text=True, capture_output=True, check=True)
    if result.stderr.strip():
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def inspect(pattern, env):
    output = run(["fc-match", "--format", "\t".join("%{" + f + "}" for f in FIELDS), pattern], env)
    return dict(zip(FIELDS, output.split("\t")))


def checks(env):
    results = []

    def check(label, pattern, expected, properties=None):
        found = inspect(pattern, env)
        errors = []
        if expected not in found["family"].split(","):
            errors.append(f"Expected {expected}; got {found['family']}")
        for key, value in (properties or {}).items():
            if found.get(key) != value:
                errors.append(f"{key}: expected {value}; got {found.get(key)}")
        results.append({"label": label, "pattern": pattern, "font": found,
                        "passed": not errors, "errors": errors})

    rendering = {"antialias": "True", "hinting": "True", "hintstyle": "1", "rgba": "5"}
    for family, expected in [("sans-serif", "Noto Sans"), ("system-ui", "Noto Sans"),
                             ("Noto Sans", "Noto Sans"), ("monospace", "Noto Sans Mono")]:
        check(f"Latin / {family}", f"{family}:lang=en:charset=0041", expected, rendering)
    for locale, region in REGIONS.items():
        for family, expected in [("sans-serif", f"Noto Sans CJK {region}"),
                                 ("Noto Sans", f"Noto Sans CJK {region}"),
                                 ("monospace", f"Noto Sans Mono CJK {region}")]:
            check(f"Han region / {locale} / {family}",
                  f"{family}:lang={locale}:charset=4e2d", expected, rendering)
    for locale, region in [("zh-cn", "SC"), ("zh-tw", "TC"), ("zh-hk", "HK")]:
        for weight, expected_weight in [("regular", "80"), ("medium", "100"), ("bold", "200")]:
            check(f"Real weight / {locale} / {weight}",
                  f"Noto Sans:lang={locale}:weight={weight}:charset=4e2d",
                  f"Noto Sans CJK {region}", {"weight": expected_weight, "embolden": "False"})
        check(f"CJK punctuation / {locale}", f"sans-serif:lang={locale}:charset=3001 3002 ff0c ff1a",
              f"Noto Sans CJK {region}", rendering)
    check("Emoji", "emoji:charset=1f600", "Noto Color Emoji",
          {"color": "True", "embeddedbitmap": "True"})
    check("Emoji via UI fallback", "Noto Sans:charset=1f600", "Noto Color Emoji",
          {"color": "True", "embeddedbitmap": "True"})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active", action="store_true", help="Inspect active fonts; do not add candidate rules")
    parser.add_argument("--output", type=Path, help="Write the full JSON report")
    args = parser.parse_args()
    env = dict(os.environ)
    with tempfile.TemporaryDirectory(prefix="aven-font-audit-") as tmp:
        if not args.active:
            configs = sorted((ROOT / "fontconfig").glob("*.conf"))
            for source in configs:
                ET.parse(source)
            config = Path(tmp) / "fonts.conf"
            includes = [Path("/etc/fonts/fonts.conf"), *configs]
            config.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n'
                              '<fontconfig>\n' + ''.join(f'<include>{escape(str(p))}</include>\n' for p in includes)
                              + '</fontconfig>\n')
            env["FONTCONFIG_FILE"] = str(config)
        try:
            results = checks(env)
            report = {
                "schema_version": 1,
                "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "host": platform.platform(),
                "os_release": Path("/etc/os-release").read_text(),
                "scope": "active-environment" if args.active else "isolated-candidate-on-host",
                "fontconfig_version": subprocess.run(["fc-match", "--version"], env=env, text=True,
                                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                      check=True).stdout.strip(),
                "passed": all(r["passed"] for r in results),
                "visual_quality": "unassessed; font matching cannot demonstrate rendering quality",
                "checks": results,
            }
        except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
            parser.exit(2, f"Font audit could not run: {error}\n")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    passed = sum(r["passed"] for r in results)
    print(f"{report['scope']}: {passed}/{len(results)} font checks passed; visual quality unassessed.")
    for result in results:
        if not result["passed"]:
            print(result["label"] + ": " + "; ".join(result["errors"]), file=sys.stderr)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
