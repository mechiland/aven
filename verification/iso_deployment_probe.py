#!/usr/bin/env python3
"""Read-only checks of an installed ISO's Atomic identity; no GUI or update calls.

Run as root in the newly installed guest, after its first reboot. This checks
the deployed OS, not that firmware booted the ISO or that the desktop looks good.
"""
import argparse
import configparser
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

LAYER = "37fc46fea2b1059cdbc35c4ff88a2b40ede7fcc105cca76693f11cc4cdffd551"
BASE = "be803f3e3bcdcc54885264702655e6e071864504154bc46044a08cc2aa2ce5df"
ORIGIN = "fedora:fedora/44/x86_64/kinoite"
PACKAGES = {"glibc-langpack-zh", "gwenview", "okular", "python3-pyside6", "thunderbird"}


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


def assess(status, origin_text, layer=LAYER, base=BASE):
    """Pure identity checks, also exercised with missing-base/wrong-origin cases."""
    booted = [d for d in status.get("deployments", []) if d.get("booted") is True]
    errors = []
    if len(booted) != 1:
        return ["Exactly one booted deployment is required"]
    d = booted[0]
    for okay, error in [
        (d.get("checksum") == layer, "Booted layered commit differs from tested commit"),
        (d.get("base-checksum") == base, "Signed Fedora base is missing or differs"),
        (d.get("origin") == ORIGIN, "rpm-ostree origin differs from Fedora Kinoite"),
        (d.get("gpg-enabled") is True, "Fedora update GPG verification is disabled"),
        (d.get("unlocked") == "none", "Deployment is unlocked"),
        (d.get("layered-commit-meta", {}).get("rpmostree.clientlayer") is True, "Client layer metadata is absent"),
        (set(d.get("requested-packages", [])) == PACKAGES, "Requested application packages differ"),
    ]:
        if not okay:
            errors.append(error)
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(origin_text)
        if parser.get("origin", "baserefspec", fallback=None) != ORIGIN:
            errors.append("Origin file must use Fedora baserefspec")
        if parser.has_option("origin", "refspec"):
            errors.append("Plain refspec remains alongside layered baserefspec")
        requested = set(filter(None, parser.get("packages", "requested", fallback="").split(";")))
        if requested != PACKAGES:
            errors.append("Origin file lost requested package persistence")
    except configparser.Error as error:
        errors.append("Invalid deployment origin: " + str(error))
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--expected-layer", default=LAYER)
    p.add_argument("--expected-base", default=BASE)
    args = p.parse_args()
    if not all(re.fullmatch(r"[0-9a-f]{64}", x) for x in [args.expected_layer, args.expected_base]):
        p.error("Expected commits must be complete lowercase SHA-256 values")
    if os.geteuid() != 0 or not Path("/run/ostree-booted").exists():
        p.error("Run as root inside the booted Atomic guest")
    repo = "/sysroot/ostree/repo"
    probes = {
        "atomic": command(["rpm-ostree", "status", "--json"]),
        "base_signature": command(["ostree", "--repo=" + repo, "show", "--gpg-verify-remote=fedora", args.expected_base]),
        "layer_parent": command(["ostree", "--repo=" + repo, "rev-parse", args.expected_layer + "^"]),
        "fedora_ref": command(["ostree", "--repo=" + repo, "rev-parse", ORIGIN]),
        "selinux": command(["getenforce"]),
        "ostreed": command(["systemctl", "is-active", "rpm-ostreed"]),
        "root_mount": command(["findmnt", "--json", "--output", "TARGET,OPTIONS", "--target", "/"]),
        "failed_units": command(["systemctl", "--failed", "--no-legend", "--plain"]),
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
    errors = assess(status, origin_text, args.expected_layer, args.expected_base)
    for name in probes:
        if probes[name]["exit_code"] != 0:
            errors.append(name + " command failed")
    signature = probes["base_signature"]
    if "Good signature" not in signature.get("stdout", "") + signature.get("stderr", ""):
        errors.append("No verified Fedora base signature")
    for name in ["layer_parent", "fedora_ref"]:
        if probes[name].get("stdout", "").strip() != args.expected_base:
            errors.append(name + " does not resolve to tested Fedora base")
    if probes["selinux"].get("stdout", "").strip() != "Enforcing":
        errors.append("SELinux is not enforcing")
    if probes["ostreed"].get("stdout", "").strip() != "active":
        errors.append("rpm-ostreed is not active")
    mounts = probes["root_mount"].get("json", {}).get("filesystems", [])
    if len(mounts) != 1 or "ro" not in mounts[0].get("options", "").split(","):
        errors.append("Root filesystem is not read-only")
    print(json.dumps({"schema_version": 1, "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "expected_layer": args.expected_layer, "expected_base": args.expected_base,
        "origin_file": str(origin_file) if origin_file else None, "origin_text": origin_text,
        "origin_sha256": hashlib.sha256(origin_text.encode()).hexdigest() if origin_text else None,
        "probes": probes, "atomic_identity_passed": not errors, "errors": errors,
        "iso_boot_install_accepted": None,
        "limitations": ["Read-only deployment checks do not prove optical firmware boot, network-free installation, first-login profile completion, visual quality, or live rollback.", "Failed units are recorded for comparison with the known baseline; they are not silently discarded."]}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
