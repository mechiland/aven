"""Exercise actual Qt dock-state restore, not hand-decoded state bytes.

QT_QPA_PLATFORM=offscreen python3 files/tests/smoke_layout.py
"""

import configparser
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtWidgets import QApplication, QDockWidget, QMainWindow, QToolBar, QWidget

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from layout import initialize, make_state
from places import configure_places


app = QApplication([])
encoded = make_state(184)
for window_width in (760, 1100, 1440):
    real = QMainWindow()
    real.resize(window_width, 700)
    real.setCentralWidget(QWidget(real))
    bar = QToolBar(real)
    bar.setObjectName("mainToolBar")
    bar.addAction("Files")
    real.addToolBar(bar)
    docks = {}
    for name, area in (("infoDock", Qt.RightDockWidgetArea), ("foldersDock", Qt.LeftDockWidgetArea), ("terminalDock", Qt.BottomDockWidgetArea), ("placesDock", Qt.LeftDockWidgetArea)):
        dock = QDockWidget(name, real)
        dock.setObjectName(name)
        dock.setWidget(QWidget(dock))
        real.addDockWidget(area, dock)
        docks[name] = dock
    assert real.restoreState(QByteArray.fromBase64(encoded.encode()))
    real.show()
    app.processEvents()
    assert abs(docks["placesDock"].width() - 184) <= 2, (window_width, docks["placesDock"].width())
    assert docks["placesDock"].isVisible()
    assert all(dock.isHidden() for name, dock in docks.items() if name != "placesDock")
    assert real.toolBarArea(bar) == Qt.TopToolBarArea
    real.close()

with tempfile.TemporaryDirectory() as temporary:
    home = Path(temporary)
    target = home / ".local/state/dolphinstaterc"
    target.parent.mkdir(parents=True)
    target.write_text("[State]\nState=original\nRestorePositionForNextInstance=false\n")
    assert initialize(home)["changed"]
    assert "State=original" in target.with_name(target.name + ".pre-aven").read_text()
    content = target.read_text()
    assert not initialize(home)["changed"]
    assert target.read_text() == content
    assert "RestorePositionForNextInstance=false" in content
    places = home / ".local/share/user-places.xbel"
    places.parent.mkdir(parents=True)
    places.write_text('''<xbel><bookmark href="file:///home/aven/Music"><title>Music</title><info><metadata owner="http://www.kde.org"><isSystemItem>true</isSystemItem><ID>native</ID></metadata></info></bookmark><bookmark href="file:///work/music"><title>Music</title><info><metadata owner="http://www.kde.org"><ID>custom</ID></metadata></info></bookmark><separator><info><metadata owner="http://www.kde.org"><UDI>device-id</UDI></metadata></info></separator></xbel>''')
    assert configure_places(home)["hidden_system_items"] == ["Music"]
    root = ET.parse(places).getroot()
    bookmarks = root.findall("bookmark")
    assert bookmarks[0].findtext("info/metadata/IsHidden") == "true"
    assert bookmarks[1].find("info/metadata/IsHidden") is None
    assert root.findtext("separator/info/metadata/UDI") == "device-id"
    assert not configure_places(home)["changed"]

print("PASS: 184px Places restored at 760/1100/1440 window widths; toolbar retained; one-time layout seed preserves later choices; custom bookmarks/devices preserved")
