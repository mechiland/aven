"""Identify only the Atomic system entries safe to hide in native KDE Places.

No device is mounted, relabelled, or removed. Solid supplies the same identifiers
that KFilePlacesModel uses. Unknown, removable, hot-pluggable, and data-bearing
volumes remain visible. In particular Fedora's shared root/home Btrfs volume is
not treated as an immutable-only device.
"""

import json
import os
from pathlib import Path
import re
import subprocess

SYSTEM_MOUNTS = {"/", "/boot", "/boot/efi"}


def parse_solid(text):
    """Read known typed fields from the public solid-hardware6 diagnostic CLI."""
    devices = {}
    current = None
    for line in text.splitlines():
        match = re.fullmatch(r"udi = '(.*)'", line)
        if match:
            current = devices.setdefault(match[1], {})
        elif current is not None:
            match = re.fullmatch(r"  ([\w.]+) = '(.*)' \(string\)", line)
            if match:
                current[match[1]] = match[2]
            else:
                match = re.fullmatch(r"  ([\w.]+) = (true|false) \(bool\)", line)
                if match:
                    current[match[1]] = match[2] == "true"
    return devices


def flatten_mounts(document):
    mounts = []
    def visit(items):
        for item in items:
            mounts.append(item)
            visit(item.get("children", []))
    visit(document.get("filesystems", []))
    return mounts


def system_devices(devices, mount_document, atomic_booted):
    """Return positively identified immutable-root and fixed boot entries only."""
    if not atomic_booted:
        return []
    mounts = flatten_mounts(mount_document)
    by_target = {mount.get("target"): mount for mount in mounts}
    targets_by_device = {}
    for mount in mounts:
        # findmnt appends [btrfs/subvolume] to a block source.
        source = mount.get("source", "").split("[", 1)[0]
        targets_by_device.setdefault(source, set()).add(mount.get("target"))
    result = []
    for udi, device in devices.items():
        target = device.get("StorageAccess.filePath")
        mount = by_target.get(target)
        if target not in SYSTEM_MOUNTS or not mount or device.get("StorageAccess.accessible") is not True:
            continue
        root_overlay = (
            target == "/" and udi.startswith("/org/kde/fstab/")
            and mount.get("fstype") in {"overlay", "composefs"}
            and "ro" in mount.get("options", "").split(",")
            and not device.get("Block.device")
        )
        if not root_overlay:
            parent = devices.get(device.get("parent"), {})
            block = device.get("Block.device")
            if (
                device.get("Block.isSystem") is not True
                or parent.get("StorageDrive.removable") is not False
                or parent.get("StorageDrive.hotpluggable") is not False
                or not block or target not in targets_by_device.get(block, set())
                or not targets_by_device[block] <= SYSTEM_MOUNTS
            ):
                continue
            if target == "/" and "ro" not in mount.get("options", "").split(","):
                continue
        result.append({"udi": udi, "uuid": device.get("StorageVolume.uuid", ""), "mount": target,
                       "reason": "read-only Atomic root" if target == "/" else "fixed system boot volume"})
    return result


def discover_system_devices():
    if not Path("/run/ostree-booted").exists():
        return []
    environment = os.environ | {"LC_ALL": "C", "LANG": "C"}
    # Solid 6.30 main() returns hwList()'s bool directly: successful enumeration
    # exits 1. Validate the typed output as well, rather than assuming POSIX 0.
    solid = subprocess.run(["solid-hardware6", "list", "details"], text=True, capture_output=True, env=environment, timeout=10)
    if solid.returncode not in (0, 1) or not solid.stdout.startswith("udi = '"):
        raise RuntimeError("Solid did not return a usable device inventory")
    mounts = json.loads(subprocess.check_output(["findmnt", "--json", "--output", "SOURCE,TARGET,FSTYPE,OPTIONS"], text=True, env=environment, timeout=10))
    return system_devices(parse_solid(solid.stdout), mounts, True)


if __name__ == "__main__":
    # Read-only diagnosis; actual IsHidden defaults are applied by files/install.py.
    print(json.dumps(discover_system_devices(), ensure_ascii=False, indent=2))
