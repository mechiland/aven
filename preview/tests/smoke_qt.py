"""Real Qt render/decode smoke test; outputs do not count as OS screenshots.

QT_QPA_PLATFORM=offscreen PYTHONPATH=preview python3 preview/tests/smoke_qt.py
"""

from pathlib import Path
import tempfile
import time
import wave

from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPalette, QPdfWriter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QTextEdit

from aven_preview.app import ImageCanvas, PreviewWindow


app = QApplication([])
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    text = root / "清晰 — Aven.txt"
    text.write_text("简体中文：日常，清晰。\n繁體中文：日常，清晰。\nAven — Latin + 中文 2026，文件 12.5 MB。", encoding="utf-8")
    image = root / "100% #中文.png"
    bitmap = QImage(1200, 800, QImage.Format_RGB32)
    bitmap.fill(QColor("#dfe5e1"))
    assert bitmap.save(str(image))
    pdf = root / "中文.pdf"
    writer = QPdfWriter(str(pdf))
    painter = QPainter(writer)
    painter.drawText(120, 300, "Aven — 中文 PDF preview")
    painter.end()
    del writer
    sound = root / "声音.wav"
    with wave.open(str(sound), "wb") as stream:
        stream.setparams((1, 2, 8000, 8000, "NONE", "not compressed"))
        stream.writeframes(b"\x00\x00" * 8000)
    window = PreviewWindow([text, image, pdf, sound])
    window.show()
    app.processEvents()
    assert isinstance(window.renderer, QTextEdit)
    assert window.renderer.toPlainText() == text.read_text()
    document = window.renderer.document()
    first = document.begin()
    delta = document.documentLayout().blockBoundingRect(first.next()).top() - document.documentLayout().blockBoundingRect(first).top()
    assert 29 <= delta <= 31, f"Chinese line spacing is {delta}px, expected the 17px × 1.75 prose role"
    QTest.keyClick(window, Qt.Key_Right, Qt.AltModifier)
    app.processEvents()
    assert window.index == 1 and isinstance(window.renderer, ImageCanvas)
    assert not window.renderer.image.isNull()
    window.navigate(1)
    app.processEvents()
    assert window.pdf and window.pdf.pageCount() == 1
    assert window.renderer.palette().color(QPalette.Dark) == window.renderer.palette().color(QPalette.Window)
    window.navigate(1)
    wait = QEventLoop()
    QTimer.singleShot(500, wait.quit)
    wait.exec()
    assert window.player is not None
    assert window.player.duration() == 1000
    assert window.player.source().toLocalFile() == str(sound)
    assert window.player.playbackState().name == "StoppedState"
    assert window.renderer.findChild(QLabel, "playbackTime").text() == "0:00 / 0:01", "Stopped audio must show duration before playback"
    QTest.keyClick(window, Qt.Key_Escape)
    assert not window.isVisible()
    video = Path(__file__).resolve().parents[2] / "fixtures/photos/05-花开-Flower.webm"
    window = PreviewWindow([video])
    states = []
    window.player.playbackStateChanged.connect(lambda state: states.append(state.name))
    window.show()
    deadline = time.monotonic() + 5
    while not window.player.videoSink().videoFrame().isValid() and time.monotonic() < deadline:
        QTest.qWait(50)
    assert window.player.videoSink().videoFrame().isValid(), "Paused video did not decode a poster frame"
    assert window.player.playbackState().name == "PausedState"
    assert window.player.position() == 0
    assert window.renderer.findChild(QLabel, "playbackTime").text() == "0:00 / 0:05", "Paused poster must show duration before playback"
    QTest.qWait(350)
    assert window.player.position() == 0 and "PlayingState" not in states, "Poster must not autoplay"
    QTest.keyClick(window, Qt.Key_Space)
    QTest.qWait(350)
    assert window.player.playbackState().name == "PlayingState" and window.player.position() > 0
    QTest.keyClick(window, Qt.Key_Escape)
    assert not window.isVisible() and window.player.playbackState().name == "StoppedState"
    print("PASS: Chinese text, Unicode image path, PDF native backing, WAV decode, audio/video duration before playback, paused video poster without autoplay, explicit playback, selection navigation, Escape close")
