"""Prevent a sidebar cleanup from hiding user storage or visibility choices."""

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from places import configure_places
from system_places import parse_solid, system_devices


class DeviceClassificationTests(unittest.TestCase):
    def setUp(self):
        self.devices = {
            "/org/kde/fstab/overlay/": {"StorageAccess.filePath": "/", "StorageAccess.accessible": True},
            "fixed-drive": {"StorageDrive.removable": False, "StorageDrive.hotpluggable": False},
            "boot": {"StorageAccess.filePath": "/boot", "StorageAccess.accessible": True,
                     "Block.isSystem": True, "Block.device": "/dev/vda2", "parent": "fixed-drive", "StorageVolume.uuid": "boot-uuid"},
            "home": {"StorageAccess.filePath": "/etc", "StorageAccess.accessible": True,
                     "Block.isSystem": True, "Block.device": "/dev/vda3", "parent": "fixed-drive", "StorageVolume.uuid": "shared-uuid"},
        }
        self.mounts = {"filesystems": [{"target": "/", "source": "composefs", "fstype": "overlay", "options": "ro,relatime", "children": [
            {"target": "/boot", "source": "/dev/vda2", "fstype": "ext4", "options": "rw"},
            {"target": "/etc", "source": "/dev/vda3[/root/etc]", "fstype": "btrfs", "options": "rw"},
            {"target": "/var/home", "source": "/dev/vda3[/home]", "fstype": "btrfs", "options": "rw"},
        ]}]}

    def selected(self):
        return system_devices(self.devices, self.mounts, True)

    def test_atomic_overlay_and_boot_only(self):
        self.assertEqual({item["udi"] for item in self.selected()}, {"/org/kde/fstab/overlay/", "boot"})
        self.assertEqual(system_devices(self.devices, self.mounts, False), [])

    def test_removable_hotplug_and_unknown_drive_stay_visible(self):
        for property in ("StorageDrive.removable", "StorageDrive.hotpluggable"):
            for value in (True, None):
                with self.subTest(property=property, value=value):
                    devices = copy.deepcopy(self.devices)
                    devices["fixed-drive"][property] = value
                    selected = system_devices(devices, self.mounts, True)
                    self.assertNotIn("boot", {item["udi"] for item in selected})

    def test_a_shared_root_and_home_device_is_not_hidden(self):
        self.devices["home"]["StorageAccess.filePath"] = "/"
        self.mounts["filesystems"][0].update(source="/dev/vda3[/root]", fstype="btrfs")
        self.assertEqual({item["udi"] for item in self.selected()}, {"boot"})

    def test_arbitrary_internal_data_mount_is_not_hidden(self):
        self.devices["boot"]["StorageAccess.filePath"] = "/data"
        self.mounts["filesystems"][0]["children"][0]["target"] = "/data"
        self.assertNotIn("boot", {item["udi"] for item in self.selected()})

    def test_writable_or_unidentified_root_is_not_hidden(self):
        self.mounts["filesystems"][0]["options"] = "rw,relatime"
        self.assertEqual({item["udi"] for item in self.selected()}, {"boot"})
        self.mounts["filesystems"][0].update(options="ro", fstype="nfs")
        self.assertEqual({item["udi"] for item in self.selected()}, {"boot"})

    def test_solid_typed_fields_are_not_guessed_from_descriptions(self):
        parsed = parse_solid("udi = 'device'\n  description = 'false /boot' (string)\n  StorageDrive.removable = true (bool)\n  StorageAccess.filePath = '/boot' (string)\n  StorageDrive.hotpluggable = unknown\n")
        self.assertIs(parsed["device"]["StorageDrive.removable"], True)
        self.assertEqual(parsed["device"]["StorageAccess.filePath"], "/boot")
        self.assertNotIn("StorageDrive.hotpluggable", parsed["device"])


class PlacesPreservationTests(unittest.TestCase):
    def test_ownership_records_are_cumulative_and_only_describe_actual_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            target = home / ".local/share/user-places.xbel"
            target.parent.mkdir(parents=True)
            original = '''<xbel>
              <bookmark href="file:///home/user/Desktop"><title>Desktop</title><info><metadata owner="http://www.kde.org"><ID>desktop-id</ID><isSystemItem>true</isSystemItem><IsHidden>false</IsHidden></metadata></info></bookmark>
              <bookmark href="file:///home/user/Music"><title>Music</title><info><metadata owner="http://www.kde.org"><ID>music-id</ID><isSystemItem>true</isSystemItem></metadata></info></bookmark>
              <separator><info><metadata owner="http://www.kde.org"><UDI>previous-boot-udi</UDI><uuid>boot-uuid</uuid></metadata></info></separator>
            </xbel>'''.encode()
            target.write_bytes(original)
            devices = [{"udi": "current-boot-udi", "uuid": "boot-uuid", "mount": "/boot"},
                       {"udi": "/org/kde/fstab/overlay/", "uuid": "", "mount": "/"}]
            result = configure_places(home, devices)
            record = Path(result["ownership_record"])
            self.assertEqual(record.parent, home / ".local/state/aven/places")
            first_record_bytes = record.read_bytes()
            data = json.loads(first_record_bytes)
            self.assertEqual(data["component"], "aven-places")
            self.assertEqual(data["target"], ".local/share/user-places.xbel")
            self.assertEqual(data["before_sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(data["after_sha256"], hashlib.sha256(target.read_bytes()).hexdigest())
            self.assertEqual(len(data["changes"]), 3)
            self.assertTrue(all(item["previous_is_hidden"] == {"present": False, "value": None} for item in data["changes"]))
            boot = next(item for item in data["changes"] if item["identifiers"].get("uuid") == "boot-uuid")
            self.assertEqual(boot["identifiers"]["udi"], "previous-boot-udi")
            self.assertFalse(boot["entry_created"])
            self.assertTrue(next(item for item in data["changes"] if item["identifiers"].get("udi") == "/org/kde/fstab/overlay/")["entry_created"])
            self.assertEqual(ET.parse(target).findtext("bookmark/info/metadata/IsHidden"), "false")
            self.assertIsNone(configure_places(home, devices)["ownership_record"])
            self.assertEqual(len(list(record.parent.glob("*.json"))), 1)
            second = configure_places(home, devices + [{"udi": "efi-udi", "uuid": "efi-uuid", "mount": "/boot/efi"}])
            self.assertNotEqual(second["ownership_record"], str(record))
            self.assertEqual(len(list(record.parent.glob("*.json"))), 2)
            self.assertEqual(record.read_bytes(), first_record_bytes)
            self.assertEqual(record.stat().st_mode & 0o777, 0o400)

    def test_failed_record_publication_rolls_back_the_xbel_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            target = home / ".local/share/user-places.xbel"
            target.parent.mkdir(parents=True)
            original = b"<xbel/>"
            target.write_bytes(original)
            with patch("places.os.link", side_effect=OSError("record publication unavailable")):
                with self.assertRaises(OSError):
                    configure_places(home, [{"udi": "boot", "uuid": "boot-uuid", "mount": "/boot"}])
            self.assertEqual(target.read_bytes(), original)
            directory = home / ".local/state/aven/places"
            self.assertEqual(list(directory.iterdir()), [])

    def test_reused_device_identifier_does_not_hide_another_disk_uuid(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            target = home / ".local/share/user-places.xbel"
            target.parent.mkdir(parents=True)
            target.write_text('<xbel><separator><info><metadata owner="http://www.kde.org"><UDI>boot</UDI><uuid>previous-user-disk</uuid></metadata></info></separator></xbel>')
            configure_places(home, [{"udi": "boot", "uuid": "current-boot", "mount": "/boot"}])
            metadata = {node.findtext("uuid"): node for node in ET.parse(target).findall("separator/info/metadata")}
            self.assertIsNone(metadata["previous-user-disk"].find("IsHidden"))
            self.assertEqual(metadata["current-boot"].findtext("IsHidden"), "true")

    def test_native_device_separators_preserve_custom_bookmarks_and_user_choices(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            target = home / ".local/share/user-places.xbel"
            target.parent.mkdir(parents=True)
            original = '''<xbel>
              <bookmark href="file:///boot"><title>My boot shortcut</title><info><metadata owner="custom"><keep>yes</keep></metadata></info></bookmark>
              <separator><info><metadata owner="http://www.kde.org"><UDI>old-boot</UDI><uuid>boot-uuid</uuid><IsHidden>false</IsHidden></metadata></info></separator>
              <separator><info><metadata owner="http://www.kde.org"><UDI>user-volume</UDI><uuid>user-uuid</uuid></metadata></info></separator>
            </xbel>'''
            target.write_text(original)
            devices = [{"udi": "new-boot", "uuid": "boot-uuid", "mount": "/boot"},
                       {"udi": "/org/kde/fstab/overlay/", "uuid": "", "mount": "/"}]
            result = configure_places(home, devices)
            self.assertEqual(len(result["hidden_system_devices"]), 1)
            tree = ET.parse(target)
            self.assertEqual(tree.findtext("bookmark/info/metadata/keep"), "yes")
            metadata = {node.findtext("UDI"): node for node in tree.findall("separator/info/metadata")}
            self.assertEqual(metadata["old-boot"].findtext("IsHidden"), "false")
            self.assertIsNone(metadata["user-volume"].find("IsHidden"))
            self.assertEqual(metadata["/org/kde/fstab/overlay/"].findtext("IsHidden"), "true")
            self.assertEqual(target.with_name("user-places.xbel.pre-aven").read_text(), original)
            self.assertFalse(configure_places(home, devices)["changed"])
            self.assertEqual(len(ET.parse(target).findall("separator")), 3)


if __name__ == "__main__":
    unittest.main()
