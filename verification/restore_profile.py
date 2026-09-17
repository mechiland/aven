#!/usr/bin/env python3
"""Snapshot or restore Aven's focused settings, retaining app profiles and data.

Restore/fonts default to a read-only plan; --apply executes that exact generated
plan after archiving current files. This never runs rpm-ostree, edits /usr, removes
packages, or opens/closes applications. Live user restoration requires logout.
"""
from __future__ import annotations

import argparse
import configparser
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import xml.etree.ElementTree as ET

SHARED = ["kdeglobals", "kwinrc", "plasmarc", "plasmashellrc", "plasma-org.kde.plasma.desktop-appletsrc", "kcminputrc", "breezerc", "gtk-3.0/settings.ini", "gtk-4.0/settings.ini", "gtk-3.0/colors.css", "gtk-3.0/gtk.css", "gtk-4.0/colors.css", "gtk-4.0/gtk.css"]
DEFAULTS = [".config/mimeapps.list", ".config/kde-mimeapps.list", ".local/share/applications/mimeapps.list"]
FILES = [".config/dolphinrc", ".local/share/kxmlgui5/dolphin/dolphinui.rc", ".local/share/dolphin/view_properties/global/.directory", "Documents/.directory", "Downloads/.directory", "Pictures/.directory", ".local/share/user-places.xbel", ".local/state/dolphinstaterc"]
HOOKS = [".local/bin/aven-browser", ".local/bin/aven-mail", ".local/bin/aven-preview", ".local/share/applications/aven-browser.desktop", ".local/share/applications/aven-mail.desktop", ".local/share/applications/org.mozilla.firefox.desktop", ".local/share/applications/net.thunderbird.Thunderbird.desktop", ".local/share/applications/org.aven.Preview.desktop", ".local/share/kio/servicemenus/aven-preview.desktop", ".config/aven/files-layout.json", ".local/share/aven/photos-profile.json"]
USER_PATHS = set([".config/" + name for name in SHARED] + DEFAULTS + FILES + HOOKS + [".config/gwenviewrc"])
# Theme updates reuse their native package IDs. Preserve the package bytes and
# compatibility launchers as well as the selected name, so appearance rollback
# restores the previous Union revision rather than loading the new assets.
UNION_PATHS = {
    '.local/bin/dolphin', '.local/bin/gwenview',
    '.local/libexec/aven-union/aven-files', '.local/libexec/aven-union/aven-photos',
    '.local/libexec/aven-union/dolphin-location.qss', '.local/libexec/aven-union/gwenview-surfaces.qss',
    '.local/share/applications/org.kde.dolphin.desktop', '.local/share/applications/org.kde.gwenview.desktop',
    '.local/share/applications/org.kde.gwenview_importer.desktop',
    '.local/share/dbus-1/services/org.kde.dolphin.FileManager1.service',
    '.config/systemd/user/plasma-dolphin.service.d/aven-union.conf',
}
_source_root = Path(__file__).resolve().parents[1]
for _source, _target in (
    ('visual/union/aven-mist', '.local/share/union/styles/aven-mist'),
    ('visual/aurorae/Aven', '.local/share/aurorae/themes/Aven'),
    ('visual/plasma/aven-dock', '.local/share/plasma/desktoptheme/aven-dock'),
    ('visual/icons/Aven', '.local/share/icons/Aven'),
    ('visual/color-schemes', '.local/share/color-schemes'),
):
    UNION_PATHS.update(str(Path(_target) / path.relative_to(_source_root/_source))
                       for path in (_source_root/_source).rglob('*') if path.is_file())
UNION_PATHS.add('.local/share/union/styles/aven-mist/contents/css/tokens.css')
USER_PATHS.update(UNION_PATHS)
FONT_PATHS = {"etc/fonts/conf.d/60-aven-families.conf", "etc/fonts/conf.d/99-aven-rendering.conf"}
MIMES = {"x-scheme-handler/http", "x-scheme-handler/https", "text/html", "x-scheme-handler/mailto", "message/rfc822", "image/jpeg", "image/png", "image/webp", "image/avif", "image/tiff", "application/pdf", "inode/directory"}
PLACES = ".local/share/user-places.xbel"
KDE_OWNER = "http://www.kde.org"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked(root, relative):
    path = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"Invalid relative path: {relative}")
    for parent in path.parents:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError(f"Refusing symlink parent: {parent}")
    return path


def state(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return {"kind": "absent"}
    if stat.S_ISLNK(info.st_mode):
        return {"kind": "symlink", "target": os.readlink(path)}
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"Expected a regular file or symlink: {path}")
    return {"kind": "file", "sha256": sha(path.read_bytes()), "mode": stat.S_IMODE(info.st_mode) & 0o777}


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def snapshot(root, destination, relatives, root_kind="home"):
    if destination.exists() or destination.is_symlink():
        raise ValueError("Snapshot destination already exists; snapshots are never overwritten")
    # Preflight all sources before creating the snapshot directory.
    entries = {rel: state(checked(root, rel)) for rel in sorted(relatives)}
    destination.mkdir(parents=True, mode=0o700)
    manifest = {"schema_version": 1, "scope": "aven-focused-profile", "root_kind": root_kind,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "entries": entries}
    for rel, item in entries.items():
        if item["kind"] == "file":
            dest = destination / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(checked(root, rel), dest)
            dest.chmod(0o600)
            if sha(dest.read_bytes()) != item["sha256"]:
                raise ValueError(f"Source changed during snapshot: {rel}")
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def merge_mime(current, original):
    def read(data):
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        parser.read_string(data.decode("utf-8") if data else "")
        return parser
    target, source = read(current), read(original)
    for section in ["Default Applications", "Added Associations", "Removed Associations"]:
        for key in MIMES:
            if source.has_option(section, key):
                if not target.has_section(section):
                    target.add_section(section)
                target.set(section, key, source.get(section, key))
            elif target.has_section(section):
                target.remove_option(section, key)
        if target.has_section(section) and not list(target.items(section)):
            target.remove_section(section)
    if not target.sections() and not target.defaults():
        return None
    text = io.StringIO()
    target.write(text, space_around_delimiters=False)
    return text.getvalue().encode("utf-8")


def load_places_records(paths):
    """Read explicit immutable installer records, never infer device ownership."""
    changes, sources = [], []
    for path in paths:
        path = path.expanduser().absolute()
        if path.suffix != ".json" or path.is_symlink() or not path.is_file():
            raise ValueError("Places ownership record must be a committed regular .json file")
        raw = path.read_bytes()
        record = json.loads(raw)
        if (not isinstance(record, dict) or record.get("schema_version") != 1 or record.get("component") != "aven-places"
                or record.get("target") != PLACES or not isinstance(record.get("changes"), list)):
            raise ValueError("Places ownership record has the wrong schema or scope")
        for change in record["changes"]:
            if not isinstance(change, dict):
                raise ValueError("Malformed Places change record")
            if change.get("kind") != "system-device":
                continue
            identity, previous = change.get("identifiers", {}), change.get("previous_is_hidden", {})
            if (not isinstance(identity, dict) or not isinstance(identity.get("udi"), str) or not identity["udi"].startswith("/")
                    or not isinstance(identity.get("uuid"), str)
                    or previous != {"present": False, "value": None}
                    or change.get("applied_is_hidden") != "true"
                    or type(change.get("entry_created")) is not bool):
                raise ValueError("Unsupported or malformed Places device transition")
            if change not in changes:
                changes.append(change)
        sources.append({"path": str(path), "sha256": sha(raw)})
    return changes, sources


def device_metadata(tree, identity):
    matches = []
    for entry in tree:
        for metadata in entry.findall("info/metadata"):
            if metadata.get("owner") != KDE_OWNER or metadata.findtext("isSystemItem") != "true":
                continue
            # Never fall back to a reused kernel UDI when a stable UUID is known.
            matches_identity = (metadata.findtext("uuid") == identity["uuid"] if identity["uuid"]
                                else not metadata.findtext("uuid") and metadata.findtext("UDI") == identity["udi"])
            if matches_identity:
                matches.append(metadata)
    return matches


def merge_places(current, original, device_changes=(), unresolved=None):
    unresolved = [] if unresolved is None else unresolved
    target, source = ET.fromstring(current), ET.fromstring(original)
    originals = {}
    for bookmark in source.findall("bookmark"):
        if bookmark.findtext("title") not in {"Desktop", "Music", "Videos", "Recent Locations"}:
            continue
        metadata = next((m for m in bookmark.findall("info/metadata") if m.get("owner") == KDE_OWNER and m.findtext("isSystemItem") == "true"), None)
        if metadata is not None:
            originals[bookmark.get("href")] = metadata.findtext("IsHidden")
    for bookmark in target.findall("bookmark"):
        href = bookmark.get("href")
        if href not in originals:
            continue
        metadata = next((m for m in bookmark.findall("info/metadata") if m.get("owner") == KDE_OWNER and m.findtext("isSystemItem") == "true"), None)
        if metadata is None:
            continue
        flag = metadata.find("IsHidden")
        # An explicit later Show choice belongs to the user, including for the
        # four ordinary defaults. Do not replace it with an older hidden state.
        if flag is not None and flag.text == "false":
            continue
        if originals[href] is None:
            if flag is not None:
                metadata.remove(flag)
        else:
            if flag is None:
                flag = ET.SubElement(metadata, "IsHidden")
            flag.text = originals[href]
    for change in device_changes:
        identity = change["identifiers"]
        matches, previous = device_metadata(target, identity), device_metadata(source, identity)
        if len(matches) > 1 or len(previous) > 1:
            unresolved.append(f"{PLACES}: ambiguous recorded device {identity}; retained")
            continue
        if not matches:
            continue
        metadata = matches[0]
        flags = metadata.findall("IsHidden")
        if len(flags) > 1:
            unresolved.append(f"{PLACES}: duplicate visibility flags for {identity}; retained")
            continue
        if not flags or flags[0].text != change["applied_is_hidden"]:
            continue  # A later explicit Show choice or removed entry is retained.
        original_flag = previous[0].find("IsHidden") if previous else None
        if original_flag is None:
            metadata.remove(flags[0])
        else:
            flags[0].text = original_flag.text
        # Keep native entry metadata and any subsequently added custom content.
    return ET.tostring(target, encoding="utf-8", xml_declaration=True)


def load_snapshot(directory, allowed, root_kind="home"):
    manifest_path = directory / "manifest.json"
    if manifest_path.is_symlink():
        raise ValueError("Refusing symlink manifest")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != 1 or manifest.get("scope") != "aven-focused-profile" or manifest.get("root_kind") != root_kind:
        raise ValueError("Snapshot has the wrong scope/root type")
    originals = {}
    for rel, item in manifest["entries"].items():
        if rel not in allowed:
            raise ValueError(f"Snapshot path outside focused allowlist: {rel}")
        item = dict(item)
        if item.get("kind") == "file":
            if type(item.get("mode")) is not int or not 0 <= item["mode"] <= 0o777:
                raise ValueError(f"Invalid saved file mode: {rel}")
            source = checked(directory, rel)
            if source.is_symlink() or not source.is_file():
                raise ValueError(f"Backup missing or symlink: {source}")
            item["data"] = source.read_bytes()
            if sha(item["data"]) != item.get("sha256"):
                raise ValueError(f"Backup hash mismatch: {source}")
        elif item.get("kind") == "symlink":
            if not isinstance(item.get("target"), str) or not item["target"] or "\x00" in item["target"]:
                raise ValueError(f"Invalid saved symlink: {rel}")
        elif item.get("kind") != "absent":
            raise ValueError(f"Invalid backup kind: {rel}")
        originals[rel] = item
    journal_path = directory / "restore-result.json"
    if root_kind == "home" and PLACES in originals and journal_path.is_file():
        if journal_path.is_symlink():
            raise ValueError("Refusing symlink restore journal")
        journal = json.loads(journal_path.read_text())
        if PLACES in journal.get("completed", []) and journal.get("places_after_sha256"):
            originals[PLACES]["undo_expected_sha256"] = journal["places_after_sha256"]
    return originals


def legacy_manifest(directory, prefix, allowed, unresolved):
    data = json.loads((directory / "manifest.json").read_text())
    originals = {}
    names = data.get("backed_up", [])
    absent = data.get("absent", [])
    expected_scope = "shared-config" if prefix == ".config/" else "profile-defaults"
    if data.get("scope", expected_scope) != expected_scope:
        raise ValueError("Legacy manifest has the wrong scope")
    if not isinstance(names, list) or not isinstance(absent, list) or not isinstance(data.get("sha256", {}), dict) or not all(isinstance(n, str) for n in names + absent):
        raise ValueError("Malformed legacy manifest")
    for name in names + absent:
        rel = prefix + name
        if rel not in allowed:
            raise ValueError(f"Legacy backup path outside scope: {rel}")
        if name in names and name in absent:
            raise ValueError(f"Conflicting original states: {name}")
        if name in absent:
            originals[rel] = {"kind": "absent"}
            continue
        source = checked(directory, name)
        if not source.exists():
            unresolved.append(f"{rel}: old manifest lists a nonexistent backup; original absence cannot be inferred")
            continue
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Refusing nonregular legacy backup: {source}")
        raw = source.read_bytes()
        expected = data.get("sha256", {}).get(name)
        if expected is not None and sha(raw) != expected:
            raise ValueError(f"Legacy backup hash mismatch: {source}")
        originals[rel] = {"kind": "file", "data": raw, "mode": source.stat().st_mode & 0o777, "sha256": sha(raw)}
    return originals


def plan(root, originals, unresolved, device_changes=()):
    operations = []
    for rel, original in sorted(originals.items()):
        current_path = checked(root, rel)
        before = state(current_path)
        desired = dict(original)
        undo_expected = desired.pop("undo_expected_sha256", None)
        if rel in DEFAULTS and before["kind"] == "file" and original["kind"] in ["file", "absent"]:
            data = merge_mime(current_path.read_bytes(), original.get("data", b""))
            desired = {"kind": "file", "data": data, "sha256": sha(data), "mode": before["mode"]} if data is not None else {"kind": "absent"}
        elif rel == PLACES and before["kind"] == "file":
            if original["kind"] == "absent":
                unresolved.append(f"{rel}: originally absent; retaining subsequently created bookmarks")
                continue
            if original["kind"] == "file":
                if undo_expected and before.get("sha256") == undo_expected:
                    # An unchanged post-restore XBEL can be undone byte exactly.
                    # If bookmarks changed meanwhile, never overwrite them.
                    data = original["data"]
                else:
                    if undo_expected:
                        unresolved.append(f"{rel}: changed after restore; device-flag undo retained for manual review")
                    data = merge_places(current_path.read_bytes(), original["data"], device_changes, unresolved)
                desired = {"kind": "file", "data": data, "sha256": sha(data), "mode": before["mode"]}
        public_desired = {k: v for k, v in desired.items() if k != "data"}
        if before == public_desired:
            continue
        operations.append({"path": rel, "before": before, "after": public_desired, "data": desired.get("data")})
    return operations


def stopped_desktop(home):
    names = {"plasmashell", "kwin_wayland", "kwin_x11", "dolphin", "gwenview", "firefox", "thunderbird"}
    active = set()
    for process in Path("/proc").glob("[0-9]*"):
        try:
            if process.stat().st_uid == os.getuid():
                name = (process / "comm").read_text().strip()
                if name in names:
                    environment = (process / "environ").read_bytes().split(b"\0")
                    process_homes = [os.fsdecode(value[5:]) for value in environment if value.startswith(b"HOME=")]
                    if any(Path(value).resolve() == home for value in process_homes):
                        active.add(name)
        except (OSError, ProcessLookupError):
            pass
    if active:
        raise ValueError("Log out of the desktop and close these applications before restore: " + ", ".join(sorted(active)))


def apply_plan(root, operations, archive, root_kind="home"):
    for operation in operations:
        if state(checked(root, operation["path"])) != operation["before"]:
            raise ValueError("Files changed after planning; re-run the plan")
    snapshot(root, archive, [op["path"] for op in operations], root_kind)
    journal = archive / "restore-result.json"
    result = {"completed": [], "complete": False}
    places_operation = next((op for op in operations if op["path"] == PLACES), None)
    if places_operation and places_operation["after"]["kind"] == "file":
        result["places_after_sha256"] = places_operation["after"]["sha256"]
    journal.write_text(json.dumps(result, indent=2) + "\n")
    try:
        for operation in operations:
            dest = checked(root, operation["path"])
            if state(dest) != operation["before"]:
                raise ValueError(f"File changed before restoration: {dest}")
            desired = operation["after"]
            if desired["kind"] == "absent":
                dest.unlink(missing_ok=True)  # removes only this leaf, never its symlink target
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as output:
                    temporary = Path(output.name)
                    if desired["kind"] == "file":
                        output.write(operation["data"])
                        output.flush()
                        os.fsync(output.fileno())
                try:
                    if desired["kind"] == "symlink":
                        temporary.unlink()
                        temporary.symlink_to(desired["target"])
                    else:
                        temporary.chmod(desired.get("mode", 0o600))
                    temporary.replace(dest)
                finally:
                    temporary.unlink(missing_ok=True)
            if state(dest) != desired:
                raise ValueError(f"Post-restore verification failed: {dest}")
            result["completed"].append(operation["path"])
            journal.write_text(json.dumps(result, indent=2) + "\n")
        result["complete"] = True
    finally:
        journal.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    take = sub.add_parser("snapshot", help="Record actual/absent states before a future Aven install")
    take.add_argument("--home", type=Path, required=True)
    take.add_argument("--output", type=Path)
    restore = sub.add_parser("restore", help="Plan restoration of one explicitly chosen snapshot or legacy backup set")
    restore.add_argument("--home", type=Path, required=True)
    restore.add_argument("--snapshot", type=Path)
    restore.add_argument("--shared-backup", type=Path)
    restore.add_argument("--defaults-backup", type=Path)
    restore.add_argument("--photos-backup", type=Path)
    restore.add_argument("--places-record", type=Path, action="append", default=[],
                         help="Explicit immutable aven-places installation record; repeat for actual changes")
    restore.add_argument("--apply", action="store_true")
    fonts = sub.add_parser("fonts", help="Plan removal of Aven-owned font rules, or restore explicit saved files")
    fonts.add_argument("--root", type=Path, required=True)
    fonts.add_argument("--backup", action="append", default=[], metavar="NAME=PATH")
    fonts.add_argument("--snapshot", type=Path, help="Undo a previous font restore from its recovery archive")
    fonts.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    unresolved, warnings = [], []
    device_changes, places_sources = [], []
    try:
        if args.command in ["snapshot", "restore"]:
            root = args.home.expanduser().resolve()
            if not root.is_dir() or root.stat().st_uid != os.getuid():
                raise ValueError("--home must be an existing directory owned by the current user")
            if args.command == "snapshot":
                destination = args.output.expanduser().resolve() if args.output else root / ".local/state/aven" / ("focused-before-" + timestamp())
                if not destination.is_relative_to(root / ".local/state/aven"):
                    raise ValueError("User snapshot must be under the selected home's .local/state/aven")
                checked(root, str(destination.relative_to(root)))
                manifest = snapshot(root, destination, USER_PATHS)
                print(json.dumps({"snapshot": str(destination), "entries": len(manifest["entries"]), "scope": manifest["scope"]}, indent=2))
                return 0
            if args.snapshot and any([args.shared_backup, args.defaults_backup, args.photos_backup]):
                raise ValueError("Use one complete snapshot or the legacy backup options, not both")
            device_changes, places_sources = load_places_records(args.places_record)
            if not device_changes:
                warnings.append("No actual-change Places device records selected; hidden device flags are retained. Older round-3 device changes have no durable ownership record.")
            originals = {}
            if args.snapshot:
                originals = load_snapshot(args.snapshot.expanduser().resolve(), USER_PATHS)
            else:
                if not any([args.shared_backup, args.defaults_backup, args.photos_backup]):
                    raise ValueError("Choose --snapshot or an explicit legacy backup")
                if args.shared_backup:
                    originals.update(legacy_manifest(args.shared_backup.expanduser().resolve(), ".config/", USER_PATHS, unresolved))
                if args.defaults_backup:
                    originals.update(legacy_manifest(args.defaults_backup.expanduser().resolve(), "", set(DEFAULTS), unresolved))
                for rel in FILES:
                    backup = checked(root, rel + ".pre-aven")
                    if backup.is_file() and not backup.is_symlink():
                        raw = backup.read_bytes()
                        originals[rel] = {"kind": "file", "data": raw, "sha256": sha(raw), "mode": backup.stat().st_mode & 0o777}
                    elif checked(root, rel).exists():
                        unresolved.append(f"{rel}: no original-state record; retained")
                if args.photos_backup:
                    raw_backup = args.photos_backup.expanduser().absolute()
                    backup = raw_backup.resolve()
                    if raw_backup.is_symlink() or backup.parent != root / ".config" or not backup.name.startswith("gwenviewrc.pre-aven-"):
                        raise ValueError("--photos-backup must be an explicit gwenviewrc.pre-aven-* file in the selected home")
                    raw = backup.read_bytes()
                    originals[".config/gwenviewrc"] = {"kind": "file", "data": raw, "sha256": sha(raw), "mode": backup.stat().st_mode & 0o777}
                elif (root / ".config/gwenviewrc").exists():
                    unresolved.append(".config/gwenviewrc: choose an explicit photo backup; retained")
                for rel in HOOKS:
                    if state(checked(root, rel))["kind"] != "absent":
                        unresolved.append(f"{rel}: legacy backups do not record original state; retained")
                warnings.append("Legacy Files/photo backups have no recorded source hashes or absent states. Unrecorded hooks/markers remain installed.")
            root_kind = "home"
            archive = root / ".local/state/aven/restores" / timestamp()
        else:
            root = args.root.expanduser().resolve()
            if not root.is_dir():
                raise ValueError("--root must be an existing system/image root")
            if root == Path("/") and (os.getuid() != 0 or not Path("/run/ostree-booted").exists()):
                raise ValueError("Live font restoration is limited to root inside the intended Atomic guest")
            root_kind = "system-fonts"
            archive = root / "var/lib/aven/font-restores" / timestamp()
            originals = load_snapshot(args.snapshot.expanduser().resolve(), FONT_PATHS, root_kind) if args.snapshot else {}
            if args.snapshot and args.backup:
                raise ValueError("Use --snapshot or --backup, not both")
            chosen = {}
            for value in args.backup:
                name, separator, file = value.partition("=")
                rel = "etc/fonts/conf.d/" + name
                if not separator or rel not in FONT_PATHS or rel in chosen:
                    raise ValueError("--backup requires each allowlisted font filename once, followed by =PATH")
                chosen[rel] = Path(file).expanduser().absolute()
            if not args.snapshot:
                for rel in sorted(FONT_PATHS):
                    current = checked(root, rel)
                    if rel in chosen:
                        backup = chosen[rel]
                        if backup.is_symlink() or not backup.is_file():
                            raise ValueError("Font backup must be a regular file")
                        raw = backup.read_bytes()
                        ET.fromstring(raw)
                        originals[rel] = {"kind": "file", "data": raw, "sha256": sha(raw), "mode": 0o644}
                    elif state(current)["kind"] == "file":
                        description = ET.fromstring(current.read_bytes()).findtext("description", "")
                        if not description.startswith("Aven:"):
                            unresolved.append(f"{rel}: not recognized as Aven-owned; retained")
                        else:
                            originals[rel] = {"kind": "absent"}
                    elif state(current)["kind"] != "absent":
                        unresolved.append(f"{rel}: not a regular Aven rule; retained")
                warnings.append("Removing Aven-owned rules disables this layer; it does not infer any pre-install font-file contents. Use --backup for a known prior file.")
        operations = plan(root, originals, unresolved, device_changes)
        report = {"command": args.command, "mode": "apply" if args.apply else "plan", "root": str(root),
                  "operations": [{k: v for k, v in op.items() if k != "data"} for op in operations],
                  "unresolved": unresolved, "warnings": warnings, "scope_complete": not unresolved,
                  "places_ownership_records": places_sources,
                  "application_profiles_retained": True, "atomic_deployment_changed": False}
        if args.apply and operations:
            if root_kind == "home":
                stopped_desktop(root)
            checked(root, str(archive.relative_to(root)))
            report["undo_archive"] = str(archive)
            report["result"] = apply_plan(root, operations, archive, root_kind)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2 if unresolved else 0
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError, configparser.Error) as error:
        print(json.dumps({"ok": False, "error": str(error), "command": args.command}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
