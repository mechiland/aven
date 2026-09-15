"""Exercise the late native-XBEL first-login race without a desktop session."""

import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from finalize_places import finalize_places, main
from system_places import require_ready_inventory

NATIVE = '''<xbel version="1.0">
  <bookmark href="file:///home/reader/Desktop"><title>Desktop</title><info><metadata owner="http://www.kde.org"><isSystemItem>true</isSystemItem><IsHidden>false</IsHidden></metadata></info></bookmark>
  <bookmark href="file:///home/reader/Music"><title>Music</title><info><metadata owner="http://www.kde.org"><isSystemItem>true</isSystemItem></metadata></info></bookmark>
  <bookmark href="file:///home/reader/work"><title>My work</title><info><metadata owner="custom"><keep>yes</keep></metadata></info></bookmark>
</xbel>'''
ROOT = {"udi": "/org/kde/fstab/overlay/", "uuid": "", "mount": "/", "reason": "read-only Atomic root"}
BOOT = {"udi": "boot", "uuid": "boot-uuid", "mount": "/boot", "reason": "fixed system boot volume"}


class Clock:
    def __init__(self, on_sleep=lambda _: None):
        self.now = 0
        self.on_sleep = on_sleep

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        self.on_sleep(self.now)


class FinalizeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.target = self.home / ".local/share/user-places.xbel"
        self.calls = []

    def native(self, content=NATIVE):
        self.target.parent.mkdir(parents=True, exist_ok=True)
        self.target.write_text(content)

    def discover(self, **kwargs):
        self.calls.append(kwargs)
        self.assertTrue(kwargs["require_ready"])
        self.assertGreater(kwargs["timeout"], 0)
        return [ROOT, BOOT]

    def run_finalize(self, clock=None, discover=None, timeout=3):
        clock = clock or Clock()
        return finalize_places(self.home, timeout=timeout, interval=0.5,
                               discover=discover or self.discover,
                               monotonic=clock.monotonic, sleep=clock.sleep)

    def test_late_native_creation_then_audited_idempotent_defaults(self):
        def create_native(now):
            if now == 1:
                self.assertFalse(self.target.exists())
                self.assertFalse((self.home / ".local/state").exists())
                self.assertEqual(self.calls, [])
                self.native()
        result = self.run_finalize(Clock(create_native))
        self.assertTrue(result["complete"])
        self.assertTrue(result["device_inventory_ready"])
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(result["hidden_system_items"], ["Music"])
        document = ET.parse(self.target)
        bookmarks = {item.findtext("title"): item for item in document.findall("bookmark")}
        self.assertEqual(bookmarks["Desktop"].findtext("info/metadata/IsHidden"), "false")
        self.assertEqual(bookmarks["My work"].findtext("info/metadata/keep"), "yes")
        self.assertEqual(self.target.with_name("user-places.xbel.pre-aven").read_text(), NATIVE)
        before = self.target.read_bytes()
        repeated = self.run_finalize()
        self.assertTrue(repeated["complete"])
        self.assertFalse(repeated["changed"])
        self.assertIsNone(repeated["ownership_record"])
        self.assertEqual(self.target.read_bytes(), before)
        self.assertEqual(len(list((self.home / ".local/state/aven/places").glob("*.json"))), 1)

    def test_transient_inventory_errors_reset_stability(self):
        self.native()
        answers = iter(([ROOT], RuntimeError("Solid startup"), [ROOT, BOOT], [BOOT, ROOT]))
        attempts = []
        def discover(**kwargs):
            attempts.append(kwargs)
            result = next(answers)
            if isinstance(result, Exception):
                raise result
            return result
        result = self.run_finalize(discover=discover)
        self.assertTrue(result["complete"])
        self.assertEqual(len(attempts), 4)
        self.assertEqual({item["mount"] for item in result["hidden_system_devices"]}, {"/", "/boot"})

    def test_changed_inventory_needs_another_complete_sample(self):
        self.native()
        answers = iter(([ROOT], [ROOT, BOOT], [ROOT, BOOT]))
        result = self.run_finalize(discover=lambda **_: next(answers))
        self.assertTrue(result["complete"])
        self.assertEqual(result["attempts"], 3)

    def test_missing_native_xbel_times_out_without_creating_any_files(self):
        clock = Clock()
        result = self.run_finalize(clock, timeout=1)
        self.assertFalse(result["complete"])
        self.assertEqual(clock.now, 1)
        self.assertEqual(self.calls, [])
        self.assertEqual(list(self.home.iterdir()), [])

    def test_partial_or_wrong_document_is_not_overwritten(self):
        for content in ("<xbel>", "<xbel/>", "<other><bookmark/></other>"):
            with self.subTest(content=content):
                self.native(content)
                result = self.run_finalize(timeout=1)
                self.assertFalse(result["complete"])
                self.assertEqual(self.target.read_text(), content)
                self.assertEqual(self.calls, [])
                self.assertFalse((self.home / ".local/state").exists())

    def test_inventory_timeout_cannot_mark_complete_or_change_native_file(self):
        self.native()
        def unavailable(**_):
            raise RuntimeError("Waiting for Solid's mounted /boot entry")
        result = self.run_finalize(discover=unavailable, timeout=1)
        self.assertFalse(result["complete"])
        self.assertIn("/boot", result["reason"])
        self.assertEqual(self.target.read_text(), NATIVE)
        self.assertFalse((self.home / ".local/state").exists())

    def test_dangling_symlink_is_a_permanent_refusal(self):
        self.target.parent.mkdir(parents=True)
        self.target.symlink_to(self.home / "not-created")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.run_finalize()
        self.assertTrue(self.target.is_symlink())
        self.assertFalse((self.home / "not-created").exists())

    def test_cli_timeout_has_nonzero_exit_and_machine_readable_result(self):
        with patch("finalize_places.finalize_places", return_value={"complete": False, "reason": "pending"}), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(main(["--home", str(self.home), "--timeout", "1"]), 75)
        self.assertFalse(json.loads(output.getvalue())["complete"])


class InventoryReadinessTests(unittest.TestCase):
    def setUp(self):
        self.devices = {
            ROOT["udi"]: {"StorageAccess.filePath": "/", "StorageAccess.accessible": True},
            "drive": {"StorageDrive.removable": False, "StorageDrive.hotpluggable": False},
            "boot": {"StorageAccess.filePath": "/boot", "StorageAccess.accessible": True,
                     "Block.device": "/dev/vda2", "Block.isSystem": True, "parent": "drive"},
        }
        self.mounts = {"filesystems": [
            {"target": "/", "source": "composefs", "fstype": "overlay", "options": "ro"},
            {"target": "/boot", "source": "/dev/vda2", "fstype": "ext4", "options": "rw"},
        ]}

    def test_complete_inventory_is_ready(self):
        require_ready_inventory(self.devices, self.mounts)

    def test_empty_or_missing_root_or_boot_is_not_ready(self):
        for missing in (ROOT["udi"], "boot", "drive"):
            with self.subTest(missing=missing):
                devices = copy.deepcopy(self.devices)
                del devices[missing]
                with self.assertRaises(RuntimeError):
                    require_ready_inventory(devices, self.mounts)
        with self.assertRaises(RuntimeError):
            require_ready_inventory({}, self.mounts)

    def test_known_removable_boot_is_ready_without_changing_hide_policy(self):
        self.devices["drive"]["StorageDrive.removable"] = True
        require_ready_inventory(self.devices, self.mounts)

    def test_mount_inventory_is_required(self):
        with self.assertRaises(RuntimeError):
            require_ready_inventory(self.devices, {})


if __name__ == "__main__":
    unittest.main()
