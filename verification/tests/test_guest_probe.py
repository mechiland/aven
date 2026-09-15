"""Source-only checks for choosing a non-disruptive integer scale probe."""
import contextlib
import io
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from guest_probe import QT_PROBE, qt_command


def display(scale):
    return {"exit_code": 0, "json": {"outputs": [{"enabled": True, "connected": True, "scale": scale}]}}


class ProbeTest(unittest.TestCase):
    def test_integer_driver_never_inventories_or_requests_focus(self):
        for scale in [1, 2]:
            with patch("guest_probe.command", return_value={"exit_code": 0}) as command, patch("window_tool.run_script", side_effect=AssertionError("integer probe must not need KWin focus")):
                self.assertEqual(qt_command(["python3", "-c", QT_PROBE], display(scale)), {"exit_code": 0})
                self.assertEqual(command.call_args.args[0][-1], str(scale))

    def test_fractional_driver_checks_focus_and_records_popup_limit(self):
        with patch("guest_probe.command", return_value={"exit_code": 0}), patch("window_tool.run_script", return_value={"ok": True, "active_window": "original"}) as inventory:
            result = qt_command(["python3", "-c", QT_PROBE], display(1.25))
            self.assertEqual(inventory.call_count, 2)
            self.assertTrue(result["focus"]["restored"])
            self.assertIsNone(result["focus"]["popup_state_restored"])
            self.assertIn("popovers", result["focus"]["limitation"])

    def test_failed_compositor_query_never_maps_a_surface(self):
        with patch("guest_probe.command", side_effect=AssertionError("failed compositor query must stop before Qt")):
            self.assertIsNone(qt_command(["python3", "-c", QT_PROBE], {})["exit_code"])

    def execute_integer_qt_code(self, compositor, screen_scale):
        # Run the actual embedded program with a forbidden QWindow constructor.
        # No real GUI or screenshot is created by these test doubles.
        rect = SimpleNamespace(x=lambda: 0, y=lambda: 0, width=lambda: 1920, height=lambda: 1200)
        screen = SimpleNamespace(devicePixelRatio=lambda: screen_scale, name=lambda: "Virtual-1",
            logicalDotsPerInch=lambda: 96, physicalDotsPerInch=lambda: 96,
            refreshRate=lambda: 60, geometry=lambda: rect, availableGeometry=lambda: rect)
        app = Mock()
        app.platformName.return_value = "wayland"
        app.screens.return_value = [screen]
        app.primaryScreen.return_value = screen
        app.exec.side_effect = AssertionError("integer probe must not run a window event loop")
        font = SimpleNamespace(family=lambda: "Noto Sans", pointSizeF=lambda: 10, pixelSize=lambda: 13, weight=lambda: 400)
        layout = Mock()
        layout.glyphRuns.return_value = []
        class ForbiddenWindow:
            def __init__(self):
                raise AssertionError("integer probe constructed a QWindow")
        core, gui = ModuleType("PySide6.QtCore"), ModuleType("PySide6.QtGui")
        for name in ["QRect", "Qt", "QTimer"]:
            setattr(core, name, Mock())
        core.QLibraryInfo = SimpleNamespace(version=lambda: SimpleNamespace(toString=lambda: "test-only"))
        core.QLocale = SimpleNamespace(system=lambda: SimpleNamespace(name=lambda: "zh_TW"))
        for name in ["QBackingStore", "QPainter", "QRegion", "QSurface", "QSurfaceFormat"]:
            setattr(gui, name, Mock())
        gui.QWindow = ForbiddenWindow
        gui.QGuiApplication = lambda args: app
        gui.QFontInfo = lambda value: font
        gui.QTextLayout = lambda *args: layout
        output = io.StringIO()
        with patch.dict(sys.modules, {"PySide6": ModuleType("PySide6"), "PySide6.QtCore": core, "PySide6.QtGui": gui}), patch.object(sys, "argv", ["-c", str(compositor)]), contextlib.redirect_stdout(output):
            exec(QT_PROBE, {})
        return json.loads(output.getvalue())

    def test_integer_embedded_program_creates_no_window(self):
        for scale in [1, 2]:
            result = self.execute_integer_qt_code(scale, scale)
            self.assertIsNone(result["window"])
            self.assertEqual(result["scale_measurement"], {"method": "integer QScreen DPR with KScreen agreement", "scale": scale, "surface_mapped": False})

    def test_integer_disagreement_fails_without_mapping_fallback(self):
        with self.assertRaisesRegex(RuntimeError, "Integer QScreen DPR differs"):
            self.execute_integer_qt_code(1, 2)


if __name__ == "__main__":
    unittest.main()
