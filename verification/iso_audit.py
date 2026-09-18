#!/usr/bin/env python3
"""Audit ISO structure/public Kickstart or a newly installed Atomic guest.

Static media checks do not establish firmware boot or installation success.
The installed command sends a read-only Python probe over explicit SSH settings.
"""
import argparse
import configparser
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import tempfile

from iso_deployment_probe import assess_cache_refs, expectation, load_expectation


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def logical_lines(text):
    pending = ""
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        pending += line
        if pending.endswith("\\"):
            pending = pending[:-1] + " "
            continue
        yield pending.strip()
        pending = ""
    if pending.strip():
        yield pending.strip()


def check_kickstart(text):
    """Reject concrete public-media disk/credential automation; no shell proof."""
    errors, ostreesetup = [], []
    section = None
    for line in logical_lines(text):
        if not line:
            continue
        first = line.split(None, 1)[0]
        if first == "%end":
            section = None
            continue
        if first in {"%include", "%ksappend"}:
            errors.append("External Kickstart include requires a separate expanded-content audit")
        if first.startswith("%"):
            section = first
        if section is None:
            if first in {"clearpart", "zerombr", "user", "sshkey", "autopart", "part", "partition", "raid", "volgroup", "logvol", "ignoredisk"}:
                errors.append("Public installer preselects disks, partitions, or credentials: " + first)
            if first == "rootpw" and shlex.split(line) != ["rootpw", "--lock"]:
                errors.append("Public installer defines a root credential")
            if first == "ostreesetup":
                ostreesetup.append(shlex.split(line))
        if re.search(r"\bNOPASSWD\b|\b(?:useradd|adduser|chpasswd)\b|authorized_keys|\bssh-(?:rsa|ed25519)\s+[A-Za-z0-9+/]{20,}|\b(?:AutoLogin|AutomaticLogin|Autologin)\b", line, re.I):
            errors.append("Public Kickstart contains account/key/passwordless-sudo/autologin provisioning")
    if len(ostreesetup) != 1:
        errors.append("Exactly one ostreesetup directive is required")
    return errors, ostreesetup[0] if len(ostreesetup) == 1 else []


def option(argv, name):
    for index, word in enumerate(argv):
        if word.startswith(name + "="):
            return word.split("=", 1)[1]
        if word == name and index + 1 < len(argv):
            return argv[index + 1]
    return None


def iso_path(value):
    path = PurePosixPath(value)
    if not value.startswith("/") or ".." in path.parts or value.startswith("//"):
        raise ValueError("Expected an absolute path inside the ISO")
    return str(path)


def run(argv, **kwargs):
    r = subprocess.run(argv, text=True, capture_output=True, timeout=90, **kwargs)
    if r.returncode != 0:
        raise ValueError("Command failed: " + shlex.join(argv) + "\n" + r.stderr[-1600:])
    return r


def media(args):
    manifest = json.loads(args.manifest.read_text())
    image = args.iso or args.manifest.parent / manifest["iso"]["file"]
    contract = load_expectation(args.manifest, getattr(args, "platform", None))
    expected = contract["ostree"]
    paths = manifest.get("paths", {})
    ks_path = iso_path(args.kickstart_path or paths["kickstart"])
    repo_path = iso_path(args.repo_path or paths["repo"])
    errors, facts = [], {}
    facts["expected"] = contract
    facts["iso"] = {"file": str(image), "bytes": image.stat().st_size, "sha256": sha(image)}
    if facts["iso"]["sha256"] != manifest["iso"]["sha256"]:
        errors.append("ISO SHA-256 differs from manifest")
    with image.open("rb") as stream:
        stream.seek(32768)
        if stream.read(7) != b"\x01CD001\x01":
            errors.append("Missing ISO9660 primary volume descriptor; a disk image is not an ISO")
    boot = run(["xorriso", "-indev", str(image), "-report_el_torito", "plain", "-report_system_area", "plain"])
    listing = boot.stdout + boot.stderr
    facts["boot_catalog"] = listing
    if not re.search(r"El Torito boot img\s*:\s*\d+\s+BIOS\s+y", listing):
        errors.append("Missing bootable BIOS El Torito entry")
    if not re.search(r"El Torito boot img\s*:\s*\d+\s+UEFI\s+y", listing):
        errors.append("Missing bootable UEFI El Torito entry")
    if "GPT" not in listing:
        errors.append("Missing hybrid GPT description")
    with tempfile.TemporaryDirectory(prefix="aven-iso-audit-") as temp:
        serial = 0
        def extract(path):
            nonlocal serial
            serial += 1
            target = Path(temp) / str(serial)
            run(["xorriso", "-osirrox", "on", "-indev", str(image), "-extract", iso_path(path), str(target)])
            return target.read_bytes()
        def extract_many(paths):
            nonlocal serial
            argv = ["xorriso", "-osirrox", "on", "-indev", str(image)]
            targets = {}
            for path in paths:
                serial += 1
                target = Path(temp) / str(serial)
                argv += ["-extract", iso_path(path), str(target)]
                targets[path] = target
            if targets:
                run(argv)
            return {path: target.read_bytes() for path, target in targets.items()}
        ks = extract(ks_path)
        ks_errors, setup = check_kickstart(ks.decode("utf-8"))
        errors.extend(ks_errors)
        facts["public_kickstart"] = {"path": ks_path, "sha256": hashlib.sha256(ks).hexdigest(), "safety_errors": ks_errors}
        if option(setup, "--url") != "file:///run/install/repo" + repo_path:
            errors.append("ostreesetup must use the ISO-mounted offline repository")
        if option(setup, "--osname") != "fedora":
            errors.append("ostreesetup stateroot must remain fedora")
        ref = option(setup, "--ref")
        if expected.get("installer_ref") and ref != expected["installer_ref"]:
            errors.append("Kickstart installer ref differs from the release contract")
        if not ref or ref.startswith("/") or ".." in PurePosixPath(ref).parts:
            errors.append("Invalid installer OSTree ref")
        else:
            resolved = extract(repo_path + "/refs/heads/" + ref).decode().strip()
            facts["installer_ref"] = {"ref": ref, "commit": resolved}
            if resolved != expected["layered_commit"]:
                errors.append("ISO installer ref does not select the tested layer")
        config = configparser.ConfigParser()
        config.read_string(extract(repo_path + "/config").decode())
        facts["repository_mode"] = config.get("core", "mode", fallback=None)
        if facts["repository_mode"] not in {"archive", "archive-z2"}:
            errors.append("Optical payload repository must use archive mode")
        facts["commit_objects"] = {}
        for kind, commit in [("layered", expected["layered_commit"]), ("base", expected["base_commit"])]:
            if not re.fullmatch(r"[0-9a-f]{64}", commit):
                raise ValueError("Invalid commit checksum in manifest")
            prefix = repo_path + "/objects/" + commit[:2] + "/" + commit[2:]
            raw = extract(prefix + ".commit")
            actual = hashlib.sha256(raw).hexdigest()
            facts["commit_objects"][kind] = actual
            if actual != commit:
                errors.append(kind + " commit object checksum differs")
            if kind == "base":
                metadata = extract(prefix + ".commitmeta")
                facts["base_detached_metadata_sha256"] = hashlib.sha256(metadata).hexdigest()
        cache_refs = expected["package_cache_refs"]
        if cache_refs:
            cache_dir = Path(temp) / "package-cache-refs"
            run(["xorriso", "-osirrox", "on", "-indev", str(image), "-extract",
                 repo_path + "/refs/heads/rpmostree/pkg", str(cache_dir)])
            cache = {}
            object_paths = set()
            for cache_ref in cache_refs:
                path = cache_dir / cache_ref.removeprefix("rpmostree/pkg/")
                checksum = path.read_text().strip() if path.is_file() and not path.is_symlink() else ""
                cache[cache_ref] = {"checksum": checksum}
                if re.fullmatch(r"[0-9a-f]{64}", checksum):
                    object_paths.add(repo_path + "/objects/" + checksum[:2] + "/" + checksum[2:] + ".commit")
            objects = extract_many(sorted(object_paths))
            for record in cache.values():
                checksum = record["checksum"]
                path = repo_path + "/objects/" + checksum[:2] + "/" + checksum[2:] + ".commit"
                if path in objects:
                    record["object_sha256"] = hashlib.sha256(objects[path]).hexdigest()
            errors.extend(assess_cache_refs(cache_refs, cache))
            facts["package_cache"] = cache
        facts["package_cache_refs_checked"] = len(cache_refs)
        for path in ["/boot/grub2/grub.cfg", "/EFI/BOOT/grub.cfg"]:
            config_text = extract(path).decode()
            if "inst.ks=" not in config_text or ks_path not in config_text:
                errors.append("Boot config does not reference public Aven Kickstart: " + path)
        if "source_manifest" in manifest:
            source_path = iso_path(paths["source"])
            source_dir = Path(temp) / "source"
            run(["xorriso", "-osirrox", "on", "-indev", str(image), "-extract", source_path, str(source_dir)])
            expected_files = set()
            for entry in manifest["source_manifest"]["files"]:
                relative = PurePosixPath(entry["path"])
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError("Source manifest contains an escaping path")
                file = source_dir / str(relative)
                if file.is_symlink() or not file.is_file() or sha(file) != entry["sha256"] or file.stat().st_size != entry["bytes"]:
                    errors.append("Embedded source hash/size mismatch: " + str(relative))
                expected_files.add(str(relative))
            actual_files = {str(file.relative_to(source_dir)) for file in source_dir.rglob("*") if file.is_file() or file.is_symlink()}
            if actual_files != expected_files:
                errors.append("Embedded source file inventory differs from the manifest")
            facts["source_files_checked"] = len(expected_files)
            embedded_platform = source_dir / "iso/platform.json"
            if embedded_platform.is_file() and expectation(json.loads(embedded_platform.read_text())) != contract:
                errors.append("Embedded platform differs from the release OSTree/profile contract")
    return {"manifest": str(args.manifest), "manifest_sha256": sha(args.manifest), "facts": facts,
            "static_media_checks_passed": not errors, "errors": errors, "iso_boot_install_accepted": None,
            "limitations": ["El Torito entries and ISO9660 structure do not prove firmware boot or a completed installation.", "Kickstart scanning detects explicit unsafe defaults; arbitrary invoked post-install scripts require source review.", "Commit-object hashes and detached-metadata presence do not validate all repository objects or the base signature. Run repository fsck and the installed probe.", "First-login Aven profile, network-free installation, screenshots and reboot remain separate required observations."]}


def installed(args):
    destination = args.ssh_host
    if destination.startswith("-") or any(c.isspace() for c in destination):
        raise ValueError("Invalid SSH destination")
    expected = load_expectation(args.manifest, args.platform, args.layer, args.base)
    remote = shlex.split(args.root_command) + [args.python, "-", "--expected-json", json.dumps(expected, separators=(",", ":"))]
    if args.profile_user:
        remote += ["--profile-user", args.profile_user]
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=accept-new",
           "-p", str(args.ssh_port)]
    if args.identity:
        ssh += ["-i", str(args.identity)]
    if args.known_hosts:
        ssh += ["-o", "UserKnownHostsFile=" + str(args.known_hosts)]
    ssh += [destination, shlex.join(remote)]
    probe = Path(__file__).with_name("iso_deployment_probe.py")
    r = subprocess.run(ssh, input=probe.read_text(), text=True, capture_output=True, timeout=180)
    result = {"ssh_destination": destination, "ssh_port": args.ssh_port, "probe_sha256": sha(probe),
              "exit_code": r.returncode, "stderr": r.stderr, "iso_boot_install_accepted": None}
    try:
        result["installed_system"] = json.loads(r.stdout)
    except json.JSONDecodeError:
        result["stdout"] = r.stdout
    result["installed_atomic_checks_passed"] = result.get("installed_system", {}).get("atomic_identity_passed") is True
    result["installed_desktop_checks_passed"] = result.get("installed_system", {}).get("desktop_startup_passed") is True
    profile_required = bool(expected["profile"] or args.profile_user)
    result["installed_first_login_checks_passed"] = result.get("installed_system", {}).get("first_login_passed")
    result["installed_checks_passed"] = (r.returncode == 0 and result["installed_atomic_checks_passed"]
        and result["installed_desktop_checks_passed"]
        and (not profile_required or result["installed_first_login_checks_passed"] is True))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("media")
    m.add_argument("--manifest", type=Path, required=True)
    m.add_argument("--platform", type=Path, help="Optional authoritative release platform to compare with the manifest")
    m.add_argument("--iso", type=Path)
    m.add_argument("--kickstart-path")
    m.add_argument("--repo-path")
    i = sub.add_parser("installed")
    i.add_argument("--ssh-host", required=True, help="Explicit user@host for the disposable installed guest")
    i.add_argument("--ssh-port", type=int, default=22)
    i.add_argument("--identity", type=Path)
    i.add_argument("--known-hosts", type=Path)
    i.add_argument("--root-command", default="sudo -n", help="Remote root execution prefix, or empty for root SSH")
    i.add_argument("--python", default="python3")
    i.add_argument("--manifest", type=Path)
    i.add_argument("--platform", type=Path)
    i.add_argument("--layer", help="Expected layer override; must agree with any manifest/platform")
    i.add_argument("--base", help="Expected base override; must agree with any manifest/platform")
    i.add_argument("--profile-user", help="Actual desktop user after the first Plasma login")
    for command in [m, i]:
        command.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = media(args) if args.command == "media" else installed(args)
    except (OSError, ValueError, KeyError, TypeError, configparser.Error, subprocess.SubprocessError) as error:
        result = {"errors": [str(error)], "iso_boot_install_accepted": None}
    result["schema_version"] = 1
    result["audited_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if result.get("static_media_checks_passed") or result.get("installed_checks_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
