"""Real temporary-file split/reassembly tests; tiny boundaries, no ISO VM input."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


split = module("aven_split_iso", "split-iso.py")
assemble = module("aven_reassemble_iso", "reassemble-iso.py")


def call(tool, *args):
    with patch.object(sys, "argv", ["packaging-test", *map(str, args)]):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            tool.main()


class IsoPackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aven-packaging-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "Aven-试用.iso"
        self.data = bytes(range(53))
        self.source.write_bytes(self.data)
        self.assets = self.root / "assets"

    def prepare(self, data=None, cap=17):
        if data is not None:
            self.data = data
            self.source.write_bytes(data)
        with patch.object(split, "PART_BYTES", cap):
            call(split, self.source, "--output", self.assets)
        self.manifest_path = self.assets / "ISO-PARTS.json"
        self.manifest = json.loads(self.manifest_path.read_text())
        self.output = self.assets / self.manifest["iso"]["file"]
        self.parts = [self.assets / part["file"] for part in self.manifest["parts"]]
        return self.manifest

    def rebuild(self):
        call(assemble, "--manifest", self.manifest_path)

    def assert_failed_cleanly(self):
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.assets.glob("*.partial")), [])
        self.assertEqual(self.source.read_bytes(), self.data)

    def test_tiny_boundary_roundtrip_and_published_hashes(self):
        m = self.prepare()
        self.assertEqual([p["bytes"] for p in m["parts"]], [17, 17, 17, 2])
        self.assertEqual(m["iso"]["sha256"], hashlib.sha256(self.data).hexdigest())
        self.assertEqual(b"".join(p.read_bytes() for p in self.parts), self.data)
        for part, path in zip(m["parts"], self.parts):
            self.assertEqual(part["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        expected = "".join(f'{entry["sha256"]}  {entry["file"]}\n' for entry in [*m["parts"], m["iso"]])
        self.assertEqual((self.assets / "ISO-SHA256SUMS").read_text(), expected)
        # Execute the copied distribution script with isolated Python imports.
        r = subprocess.run([sys.executable, "-I", str(self.assets / "reassemble-iso.py"),
                            "--manifest", str(self.manifest_path)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.output.read_bytes(), self.data)
        self.assertEqual(self.source.read_bytes(), self.data)
        self.assertEqual(list(self.assets.glob("*.partial")), [])

    def test_exact_boundary_has_no_empty_extra_part(self):
        m = self.prepare(bytes(range(34)))
        self.assertEqual([p["bytes"] for p in m["parts"]], [17, 17])
        self.rebuild()
        self.assertEqual(self.output.read_bytes(), self.data)

    def test_single_byte_over_boundary_is_retained(self):
        m = self.prepare(bytes(range(18)))
        self.assertEqual([p["bytes"] for p in m["parts"]], [17, 1])
        self.rebuild()
        self.assertEqual(self.output.read_bytes(), self.data)

    def test_same_size_corruption_is_rejected_and_partial_removed(self):
        self.prepare()
        damaged = bytearray(self.parts[1].read_bytes())
        damaged[3] ^= 255
        self.parts[1].write_bytes(damaged)
        with self.assertRaisesRegex(ValueError, "Part checksum mismatch"):
            self.rebuild()
        self.assert_failed_cleanly()

    def test_truncated_part_is_rejected_and_partial_removed(self):
        self.prepare()
        self.parts[1].write_bytes(self.parts[1].read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError, "Part size mismatch"):
            self.rebuild()
        self.assert_failed_cleanly()

    def test_missing_part_is_rejected_and_partial_removed(self):
        self.prepare()
        self.parts[1].unlink()
        with self.assertRaises(FileNotFoundError):
            self.rebuild()
        self.assert_failed_cleanly()

    def test_wrong_whole_hash_cannot_publish_valid_individual_parts(self):
        self.prepare()
        self.manifest["iso"]["sha256"] = "0" * 64
        self.manifest_path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, "Reconstructed ISO checksum mismatch"):
            self.rebuild()
        self.assert_failed_cleanly()

    def test_reordered_parts_fail_whole_hash(self):
        self.prepare()
        self.manifest["parts"][0], self.manifest["parts"][1] = self.manifest["parts"][1], self.manifest["parts"][0]
        self.manifest_path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, "Reconstructed ISO checksum mismatch"):
            self.rebuild()
        self.assert_failed_cleanly()

    def test_existing_iso_is_never_overwritten(self):
        self.prepare()
        self.output.write_bytes(b"existing user file")
        with self.assertRaises(SystemExit):
            self.rebuild()
        self.assertEqual(self.output.read_bytes(), b"existing user file")
        self.assertEqual(list(self.assets.glob("*.partial")), [])

    def test_concurrent_output_creation_is_not_overwritten(self):
        self.prepare()
        original_link = assemble.os.link
        def competing_link(source, destination):
            Path(destination).write_bytes(b"created by another process")
            return original_link(source, destination)
        with patch.object(assemble.os, "link", competing_link):
            with self.assertRaises(FileExistsError):
                self.rebuild()
        self.assertEqual(self.output.read_bytes(), b"created by another process")
        self.assertEqual(list(self.assets.glob("*.partial")), [])

    def test_manifest_path_escape_is_rejected_before_output(self):
        self.prepare()
        self.manifest["parts"][1]["file"] = "../outside-part"
        self.manifest_path.write_text(json.dumps(self.manifest))
        with self.assertRaises(SystemExit):
            self.rebuild()
        self.assert_failed_cleanly()

    def test_split_refuses_existing_release_assets(self):
        self.assets.mkdir()
        sentinel = self.assets / "keep.txt"
        sentinel.write_bytes(b"existing release assets")
        with self.assertRaises(SystemExit):
            call(split, self.source, "--output", self.assets)
        self.assertEqual(sentinel.read_bytes(), b"existing release assets")
        self.assertEqual(list(self.assets.iterdir()), [sentinel])


if __name__ == "__main__":
    unittest.main()
