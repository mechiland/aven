#!/usr/bin/env python3
"""Runtime evidence from the logged-in disposable Kinoite guest.

Writes JSON to stdout. Does not change app configuration, desktop settings, or OSTree.
Uses QScreen without a window at integer scales. At fractional scales, briefly
maps a transparent Qt surface after capture because QScreen DPR is rounded on
Wayland. Checks that KWin returns focus after this surface closes; popovers may
still be dismissed by the temporary focus change.
Run with scripts/guest-session.sh so Qt observes the actual Wayland session.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def command(argv, timeout=20):
    try:
        run = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
        result = {"argv": argv, "exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
        if run.returncode == 0:
            try:
                result["json"] = json.loads(run.stdout)
            except json.JSONDecodeError:
                pass
        return result
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"argv": argv, "exit_code": None, "error": str(error)}


def qt_command(argv, display):
    """Avoid a surface at integer scale; observe focus only for fractional DPR."""
    try:
        outputs = [o for o in display.get("json", {}).get("outputs", [])
                   if o.get("enabled") is True and o.get("connected") is True]
        if display.get("exit_code") != 0 or len(outputs) != 1:
            raise ValueError("A successful one-output KScreen JSON probe is required before Qt")
        scale = outputs[0].get("scale")
        if type(scale) not in [int, float] or scale not in [1, 1.25, 1.5, 2]:
            raise ValueError("Unsupported or missing compositor scale")
        argv = [*argv, str(scale)]
        if scale in [1, 2]:
            return command(argv)  # QT_PROBE verifies QScreen agreement; no QWindow is created.
        from window_tool import run_script
        before = run_script({"command": "inventory"})
        if before.get("ok") is not True or "active_window" not in before:
            raise ValueError("Cannot observe original KWin focus")
        result = command(argv)
        after = run_script({"command": "inventory"})
        result["focus"] = {"before": before["active_window"], "after": after.get("active_window"),
            "restored": after.get("ok") is True and "active_window" in after and before["active_window"] == after["active_window"],
            "method": "read-only KWin inventory before mapping and after Qt client exit",
            "activation_requests_sent": 0,
            "popup_state_restored": None,
            "limitation": "The fractional measurement surface may dismiss native menus/popovers. Matching active-window UUID does not restore popup state."}
        return result
    except (ImportError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        return {"argv": argv, "exit_code": None, "error": str(error)}


QT_PROBE = r'''
import json
import sys
from PySide6.QtCore import QLibraryInfo, QLocale, QRect, Qt, QTimer
from PySide6.QtGui import (QBackingStore, QFontInfo, QGuiApplication, QPainter,
    QRegion, QSurface, QSurfaceFormat, QTextLayout, QWindow)
app = QGuiApplication([])
app.setApplicationName("aven-runtime-scale-probe")
app.setQuitOnLastWindowClosed(False)
compositor_scale = float(sys.argv[1])
if app.platformName() != "wayland" or len(app.screens()) != 1:
    raise RuntimeError("One-screen native Wayland session required")
# A mapped wl_surface receives wp_fractional_scale preferred_scale. A bare
# QGuiApplication only receives integer wl_output scale. Submit an alpha-zero
# backing buffer so the surface is genuinely mapped without visible pixels.
class ScaleWindow(QWindow):
    def __init__(self):
        super().__init__()
        self.setFlags(Qt.SplashScreen | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
            | Qt.WindowDoesNotAcceptFocus | Qt.WindowTransparentForInput)
        self.setSurfaceType(QSurface.RasterSurface)
        fmt = QSurfaceFormat()
        fmt.setAlphaBufferSize(8)
        self.setFormat(fmt)
        self.resize(4, 4)
        self.setScreen(app.primaryScreen())
        self.backing = QBackingStore(self)
        self.frames_submitted = 0
        self.exposed_once = False
    def exposeEvent(self, event):
        if self.isExposed():
            self.exposed_once = True
            self.backing.resize(self.size())
            region = QRegion(QRect(0, 0, self.width(), self.height()))
            self.backing.beginPaint(region)
            painter = QPainter(self.backing.paintDevice())
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(QRect(0, 0, self.width(), self.height()), Qt.transparent)
            painter.end()
            self.backing.endPaint()
            self.backing.flush(region)
            self.frames_submitted += 1
window_probe = None
if compositor_scale in (1, 2):
    if app.primaryScreen().devicePixelRatio() != compositor_scale:
        raise RuntimeError("Integer QScreen DPR differs from KScreen; refusing to map a measurement window")
    measurement = {"method": "integer QScreen DPR with KScreen agreement",
        "scale": app.primaryScreen().devicePixelRatio(), "surface_mapped": False}
else:
    window = ScaleWindow()
    window.show()
    window_probe = {}
    def sample_window():
        window_probe.update({"scale": window.devicePixelRatio(), "exposed": window.isExposed(),
            "exposed_once": window.exposed_once, "visible": window.isVisible(),
            "screen": window.screen().name() if window.screen() else None,
            "frames_submitted": window.frames_submitted, "active": window.isActive(),
            "size": [window.width(), window.height()], "alpha_buffer_size": window.format().alphaBufferSize(),
            "method": "mapped transparent 4x4 QWindow with alpha-zero QBackingStore; input-transparent; focus hint may be ignored by Wayland"})
        app.quit()
    QTimer.singleShot(700, sample_window)
    app.exec()
    window.close()
    app.processEvents()
    measurement = {"method": "mapped QWindow DPR with KScreen agreement",
        "scale": window_probe.get("scale"), "surface_mapped": True}
font = QFontInfo(app.font())
sample = "文件 / Documents：12 个项目，24.8 MB。繁體中文：國門骨直，清晰舒適。"
layout = QTextLayout(sample, app.font())
layout.beginLayout()
line = layout.createLine()
line.setLineWidth(1800)
layout.endLayout()
glyph_runs = [{"family": run.rawFont().familyName(), "style": run.rawFont().styleName(),
    "glyph_count": len(run.glyphIndexes()), "missing_glyphs": sum(i == 0 for i in run.glyphIndexes())}
    for run in layout.glyphRuns()]
print(json.dumps({
    "platform": app.platformName(), "qt": QLibraryInfo.version().toString(),
    "locale": QLocale.system().name(),
    "font": {"family": font.family(), "point_size": font.pointSizeF(), "pixel_size": font.pixelSize(), "weight": font.weight()},
    "qt_shaping_sample": sample, "qt_shaping_runs": glyph_runs,
    "window": window_probe,
    "scale_measurement": measurement,
    "screens": [{"name": s.name(), "scale": s.devicePixelRatio(),
        "logical_dpi": s.logicalDotsPerInch(), "physical_dpi": s.physicalDotsPerInch(),
        "refresh_hz": s.refreshRate(),
        "geometry": [s.geometry().x(), s.geometry().y(), s.geometry().width(), s.geometry().height()],
        "available": [s.availableGeometry().x(), s.availableGeometry().y(), s.availableGeometry().width(), s.availableGeometry().height()]}
        for s in app.screens()]
}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guest", choices=["stock", "aven"], required=True)
    args = parser.parse_args()
    home = Path.home()
    commands = {
        "atomic": ["rpm-ostree", "status", "--json"],
        "packages": ["rpm", "-q", "plasma-desktop", "kwin", "dolphin", "firefox", "thunderbird", "gwenview", "fontconfig", "freetype", "python3-pyside6", "xdg-desktop-portal-kde"],
        "font_packages": ["rpm", "-qa", "*noto*", "*cjk*", "glibc-langpack-zh"],
        "display": ["kscreen-doctor", "-o"],
        "display_json": ["kscreen-doctor", "-j"],
        "qt": [sys.executable, "-c", QT_PROBE],
        "locales": ["locale", "-a"],
        "default_browser": ["xdg-mime", "query", "default", "x-scheme-handler/https"],
        "default_mail": ["xdg-mime", "query", "default", "x-scheme-handler/mailto"],
        "default_photo": ["xdg-mime", "query", "default", "image/jpeg"],
        "default_pdf": ["xdg-mime", "query", "default", "application/pdf"],
    }
    dbus = shutil.which("qdbus-qt6") or shutil.which("qdbus6") or shutil.which("qdbus") or "qdbus-qt6"
    commands.update({
        "kwin_loaded_effects": [dbus, "org.kde.KWin", "/Effects", "org.kde.kwin.Effects.loadedEffects"],
        "kwin_active_effects": [dbus, "org.kde.KWin", "/Effects", "org.kde.kwin.Effects.activeEffects"],
        "kwin_support": [dbus, "org.kde.KWin", "/KWin", "org.kde.KWin.supportInformation"],
    })
    configs = [home / ".config/kdeglobals", home / ".config/kwinrc", home / ".config/dolphinrc",
               home / ".config/gwenviewrc", home / ".config/gtk-3.0/settings.ini",
               home / ".config/gtk-4.0/settings.ini", Path("/etc/fonts/conf.d/60-aven-families.conf"),
               Path("/etc/fonts/conf.d/99-aven-rendering.conf")]
    # Hash app configs rather than exposing recent file paths in them.
    config_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None for path in configs}
    report = {
        "schema_version": 1,
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "guest": args.guest,
        "method": "guest runtime probe; integer QScreen without a window, fractional transparent Qt surface after capture with focus-return check",
        "machine": platform.machine(),
        "os_release": Path("/etc/os-release").read_text(),
        "ostree_booted": Path("/run/ostree-booted").exists(),
        "environment": {key: os.environ.get(key) for key in ["XDG_SESSION_TYPE", "XDG_CURRENT_DESKTOP", "WAYLAND_DISPLAY", "LANG", "LC_ALL", "LANGUAGE", "QT_SCALE_FACTOR", "QT_SCREEN_SCALE_FACTORS", "GDK_SCALE", "GDK_DPI_SCALE", "FREETYPE_PROPERTIES"]},
        "config_sha256": config_hashes,
        "commands": {},
        "font_matches": {},
        "limitations": ["Font matching and configuration hashes do not prove visual quality.", "At integer scales the Qt probe creates no window; QScreen and KScreen must agree.", "At fractional scales the separate measurement surface is mapped after the screenshot, not part of captured pixels.", "Wayland may temporarily focus the fractional alpha-zero surface; original KWin active UUID must return after it closes.", "The fractional probe can dismiss native menus/popovers even when the active UUID returns. Popup state is not restored; reopen it through the native application before further interaction.", "QScreen scale may be rounded on Wayland; use mapped QWindow scale with KScreen agreement for fractional captures.", "Atomic state reports available deployments; rollback must be exercised separately."],
    }
    for name, argv in commands.items():
        report["commands"][name] = qt_command(argv, report["commands"].get("display_json", {})) if name == "qt" else command(argv)
    fmt = "%{family}|%{style}|%{weight}|%{hintstyle}|%{rgba}|%{embolden}|%{file}\n"
    for pattern in ["sans-serif:lang=en:charset=0041", "Noto Sans:lang=zh-cn:charset=4e2d", "Noto Sans:lang=zh-tw:charset=4e2d", "Noto Sans:lang=zh-hk:charset=4e2d", "Noto Sans:lang=zh-cn:weight=medium:charset=4e2d", "monospace:lang=zh-cn:charset=4e2d", "emoji:charset=1f600"]:
        report["font_matches"][pattern] = command(["fc-match", "--format", fmt, pattern])
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
