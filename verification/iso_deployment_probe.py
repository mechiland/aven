#!/usr/bin/env python3
"""Read-only checks of an installed ISO's Atomic identity; no GUI or update calls.

Run as root in the newly installed guest, after its first reboot. Use an explicit
--manifest or --platform for newer releases, and --profile-user after that user's
first Plasma login. With no release file, the historical prototype remains the
default. This checks the deployed OS, not optical boot or visual quality.
"""
import argparse
import configparser
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import subprocess

LAYER = "37fc46fea2b1059cdbc35c4ff88a2b40ede7fcc105cca76693f11cc4cdffd551"
BASE = "be803f3e3bcdcc54885264702655e6e071864504154bc46044a08cc2aa2ce5df"
ORIGIN = "fedora:fedora/44/x86_64/kinoite"
PACKAGES = {"glibc-langpack-zh", "gwenview", "okular", "python3-pyside6", "thunderbird"}
DUPLICATE_FLATPAKS = {"org.kde.gwenview", "org.kde.okular"}
DESKTOP_PROBES = {"system_flatpak_apps", "display_manager", "default_target"}
SHA256 = re.compile(r"[0-9a-f]{64}")
PANEL_QUERY = """const result = []; for (const p of panels()) result.push({id:p.id,
location:p.location, alignment:p.alignment, height:p.height, lengthMode:p.lengthMode,
opacity:p.opacity, floating:p.floating}); print(JSON.stringify(result));"""


def expectation(document=None, layer=None, base=None):
    """Validate an explicit release contract, or retain the historical defaults."""
    if document is None:
        document = {"ostree": {"layered_commit": layer or LAYER, "base_commit": base or BASE,
                               "origin": ORIGIN, "requested_packages": sorted(PACKAGES)}}
    tree = document["ostree"]
    result = {"ostree": dict(tree), "profile": dict(document.get("profile", {}))}
    tree = result["ostree"]
    for key, override in [("layered_commit", layer), ("base_commit", base)]:
        if not isinstance(tree.get(key), str) or not SHA256.fullmatch(tree[key]):
            raise ValueError("Expected commits must be complete lowercase SHA-256 values")
        if override is not None and override != tree[key]:
            raise ValueError("Explicit commit differs from manifest/platform: " + key)
    if tree.get("origin") != ORIGIN:
        raise ValueError("Expected origin must retain the signed Fedora Kinoite update remote")
    for key in ["requested_packages", "requested_local_packages", "local_replacements", "package_cache_refs"]:
        values = tree.setdefault(key, [])
        if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
            raise ValueError("Expected a list of nonempty strings: " + key)
        if len(set(values)) != len(values):
            raise ValueError("Duplicate release entries: " + key)
    for value in tree["requested_local_packages"] + tree["local_replacements"]:
        if not re.fullmatch(r"[0-9a-f]{64}:[A-Za-z0-9+_.:-]+", value):
            raise ValueError("Local package origin requires checksum:NEVRA: " + value)
        nevra = value.split(":", 1)[1]
        pieces = nevra.rsplit("-", 2)
        if len(pieces) != 3 or not all(pieces):
            raise ValueError("Invalid local package NEVRA: " + nevra)
        name, version, release_arch = pieces
        # rpm-ostree's ref encoding doubles '_' and hex-escapes other symbols.
        encoded = "".join("__" if c == "_" else c if c.isalnum() or c in ".-" else f"_{ord(c):02X}"
                          for c in version + "-" + release_arch)
        ref = "rpmostree/pkg/" + name + "/" + encoded
        if ref not in tree["package_cache_refs"]:
            raise ValueError("Release omits local package cache ref: " + ref)
    for ref in tree["package_cache_refs"]:
        if not re.fullmatch(r"rpmostree/pkg/[A-Za-z0-9+_.-]+/[A-Za-z0-9_.-]+", ref) or ".." in ref:
            raise ValueError("Invalid package cache ref: " + ref)
    if tree.get("installer_ref") is not None and (
            not re.fullmatch(r"[A-Za-z0-9_./-]+", tree["installer_ref"])
            or tree["installer_ref"].startswith("/") or ".." in tree["installer_ref"]):
        raise ValueError("Invalid installer ref")
    if result["profile"].get("style") not in {None, "breeze", "union"}:
        raise ValueError("Unsupported release profile style")
    return result


def load_expectation(manifest=None, platform=None, layer=None, base=None):
    documents = [expectation(json.loads(Path(path).read_text()), layer, base)
                 for path in [manifest, platform] if path is not None]
    if not documents:
        return expectation(layer=layer, base=base)
    if len(documents) == 2 and documents[0] != documents[1]:
        raise ValueError("Manifest and platform OSTree/profile contracts differ")
    return documents[0]


def assess_cache_refs(expected, records):
    errors = []
    for ref in expected:
        record = records.get(ref, {})
        checksum = record.get("checksum", "")
        if not isinstance(checksum, str) or not SHA256.fullmatch(checksum):
            errors.append("Missing or unresolved package cache ref: " + ref)
        elif record.get("object_sha256") != checksum:
            errors.append("Missing or corrupt package cache commit object: " + ref)
    return errors


def collect_cache_refs(repo, expected):
    records = {}
    for ref in expected:
        resolved = command(["ostree", "--repo=" + str(repo), "rev-parse", ref])
        record = {"resolve": resolved}
        checksum = resolved.get("stdout", "").strip() if resolved.get("exit_code") == 0 else ""
        record["checksum"] = checksum
        if SHA256.fullmatch(checksum):
            path = Path(repo) / "objects" / checksum[:2] / (checksum[2:] + ".commit")
            try:
                record["object_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as error:
                record["error"] = str(error)
        records[ref] = record
    return records


def command(argv):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=60,
                           env=os.environ | {"LC_ALL": "C"})
        result = {"argv": argv, "exit_code": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
        if r.returncode == 0:
            try:
                result["json"] = json.loads(r.stdout)
            except json.JSONDecodeError:
                pass
        return result
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"argv": argv, "exit_code": None, "error": str(error)}


def assess(status, origin_text, layer=LAYER, base=BASE, expected=None):
    """Pure identity checks, also exercised with missing-base/wrong-origin cases."""
    tree = (expected or expectation(layer=layer, base=base))["ostree"]
    booted = [d for d in status.get("deployments", []) if d.get("booted") is True]
    errors = []
    if len(booted) != 1:
        return ["Exactly one booted deployment is required"]
    d = booted[0]
    for okay, error in [
        (d.get("checksum") == tree["layered_commit"], "Booted layered commit differs from expected commit"),
        (d.get("base-checksum") == tree["base_commit"], "Signed Fedora base is missing or differs"),
        (d.get("origin") == tree["origin"], "rpm-ostree origin differs from Fedora Kinoite"),
        (d.get("gpg-enabled") is True, "Fedora update GPG verification is disabled"),
        (d.get("unlocked") == "none", "Deployment is unlocked"),
        (d.get("layered-commit-meta", {}).get("rpmostree.clientlayer") is True, "Client layer metadata is absent"),
        (set(d.get("requested-packages", [])) == set(tree["requested_packages"]), "Requested application packages differ"),
        (set(d.get("requested-local-packages", [])) == {v.split(":", 1)[1] for v in tree["requested_local_packages"]},
         "Requested local packages differ"),
        (set(d.get("requested-base-local-replacements", [])) == {v.split(":", 1)[1] for v in tree["local_replacements"]},
         "Requested base local replacements differ"),
    ]:
        if not okay:
            errors.append(error)
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(origin_text)
        if parser.get("origin", "baserefspec", fallback=None) != tree["origin"]:
            errors.append("Origin file must use Fedora baserefspec")
        if parser.has_option("origin", "refspec"):
            errors.append("Plain refspec remains alongside layered baserefspec")
        requested = set(filter(None, parser.get("packages", "requested", fallback="").split(";")))
        if requested != set(tree["requested_packages"]):
            errors.append("Origin file lost requested package persistence")
        for section, key, field in [("packages", "requested-local", "requested_local_packages"),
                                    ("overrides", "replace-local", "local_replacements")]:
            actual = set(filter(None, parser.get(section, key, fallback="").split(";")))
            if actual != set(tree[field]):
                errors.append("Origin file checksum:NEVRA entries differ: " + section + "/" + key)
    except configparser.Error as error:
        errors.append("Invalid deployment origin: " + str(error))
    return errors


def assess_desktop(probes):
    """Verify public login startup and absence of the bundled system duplicates."""
    errors = []
    for name in DESKTOP_PROBES:
        if probes.get(name, {}).get("exit_code") != 0:
            errors.append(name + " command failed")
    installed = set(probes.get("system_flatpak_apps", {}).get("stdout", "").splitlines())
    duplicates = sorted(installed & DUPLICATE_FLATPAKS)
    if duplicates:
        errors.append("Bundled system Flatpak duplicates remain: " + ", ".join(duplicates))
    dm = dict(line.split("=", 1) for line in probes.get("display_manager", {}).get("stdout", "").splitlines() if "=" in line)
    if (dm.get("Id") != "plasmalogin.service" or dm.get("LoadState") != "loaded"
            or dm.get("ActiveState") != "active" or dm.get("UnitFileState") != "enabled"):
        errors.append("Native Plasma Login Manager is not loaded, active, and enabled as display-manager")
    if probes.get("default_target", {}).get("stdout", "").strip() != "graphical.target":
        errors.append("Default system target is not graphical.target")
    return errors


def assess_first_login(record, profile):
    """Require completion records plus current settings and a live Union dock."""
    errors = list(record.get("errors", []))
    for phase in ["seed", "layout"]:
        marker = record.get("markers", {}).get(phase, {})
        if (not isinstance(marker, dict) or marker.get("schema_version") != 1 or marker.get("phase") != phase
                or marker.get("home") != record.get("home") or not marker.get("completed_at")):
            errors.append("First-login " + phase + " completion marker is absent or invalid")
    if profile.get("style") == "union":
        settings = record.get("settings", {})
        for key, value in {"widgetStyle": "Union", "unionStyle": "aven-mist", "shellTheme": "aven-dock"}.items():
            if settings.get(key) != value:
                errors.append("First-login profile setting differs: " + key)
        if not record.get("union_assets_present"):
            errors.append("Installed Union/Dock profile assets are missing")
        panels = record.get("live_panels", {})
        if panels.get("exit_code") != 0 or not isinstance(panels.get("json"), list) or not panels["json"]:
            errors.append("A running user Plasma dock could not be queried")
        else:
            required = {"location": "bottom", "alignment": "center", "height": 58,
                        "lengthMode": "fit", "opacity": "translucent", "floating": True}
            for panel in panels["json"]:
                if not isinstance(panel, dict) or any(panel.get(k) != v for k, v in required.items()):
                    errors.append("Live Plasma panel does not match the Union dock layout")
    return errors


def collect_first_login(username):
    record = {"user": username, "markers": {}, "settings": {}, "errors": []}
    if not username:
        record["errors"].append("Explicit --profile-user is required to verify first-login completion")
        return record
    try:
        account = pwd.getpwnam(username)
        if not 1000 <= account.pw_uid < 60000:
            raise ValueError("First-login verification requires an actual desktop user")
        home = Path(account.pw_dir)
        record.update(uid=account.pw_uid, home=str(home))
        for phase in ["seed", "layout"]:
            path = home / ".local/state/aven" / ("iso-" + phase + "-v1.json")
            try:
                record["markers"][phase] = json.loads(path.read_text())
            except (OSError, ValueError) as error:
                record["errors"].append(str(error))
        for filename, section, mappings in [
            ("kdeglobals", "KDE", {"widgetStyle": "widgetStyle", "unionStyle": "unionStyle"}),
            ("plasmarc", "Theme", {"name": "shellTheme"})]:
            config = configparser.ConfigParser(interpolation=None, strict=False)
            config.optionxform = str
            config.read(home / ".config" / filename)
            for key, field in mappings.items():
                record["settings"][field] = config.get(section, key, fallback=None)
        record["union_assets_present"] = all((home / relative).is_file() for relative in [
            ".local/share/union/styles/aven-mist/metadata.json",
            ".local/share/union/styles/aven-mist/contents/css/controls.css",
            ".local/share/plasma/desktoptheme/aven-dock/metadata.json",
            ".local/share/plasma/desktoptheme/aven-dock/widgets/panel-background.svg"])
        dbus = shutil.which("qdbus6") or shutil.which("qdbus-qt6") or shutil.which("qdbus")
        if dbus:
            runtime = "/run/user/" + str(account.pw_uid)
            record["live_panels"] = command(["runuser", "-u", username, "--", "env",
                "XDG_RUNTIME_DIR=" + runtime, "DBUS_SESSION_BUS_ADDRESS=unix:path=" + runtime + "/bus",
                dbus, "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", PANEL_QUERY])
        else:
            record["errors"].append("Qt D-Bus client is unavailable")
    except (OSError, KeyError, ValueError, configparser.Error) as error:
        record["errors"].append(str(error))
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--expected-layer")
    p.add_argument("--expected-base")
    p.add_argument("--manifest", type=Path)
    p.add_argument("--platform", type=Path)
    p.add_argument("--expected-json", help=argparse.SUPPRESS)
    p.add_argument("--profile-user", help="Actual desktop user after the first Plasma login")
    args = p.parse_args()
    try:
        if args.expected_json:
            if args.manifest or args.platform:
                raise ValueError("Use release files or the streamed release contract, not both")
            expected = expectation(json.loads(args.expected_json), args.expected_layer, args.expected_base)
        else:
            expected = load_expectation(args.manifest, args.platform, args.expected_layer, args.expected_base)
    except (OSError, ValueError, KeyError, TypeError) as error:
        p.error(str(error))
    tree = expected["ostree"]
    layer, base = tree["layered_commit"], tree["base_commit"]
    if os.geteuid() != 0 or not Path("/run/ostree-booted").exists():
        p.error("Run as root inside the booted Atomic guest")
    repo = "/sysroot/ostree/repo"
    probes = {
        "atomic": command(["rpm-ostree", "status", "--json"]),
        "base_signature": command(["ostree", "--repo=" + repo, "show", "--gpg-verify-remote=fedora", base]),
        "layer_parent": command(["ostree", "--repo=" + repo, "rev-parse", layer + "^"]),
        "fedora_ref": command(["ostree", "--repo=" + repo, "rev-parse", tree["origin"]]),
        "selinux": command(["getenforce"]),
        "ostreed": command(["systemctl", "is-active", "rpm-ostreed"]),
        "root_mount": command(["findmnt", "--json", "--output", "TARGET,OPTIONS", "--target", "/"]),
        "failed_units": command(["systemctl", "--failed", "--no-legend", "--plain"]),
        "system_flatpak_apps": command(["flatpak", "list", "--system", "--app", "--columns=application"]),
        "display_manager": command(["systemctl", "show", "display-manager.service", "--property=Id,LoadState,ActiveState,UnitFileState"]),
        "default_target": command(["systemctl", "get-default"]),
    }
    status = probes["atomic"].get("json", {})
    booted = [d for d in status.get("deployments", []) if d.get("booted") is True]
    origin_text = ""
    origin_file = None
    if len(booted) == 1:
        d = booted[0]
        osname, checksum, serial = d.get("osname"), d.get("checksum"), d.get("serial")
        if osname == "fedora" and re.fullmatch(r"[0-9a-f]{64}", checksum or "") and type(serial) is int and serial >= 0:
            origin_file = Path(f"/sysroot/ostree/deploy/{osname}/deploy/{checksum}.{serial}.origin")
            if origin_file.is_file():
                origin_text = origin_file.read_text()
    errors = assess(status, origin_text, expected=expected)
    for name in probes:
        if name not in DESKTOP_PROBES and probes[name]["exit_code"] != 0:
            errors.append(name + " command failed")
    signature = probes["base_signature"]
    if "Good signature" not in signature.get("stdout", "") + signature.get("stderr", ""):
        errors.append("No verified Fedora base signature")
    for name in ["layer_parent", "fedora_ref"]:
        if probes[name].get("stdout", "").strip() != base:
            errors.append(name + " does not resolve to expected Fedora base")
    if probes["selinux"].get("stdout", "").strip() != "Enforcing":
        errors.append("SELinux is not enforcing")
    if probes["ostreed"].get("stdout", "").strip() != "active":
        errors.append("rpm-ostreed is not active")
    mounts = probes["root_mount"].get("json", {}).get("filesystems", [])
    if len(mounts) != 1 or "ro" not in mounts[0].get("options", "").split(","):
        errors.append("Root filesystem is not read-only")
    cache = collect_cache_refs(repo, tree["package_cache_refs"])
    cache_errors = assess_cache_refs(tree["package_cache_refs"], cache)
    errors.extend(cache_errors)
    atomic_errors = errors[:]
    desktop_errors = assess_desktop(probes)
    errors.extend(desktop_errors)
    profile = None
    profile_errors = []
    if expected["profile"] or args.profile_user:
        profile = collect_first_login(args.profile_user)
        profile_errors = assess_first_login(profile, expected["profile"])
        errors.extend(profile_errors)
    print(json.dumps({"schema_version": 1, "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "expected_layer": layer, "expected_base": base, "expected": expected,
        "origin_file": str(origin_file) if origin_file else None, "origin_text": origin_text,
        "origin_sha256": hashlib.sha256(origin_text.encode()).hexdigest() if origin_text else None,
        "probes": probes, "atomic_identity_passed": not atomic_errors,
        "desktop_startup_passed": not desktop_errors,
        "package_cache": cache, "package_cache_refs_checked": len(cache), "package_cache_passed": not cache_errors,
        "first_login": profile, "first_login_passed": not profile_errors if profile is not None else None,
        "errors": errors,
        "iso_boot_install_accepted": None,
        "limitations": ["Read-only deployment checks do not prove optical firmware boot, network-free installation, visual quality, or live rollback.", "First-login checks require an explicit desktop user and inspect completion records, selected Union/Dock settings, installed assets, and running Plasma panel properties; they do not prove every application's loaded style or visual appearance.", "Cache checks validate required refs and their commit-object hashes; full cached file-object integrity requires repository fsck.", "Failed units are recorded for comparison with the known baseline; they are not silently discarded.", "Duplicate Flatpak check covers system applications imported by Anaconda, not applications later installed in individual user accounts."]}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
