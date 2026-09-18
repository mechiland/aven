"""Protect first-login completion/retry behavior without a guest or desktop."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[2] / "iso/first-login.py"


class FirstLoginCompletionTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("iso_first_login_test", SOURCE)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.module.STATE = self.home / ".local/state/aven"
        self.calls = []
        real_exists = Path.exists
        for replacement in (
            patch.object(self.module.os, "getuid", return_value=1000),
            patch.object(Path, "home", return_value=self.home),
            patch.object(Path, "exists", lambda path: True if str(path) == "/run/ostree-booted" else real_exists(path)),
            patch.object(self.module.shutil, "which", return_value="/usr/bin/qdbus-qt6"),
            patch.object(sys, "argv", [str(SOURCE), "layout"]),
        ):
            replacement.start()
            self.addCleanup(replacement.stop)

    def seed_complete(self):
        self.module.STATE.mkdir(parents=True)
        (self.module.STATE / "iso-seed-v1.json").write_text('{"phase":"seed"}\n')

    def run_layout(self, fail_places=False):
        def run(argv, **kwargs):
            self.calls.append(argv)
            if fail_places and any(str(item).endswith("files/finalize-places.py") for item in argv):
                raise subprocess.CalledProcessError(75, argv)
            if argv[-1] == "org.kde.KWin.VirtualDesktopManager.count":
                return subprocess.CompletedProcess(argv, 0, stdout="1\n")
            return subprocess.CompletedProcess(argv, 0)
        with patch.object(self.module.subprocess, "run", side_effect=run):
            self.module.main()

    def test_places_timeout_leaves_marker_absent_and_next_login_retries(self):
        self.seed_complete()
        marker = self.module.STATE / "iso-layout-v1.json"
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_layout(fail_places=True)
        self.assertFalse(marker.exists())
        self.assertTrue((self.module.STATE / "iso-seed-v1.json").exists())
        self.run_layout()
        self.assertEqual(json.loads(marker.read_text())["phase"], "layout")
        self.assertEqual(sum(any(str(part).endswith("files/finalize-places.py") for part in call)
                             for call in self.calls), 2)

    def test_completed_layout_is_not_reapplied_on_next_login(self):
        self.seed_complete()
        self.run_layout()
        marker = self.module.STATE / "iso-layout-v1.json"
        before = (marker.read_bytes(), marker.stat().st_mtime_ns)
        self.calls.clear()
        self.run_layout()
        self.assertEqual(self.calls, [])
        self.assertEqual((marker.read_bytes(), marker.stat().st_mtime_ns), before)

    def test_missing_seed_never_marks_layout_complete(self):
        with self.assertRaisesRegex(RuntimeError, "seed failed"):
            self.run_layout()
        self.assertFalse((self.module.STATE / "iso-layout-v1.json").exists())
        self.assertEqual(self.calls, [])

    def test_native_setup_system_user_is_not_seeded_or_given_state(self):
        with patch.object(self.module.os, "getuid", return_value=999):
            self.run_layout()
        self.assertFalse(self.module.STATE.exists())
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
