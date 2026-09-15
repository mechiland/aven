"""Hide a few default Places entries using KDE's normal XBEL metadata.

Bookmarks and their URLs remain in place. KDE's Show Hidden Places command can
reveal them. The only device defaults are positively identified Atomic system
entries; removable devices, user volumes and explicit visibility choices remain.
"""

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET

from system_places import discover_system_devices

KDE_OWNER = "http://www.kde.org"
HIDDEN_SYSTEM_ITEMS = {"Desktop", "Music", "Videos", "Recent Locations"}
PLACES_TARGET = ".local/share/user-places.xbel"


def _atomic_write(target, data, mode):
    descriptor, temporary = tempfile.mkstemp(prefix=".aven-places-", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), mode)
        os.replace(temporary, target)
        descriptor = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _commit_places(home, target, before, after, changes):
    """Publish one immutable ownership record only after the XBEL change succeeds.

    Prepare and sync the record before changing XBEL. A failed publish rolls
    back our exact written bytes. An interrupted process can leave a .pending
    file; it is deliberately not a restore ownership record or auto-promoted.
    """
    directory = home / ".local/state/aven/places"
    directory.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    name = now.strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid.uuid4().hex[:12]
    pending = directory / (name + ".pending")
    record = directory / (name + ".json")
    payload = {
        "schema_version": 1, "component": "aven-places", "created_at": now.isoformat(),
        "target": PLACES_TARGET,
        "before_sha256": hashlib.sha256(before).hexdigest(),
        "after_sha256": hashlib.sha256(after).hexdigest(), "changes": changes,
    }
    descriptor = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    mode = stat.S_IMODE(target.stat().st_mode)
    published = False
    try:
        if target.read_bytes() != before:
            raise RuntimeError("Places changed during installation; close Dolphin and retry")
        _atomic_write(target, after, mode)
        # Hard-link publication is atomic and refuses to overwrite a record.
        os.link(pending, record)
        published = True
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except BaseException:
        if target.read_bytes() == after:
            _atomic_write(target, before, mode)
        if published:
            record.unlink()
        raise
    finally:
        pending.unlink(missing_ok=True)
    return str(record)


def configure_places(home: Path, system_devices=None):
    target = home / PLACES_TARGET
    if not target.exists():
        return {"changed": False, "reason": "native Places list not initialized yet"}
    if target.is_symlink():
        raise ValueError("Refusing to replace a symlinked Places file")
    before = target.read_bytes()
    tree = ET.ElementTree(ET.fromstring(before))
    hidden = []
    changes = []
    for bookmark in tree.getroot().findall("bookmark"):
        metadata = next((node for node in bookmark.findall("info/metadata") if node.get("owner") == KDE_OWNER), None)
        title = bookmark.findtext("title")
        if metadata is None or metadata.findtext("isSystemItem") != "true" or title not in HIDDEN_SYSTEM_ITEMS:
            continue
        flag = metadata.find("IsHidden")
        if flag is not None:
            # Existing flags include an explicit choice to show this bookmark.
            continue
        changes.append({"kind": "system-bookmark", "identifiers": {
            "href": bookmark.get("href"), "title": title, "id": metadata.findtext("ID")},
            "previous_is_hidden": {"present": False, "value": None},
            "applied_is_hidden": "true", "entry_created": False})
        flag = ET.SubElement(metadata, "IsHidden")
        flag.text = "true"
        hidden.append(title)
    discovery_error = None
    if system_devices is None:
        try:
            system_devices = discover_system_devices()
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            # A missing inventory must never turn into a broad hide-devices rule.
            system_devices = []
            discovery_error = str(error)
    hidden_devices = []
    for device in system_devices:
        metadata = None
        for entry in tree.getroot():
            candidate = next((node for node in entry.findall("info/metadata") if node.get("owner") == KDE_OWNER), None)
            if candidate is None or not candidate.findtext("UDI"):
                continue
            # Match KFilePlacesModel: a known UUID takes precedence over a UDI,
            # which the kernel may reuse for a different disk after reboot.
            candidate_uuid = candidate.findtext("uuid")
            matches = candidate_uuid == device["uuid"] if candidate_uuid and device["uuid"] else candidate.findtext("UDI") == device["udi"]
            if matches:
                metadata = candidate
                break
        if metadata is not None and metadata.find("IsHidden") is not None:
            # Native explicit false means the user chose to show this device.
            continue
        entry_created = metadata is None
        if entry_created:
            # KFilePlacesItem::createDeviceBookmark uses an XBEL separator with
            # UDI/isSystemItem/uuid metadata, rather than a URL bookmark.
            entry = ET.SubElement(tree.getroot(), "separator")
            metadata = ET.SubElement(ET.SubElement(entry, "info"), "metadata", owner=KDE_OWNER)
            ET.SubElement(metadata, "UDI").text = device["udi"]
            ET.SubElement(metadata, "isSystemItem").text = "true"
            if device["uuid"]:
                ET.SubElement(metadata, "uuid").text = device["uuid"]
        changes.append({"kind": "system-device", "identifiers": {
            "udi": metadata.findtext("UDI"), "uuid": metadata.findtext("uuid") or ""},
            "previous_is_hidden": {"present": False, "value": None},
            "applied_is_hidden": "true", "entry_created": entry_created})
        ET.SubElement(metadata, "IsHidden").text = "true"
        hidden_devices.append(device)
    ownership_record = None
    if changes:
        saved = target.with_name(target.name + ".pre-aven")
        if not saved.exists():
            shutil.copy2(target, saved)
        # Preserve standard namespace names for readability, though URI is what
        # the XBEL reader uses. Unknown metadata is retained by ElementTree.
        ET.register_namespace("bookmark", "http://www.freedesktop.org/standards/desktop-bookmarks")
        ET.register_namespace("mime", "http://www.freedesktop.org/standards/shared-mime-info")
        ET.register_namespace("kdepriv", "http://www.kde.org/kdepriv")
        ET.indent(tree)
        output = io.BytesIO()
        tree.write(output, encoding="utf-8", xml_declaration=True)
        ownership_record = _commit_places(home, target, before, output.getvalue(), changes)
    return {"changed": bool(hidden or hidden_devices), "hidden_system_items": hidden,
            "hidden_system_devices": hidden_devices, "device_discovery_error": discovery_error,
            "ownership_record": ownership_record}
