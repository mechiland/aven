"""Offline restoration safety checks; no guest or visual-quality assertions."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

SPEC = importlib.util.spec_from_file_location("restore_profile", Path(__file__).parents[1] / "restore_profile.py")
restore = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(restore)


def device(udi="/boot-device", uuid="boot-uuid", hidden=None, extra=""):
    flag = "" if hidden is None else f"<IsHidden>{hidden}</IsHidden>"
    return (f'<separator><info><metadata owner="http://www.kde.org"><UDI>{udi}</UDI>'
            f'<isSystemItem>true</isSystemItem><uuid>{uuid}</uuid>{flag}{extra}</metadata></info></separator>')


def xbel(*entries):
    return ("<xbel>" + "".join(entries) + "</xbel>").encode()


def change(udi="/boot-device", uuid="boot-uuid"):
    return {"kind": "system-device", "identifiers": {"udi": udi, "uuid": uuid},
            "previous_is_hidden": {"present": False, "value": None},
            "applied_is_hidden": "true", "entry_created": True}


class RestorePlacesTests(unittest.TestCase):
    def hidden(self, raw, identity=None):
        matches = restore.device_metadata(ET.fromstring(raw), identity or change()["identifiers"])
        return matches[0].findtext("IsHidden") if matches else "missing-device"

    def test_exact_record_reverts_only_owned_flag_preserving_bookmarks_and_metadata(self):
        custom = '<bookmark href="file:///boot"><title>My boot notes</title><info><metadata owner="custom"><IsHidden>true</IsHidden></metadata></info></bookmark>'
        current = xbel(device(hidden="true", extra="<userNote>Keep me</userNote>"),
                       device("/usb", "usb-uuid", "true"), custom)
        result = restore.merge_places(current, xbel(), [change()])
        self.assertIsNone(self.hidden(result))
        self.assertEqual(self.hidden(result, {"udi": "/usb", "uuid": "usb-uuid"}), "true")
        tree = ET.fromstring(result)
        self.assertEqual(tree.findtext("bookmark/title"), "My boot notes")
        self.assertEqual(tree.findtext("separator/info/metadata/userNote"), "Keep me")

    def test_no_record_does_not_infer_from_hidden_system_device(self):
        self.assertEqual(self.hidden(restore.merge_places(xbel(device(hidden="true")), xbel())), "true")

    def test_explicit_current_visibility_is_preserved(self):
        result = restore.merge_places(xbel(device(hidden="false")), xbel(device(hidden="true")), [change()])
        self.assertEqual(self.hidden(result), "false")

    def test_selected_snapshot_already_hidden_stays_hidden(self):
        result = restore.merge_places(xbel(device(hidden="true")), xbel(device(hidden="true")), [change()])
        self.assertEqual(self.hidden(result), "true")

    def test_uuid_reused_udi_is_not_owned(self):
        result = restore.merge_places(xbel(device(uuid="new-user-disk", hidden="true")), xbel(), [change()])
        self.assertEqual(self.hidden(result, {"udi": "/boot-device", "uuid": "new-user-disk"}), "true")

    def test_uuid_survives_changed_udi(self):
        result = restore.merge_places(xbel(device(udi="/different-udi", hidden="true")), xbel(), [change()])
        self.assertIsNone(self.hidden(result))

    def test_missing_uuid_does_not_fall_back_to_kernel_name(self):
        result = restore.merge_places(xbel(device(uuid="", hidden="true")), xbel(), [change()])
        self.assertEqual(self.hidden(result, {"udi": "/boot-device", "uuid": ""}), "true")

    def test_overlay_udi_without_uuid_is_restored(self):
        identity = {"udi": "/org/kde/fstab/overlay/", "uuid": ""}
        result = restore.merge_places(xbel(device(**identity, hidden="true")), xbel(), [change(**identity)])
        self.assertIsNone(self.hidden(result, identity))

    def test_ambiguous_device_is_retained_and_reported(self):
        unresolved = []
        result = restore.merge_places(xbel(device(hidden="true"), device(hidden="true")), xbel(), [change()], unresolved)
        self.assertEqual(self.hidden(result), "true")
        self.assertEqual(len(unresolved), 1)

    def test_explicit_ordinary_place_visibility_is_preserved(self):
        entry = '<bookmark href="file:///home/aven/Music"><title>Music</title><info><metadata owner="http://www.kde.org"><isSystemItem>true</isSystemItem><IsHidden>{}</IsHidden></metadata></info></bookmark>'
        result = restore.merge_places(xbel(entry.format("false")), xbel(entry.format("true")))
        self.assertEqual(ET.fromstring(result).findtext("bookmark/info/metadata/IsHidden"), "false")

    def test_record_preflight_rejects_unowned_transition(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "record.json"
            record = {"schema_version": 1, "component": "aven-places", "target": restore.PLACES, "changes": [change()]}
            path.write_text(json.dumps(record))
            changes, sources = restore.load_places_records([path])
            self.assertEqual(changes, [change()])
            self.assertEqual(sources[0]["sha256"], restore.sha(path.read_bytes()))
            record["changes"][0]["previous_is_hidden"] = {"present": True, "value": "false"}
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "transition"):
                restore.load_places_records([path])

    def test_apply_and_unchanged_undo_are_byte_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / restore.PLACES
            target.parent.mkdir(parents=True)
            original, current = xbel(), xbel(device(hidden="true", extra="<userNote>Keep</userNote>"))
            target.write_bytes(current)
            source = {restore.PLACES: {"kind": "file", "data": original, "sha256": restore.sha(original), "mode": 0o644}}
            operations = restore.plan(root, source, [], [change()])
            archive = root / "archive"
            restore.apply_plan(root, operations, archive)
            self.assertIsNone(self.hidden(target.read_bytes()))
            undo = restore.load_snapshot(archive, restore.USER_PATHS)
            restore.apply_plan(root, restore.plan(root, undo, []), root / "undo")
            self.assertEqual(target.read_bytes(), current)

    def test_malformed_or_uncommitted_records_fail_preflight(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "record.json"
            good = {"schema_version": 1, "component": "aven-places", "target": restore.PLACES, "changes": [change()]}
            for record in [[], dict(good, changes=[None]), dict(good, changes=[dict(change(), identifiers=None)])]:
                path.write_text(json.dumps(record))
                with self.assertRaises(ValueError):
                    restore.load_places_records([path])
            pending = Path(folder) / "record.pending"
            pending.write_text(json.dumps(good))
            with self.assertRaisesRegex(ValueError, "committed"):
                restore.load_places_records([pending])

    def test_later_bookmarks_prevent_whole_file_undo(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / restore.PLACES
            target.parent.mkdir(parents=True)
            target.write_bytes(xbel(device(hidden="true")))
            original = xbel()
            source = {restore.PLACES: {"kind": "file", "data": original, "sha256": restore.sha(original), "mode": 0o644}}
            archive = root / "archive"
            restore.apply_plan(root, restore.plan(root, source, [], [change()]), archive)
            target.write_bytes(xbel(device(), '<bookmark href="file:///new"><title>Added later</title></bookmark>'))
            unresolved = []
            operations = restore.plan(root, restore.load_snapshot(archive, restore.USER_PATHS), unresolved)
            self.assertIn("changed after restore", unresolved[0])
            if operations:
                restore.apply_plan(root, operations, root / "undo")
            self.assertIn(b"Added later", target.read_bytes())
            self.assertIsNone(self.hidden(target.read_bytes()))


if __name__ == "__main__":
    unittest.main()
