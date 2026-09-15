"""Seed Dolphin's native dock layout through Qt's public serialization API.

Run offscreen, once per prototype home. No Qt binary-layout offsets are used.
The real Dolphin remains free to resize and save these panels afterwards.
"""

import argparse
import configparser
import json
from pathlib import Path
import shutil


def make_state(places_width=224):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QDockWidget, QMainWindow, QToolBar, QWidget

    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    window.resize(1100, 760)
    window.setCentralWidget(QWidget(window))
    toolbar = QToolBar(window)
    toolbar.setObjectName("mainToolBar")
    toolbar.addWidget(QWidget(toolbar))
    window.addToolBar(toolbar)
    docks = {}
    # These are the names in DolphinMainWindow::setupDockWidgets (26.04/26.08).
    for name, area in (("infoDock", Qt.RightDockWidgetArea), ("foldersDock", Qt.LeftDockWidgetArea), ("terminalDock", Qt.BottomDockWidgetArea), ("placesDock", Qt.LeftDockWidgetArea)):
        dock = QDockWidget(window)
        dock.setObjectName(name)
        dock.setTitleBarWidget(QWidget(dock))
        dock.setWidget(QWidget(dock))
        window.addDockWidget(area, dock)
        if name != "placesDock":
            dock.hide()
        docks[name] = dock
    window.show()
    app.processEvents()
    window.resizeDocks([docks["placesDock"]], [places_width], Qt.Horizontal)
    app.processEvents()
    actual_width = docks["placesDock"].width()
    if abs(actual_width - places_width) > 2:
        raise RuntimeError(f"Qt did not apply the requested Places width: {actual_width}")
    state = bytes(window.saveState().toBase64()).decode("ascii")
    window.close()
    return state


def initialize(home, places_width=224, reset=False):
    marker = home / ".config/aven/files-layout.json"
    if marker.exists() and not reset:
        return {"changed": False, "reason": "initial layout already seeded"}
    state = make_state(places_width)
    target = home / ".local/state/dolphinstaterc"
    legacy = home / ".local/share/dolphin/dolphinstaterc"
    if not target.exists() and legacy.exists():
        # Preserve other state keys when moving from the pre-XDG_STATE_HOME path.
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    saved = target.with_name(target.name + ".pre-aven")
    if target.exists() and not saved.exists():
        shutil.copy2(target, saved)
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    config.read(target, encoding="utf-8")
    if not config.has_section("State"):
        config.add_section("State")
    config.set("State", "State", state)
    with target.open("w", encoding="utf-8") as stream:
        config.write(stream, space_around_delimiters=False)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"version": 1, "places_width": places_width, "state_file": str(target)}, indent=2) + "\n", encoding="utf-8")
    return {"changed": True, "places_width": places_width, "state_file": str(target)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--width", type=int, default=224)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if not 160 <= args.width <= 320:
        parser.error("Places width must be between 160 and 320 logical pixels")
    print(json.dumps(initialize(args.home.resolve(), args.width, args.reset)))
