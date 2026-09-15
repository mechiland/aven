"""Real QProcess handoff lifecycle with a controlled document helper.

QT_QPA_PLATFORM=offscreen PYTHONPATH=preview python3 -m unittest discover \
    -s preview/tests -p 'test_open_handoff.py'
"""

import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QProcess, Qt, QUrl
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from aven_preview.app import PreviewWindow


class HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.document = self.root / "中文 100% #&' $(literal).txt"
        self.document.write_text("日常文件 — Latin + 中文。", encoding="utf-8")
        self.helper = self.root / "document-helper"
        self.helper.write_text(f"#!{sys.executable}\n" + '''import json, sys, time
from pathlib import Path
root = Path(__file__).parent
with (root / 'received.jsonl').open('a') as stream:
    stream.write(json.dumps(sys.argv[1:]) + '\\n')
deadline = time.monotonic() + 5
while not (root / 'release').exists() and time.monotonic() < deadline:
    time.sleep(.01)
raise SystemExit(int((root / 'release').read_text()) if (root / 'release').exists() else 99)
''')
        self.helper.chmod(0o755)
        self.patch = patch("aven_preview.app.DOCUMENT_OPENER", str(self.helper))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.window = PreviewWindow([self.document])
        self.window.show()
        self.window.activateWindow()
        QTest.qWait(20)
        self.addCleanup(self.close_window)

    def close_window(self):
        self.window.close()
        QTest.qWait(30)

    def until(self, condition):
        deadline = time.monotonic() + 3
        while not condition() and time.monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(condition())

    def received(self):
        path = self.root / "received.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def begin(self, keyboard=False):
        if keyboard:
            QTest.keyClick(self.window, Qt.Key_Return)
        else:
            self.window.open_button.click()
        self.until(lambda: bool(self.received()))
        self.assertTrue(self.window.isVisible(), "Preview must survive until the helper reports completion")
        self.assertFalse(self.window.open_button.isEnabled())
        self.assertIsNotNone(self.window.opener)

    def test_button_waits_for_success_and_preserves_exact_unicode_url(self):
        self.begin()
        self.window.open_file()  # Repeated Enter/click cannot launch a duplicate.
        QTest.qWait(30)
        self.assertEqual(len(self.received()), 1)
        self.assertEqual(len(self.received()[0]), 1)
        self.assertEqual(QUrl(self.received()[0][0]).toLocalFile(), str(self.document))
        (self.root / "release").write_text("0")
        self.until(lambda: self.window.opener is None)
        self.assertFalse(self.window.isVisible())

    def test_enter_uses_same_async_handoff(self):
        self.begin(keyboard=True)
        (self.root / "release").write_text("0")
        self.until(lambda: self.window.opener is None)
        self.assertFalse(self.window.isVisible())

    def test_failed_launch_keeps_preview_and_allows_retry(self):
        self.begin()
        (self.root / "release").write_text("7")
        self.until(lambda: self.window.opener is None)
        self.assertTrue(self.window.isVisible())
        self.assertTrue(self.window.open_button.isEnabled())
        self.assertIn("Could not open", self.window.meta.text())
        (self.root / "release").write_text("0")
        self.window.open_button.click()
        self.until(lambda: self.window.opener is None)
        self.assertFalse(self.window.isVisible())
        self.assertEqual(len(self.received()), 2)

    def test_missing_helper_reports_failure_without_closing_preview(self):
        with patch("aven_preview.app.DOCUMENT_OPENER", str(self.root / "missing-helper")):
            self.window.open_button.click()
            self.until(lambda: self.window.opener is None)
        self.assertTrue(self.window.isVisible())
        self.assertTrue(self.window.open_button.isEnabled())
        self.assertEqual(self.received(), [])

    def test_escape_cancels_pending_helper(self):
        self.begin()
        process = self.window.opener
        QTest.keyClick(self.window, Qt.Key_Escape)
        self.until(lambda: process.state() == QProcess.NotRunning)
        self.assertFalse(self.window.isVisible())
        self.assertIsNone(self.window.opener)


if __name__ == "__main__":
    unittest.main()
