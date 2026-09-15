#!/usr/bin/env python3
"""Read-only installed ISO records or active user fonts; stream with python -B."""
import argparse
import base64
import configparser
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import subprocess


def file_record(path, contents=False):
    data = path.read_bytes()
    stat = path.stat()
    result = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
              "mtime_ns": stat.st_mtime_ns, "uid": stat.st_uid,
              "mode": oct(stat.st_mode & 0o777)}
    if contents:
        result["content_base64"] = base64.b64encode(data).decode()
    return result


def command(argv):
    result = subprocess.run(argv, text=True, capture_output=True, timeout=30)
    return {"argv": argv, "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["records", "fonts"])
    parser.add_argument("--user", default="reader")
    args = parser.parse_args()
    source = Path("/var/lib/aven/source")
    account = pwd.getpwnam(args.user)
    home = Path(account.pw_dir)
    report = {"schema_version": 1, "guest_collected_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "mode": args.mode, "user": args.user, "uid": os.getuid(), "home": str(home),
              "method": "Read-only Python stdin stream; no GUI, cache rebuilds or guest files written."}
    if args.mode == "records":
        paths = [Path("/var/lib/aven/installation.json"), Path("/var/log/aven-install.log"),
                 home / ".local/share/user-places.xbel"]
        paths += [home / ".local/state/aven" / name for name in
                  ["iso-seed-v1.json", "iso-layout-v1.json", "iso-seed.log", "iso-layout.log"]]
        paths += sorted((home / ".local/state/aven/places").glob("*.json"))
        report["files"] = {str(path): file_record(path, True) for path in paths}
        report["source_files"] = {str(path.relative_to(source)): file_record(path)
                                  for path in sorted(source.rglob("*"))
                                  if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"}
        report["installed_font_rules"] = {}
        for name in ["60-aven-families.conf", "99-aven-rendering.conf"]:
            active = file_record(Path("/etc/fonts/conf.d") / name)
            shipped = file_record(source / "typography/fontconfig" / name)
            report["installed_font_rules"][name] = {"active_sha256": active["sha256"],
                "source_sha256": shipped["sha256"], "matches_source": active["sha256"] == shipped["sha256"]}
        report["duplicate_flatpak_exports"] = {name: {"exists": path.exists(), "is_symlink": path.is_symlink()}
            for name in ["org.kde.gwenview", "org.kde.okular"]
            for path in [Path("/var/lib/flatpak/exports/share/applications") / (name + ".desktop")]}
        report["native_first_user_complete_marker"] = Path("/etc/plasma-setup-done").exists()
        report["rtc"] = command(["timedatectl", "show", "--property=Timezone,LocalRTC,NTPSynchronized,TimeUSec,RTCTimeUSec"])
        report["adjtime"] = Path("/etc/adjtime").read_text()
        report["failed_unit_journal"] = command(["journalctl", "-b", "-u", "mcelog.service", "-u", "systemd-remount-fs.service", "-u", "rpm-ostree-countme.service", "--no-pager", "-n", "80"])
        report["boot_id"] = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    else:
        if os.getuid() != account.pw_uid or Path.home() != home:
            raise RuntimeError("Active font and MIME audit must run as the actual desktop user")
        path = source / "typography/audit.py"
        scope = {"__file__": str(path), "__name__": "aven_read_only_active_font_checks"}
        exec(compile(path.read_bytes(), str(path), "exec"), scope)
        checks = scope["checks"](dict(os.environ))
        report.update(checks=checks, passed=all(item["passed"] for item in checks),
                      audit_source_sha256=file_record(path)["sha256"],
                      fontconfig_overrides={key: value for key, value in os.environ.items() if key.startswith("FONTCONFIG_")},
                      visual_quality=None)
        config = configparser.ConfigParser(interpolation=None)
        config.optionxform = str
        config.read(home / ".config/kdeglobals")
        report["plasma_font_values"] = {section: {key: value for key, value in config[section].items()
                if "font" in key.lower() or key.startswith("Xft")} for section in ["General", "WM"] if section in config}
        from gi.repository import Gio
        expected = {"org.mozilla.firefox.desktop": ["x-scheme-handler/http", "x-scheme-handler/https", "text/html"],
                    "net.thunderbird.Thunderbird.desktop": ["x-scheme-handler/mailto", "message/rfc822"],
                    "org.kde.gwenview.desktop": ["image/jpeg", "image/png", "image/webp", "image/avif", "image/tiff"],
                    "org.kde.okular.desktop": ["application/pdf"], "org.kde.dolphin.desktop": ["inode/directory"]}
        associations = []
        for desktop, mimes in expected.items():
            for mime in mimes:
                actual = Gio.AppInfo.get_default_for_type(mime, False)
                actual_id = actual.get_id() if actual else None
                associations.append({"mime": mime, "expected": desktop, "actual": actual_id, "passed": actual_id == desktop})
        report["default_associations"] = associations
        report["default_associations_passed"] = all(item["passed"] for item in associations)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
