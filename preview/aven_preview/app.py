"""A thin Qt renderer container, not a file manager or photo application.

Dolphin supplies the selected URLs through a normal KIO service menu. Qt owns
image, PDF and multimedia decoding; this module supplies one disposable window.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QLocale, QMargins, QMimeDatabase, QRectF, QSize, Qt, QUrl
from PySide6.QtGui import (
    QColorSpace, QDesktopServices, QFont, QIcon, QImageReader, QKeySequence, QPainter,
    QPalette, QShortcut, QTextBlockFormat, QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QSlider, QTextEdit, QVBoxLayout, QWidget,
)

from .core import PreviewError, human_size, read_text, reading_metrics, selection


def label(en: str, zh: str, tw: str | None = None) -> str:
    name = QLocale.system().name()
    if name.startswith(("zh_TW", "zh_HK", "zh_MO")):
        return tw or zh
    return zh if name.startswith("zh") else en


def mime_label(mime) -> str:
    """Translate the small set of formats that this extension owns.

    Qt's shared MIME database can return English comments in a Chinese session.
    Keep its precise native description for other formats and other languages.
    """
    if not QLocale.system().name().startswith("zh"):
        return mime.comment()
    name = mime.name()
    formats = {
        "image/jpeg": ("JPEG 图像", "JPEG 影像"),
        "image/png": ("PNG 图像", "PNG 影像"),
        "image/gif": ("GIF 图像", "GIF 影像"),
        "image/webp": ("WebP 图像", "WebP 影像"),
        "image/svg+xml": ("SVG 图像", "SVG 影像"),
        "application/pdf": ("PDF 文档", "PDF 文件"),
        "text/plain": ("纯文本", "純文字"),
        "application/json": ("JSON 文档", "JSON 文件"),
        "application/xml": ("XML 文档", "XML 文件"),
        "text/xml": ("XML 文档", "XML 文件"),
        "video/webm": ("WebM 视频", "WebM 影片"),
        "video/mp4": ("MPEG-4 视频", "MPEG-4 影片"),
        "audio/mpeg": ("MP3 音频", "MP3 音訊"),
        "audio/x-wav": ("WAV 音频", "WAV 音訊"),
        "audio/flac": ("FLAC 音频", "FLAC 音訊"),
    }
    translated = formats.get(name)
    if translated is None:
        for prefix, values in (("image/", ("图像", "影像")), ("video/", ("视频", "影片")), ("audio/", ("音频", "音訊")), ("text/", ("文本", "文字"))):
            if name.startswith(prefix):
                translated = values
                break
    return label(mime.comment(), *translated) if translated else mime.comment()


class ImageCanvas(QWidget):
    def __init__(self, path: Path, parent: QWidget):
        super().__init__(parent)
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        reader.setAllocationLimit(256)
        original = reader.size()
        if original.isValid() and max(original.width(), original.height()) > 4096:
            reader.setScaledSize(original.scaled(QSize(4096, 4096), Qt.KeepAspectRatio))
        self.image = reader.read()
        if self.image.isNull():
            raise PreviewError(label("This image cannot be previewed.", "无法预览此图像。", "無法預覽此影像。"))
        if self.image.colorSpace().isValid():
            self.image = self.image.convertedToColorSpace(QColorSpace(QColorSpace.SRgb))
        self.setMinimumSize(240, 180)
        self.setAccessibleName(label("Image preview", "图像预览", "影像預覽"))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().base())
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        bounds = self.rect().adjusted(24, 24, -24, -24)
        size = self.image.size().scaled(bounds.size(), Qt.KeepAspectRatio)
        target = QRectF(0, 0, size.width(), size.height())
        target.moveCenter(QRectF(bounds).center())
        painter.drawImage(target, self.image)


class PreviewWindow(QMainWindow):
    def __init__(self, paths: list[Path], error: str | None = None):
        super().__init__()
        self.paths = paths
        self.index = 0
        self.renderer: QWidget | None = None
        self.player = None
        self.pdf = None
        self.setObjectName("aven-preview")
        self.setWindowIcon(QIcon.fromTheme("document-preview"))
        self.setMinimumSize(460, 360)
        available = QApplication.primaryScreen().availableGeometry()
        self.resize(min(880, int(available.width() * .8)), min(680, int(available.height() * .82)))
        self.move(available.center() - self.rect().center())

        root = QWidget(self)
        self.setCentralWidget(root)
        self.layout = QVBoxLayout(root)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.content = QWidget(root)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.content, 1)

        footer = QFrame(root)
        footer.setObjectName("previewFooter")
        footer.setStyleSheet("#previewFooter { border-top: 1px solid palette(midlight); }")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(18, 10, 18, 10)
        footer_layout.setSpacing(10)
        self.previous = self.button("go-previous", label("Previous selected file", "上一个所选文件", "上一個所選檔案"), lambda: self.navigate(-1))
        self.next = self.button("go-next", label("Next selected file", "下一个所选文件", "下一個所選檔案"), lambda: self.navigate(1))
        footer_layout.addWidget(self.previous)
        footer_layout.addWidget(self.next)
        self.meta = QLabel(footer)
        self.meta.setTextFormat(Qt.PlainText)
        self.meta.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        palette = self.meta.palette()
        palette.setColor(QPalette.WindowText, palette.color(QPalette.PlaceholderText))
        self.meta.setPalette(palette)
        footer_layout.addWidget(self.meta, 1)
        self.open_button = QPushButton(label("Open", "打开", "開啟"), footer)
        self.open_button.setIcon(QIcon.fromTheme("document-open"))
        self.open_button.setMinimumHeight(32)
        self.open_button.setToolTip(label("Open in the default application (Enter)", "在默认应用中打开（Enter）", "在預設應用程式中開啟（Enter）"))
        self.open_button.clicked.connect(self.open_file)
        footer_layout.addWidget(self.open_button)
        self.layout.addWidget(footer)
        for keys, action in (("Escape", self.close), ("Ctrl+Alt+P", self.close), ("Space", self.space), ("Return", self.open_file), ("Enter", self.open_file), ("Alt+Left", lambda: self.navigate(-1)), ("Alt+Right", lambda: self.navigate(1))):
            shortcut = QShortcut(QKeySequence(keys), self)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(action)
        if paths:
            self.load()
        else:
            self.setWindowTitle(label("Preview", "预览", "預覽"))
            self.message(error or label("Select a file to preview.", "请选择要预览的文件。", "請選擇要預覽的檔案。"))
            self.open_button.setEnabled(False)
            self.previous.hide()
            self.next.hide()

    def button(self, icon, title, callback):
        button = QPushButton(QIcon.fromTheme(icon), "", self)
        button.setAccessibleName(title)
        button.setToolTip(title)
        button.setFixedSize(32, 32)
        button.clicked.connect(callback)
        return button

    def reset_renderer(self):
        if self.player:
            self.player.stop()
            self.player.setSource(QUrl())
            self.player.deleteLater()
            self.player = None
        if self.pdf:
            self.pdf.close()
            self.pdf.deleteLater()
            self.pdf = None
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.renderer = None

    def message(self, text):
        view = QLabel(text, self.content)
        view.setTextFormat(Qt.PlainText)
        view.setAlignment(Qt.AlignCenter)
        view.setWordWrap(True)
        view.setContentsMargins(48, 48, 48, 48)
        self.content_layout.addWidget(view)
        self.renderer = view

    def load(self):
        self.reset_renderer()
        path = self.paths[self.index]
        self.setWindowTitle(f"{path.name} — {label('Preview', '预览', '預覽')}")
        self.previous.setVisible(len(self.paths) > 1)
        self.next.setVisible(len(self.paths) > 1)
        self.previous.setEnabled(self.index > 0)
        self.next.setEnabled(self.index < len(self.paths) - 1)
        prefix = f"{self.index + 1} / {len(self.paths)}   ·   " if len(self.paths) > 1 else ""
        try:
            # Recheck on every load: removable storage may disappear while open.
            path = selection([str(path)])[0]
            mime = QMimeDatabase().mimeTypeForFile(str(path))
            self.meta.setText(prefix + f"{mime_label(mime)}   ·   {human_size(path.stat().st_size)}")
            self.meta.setToolTip(label("Esc closes preview · Ctrl+Alt+P toggles", "Esc 关闭预览 · Ctrl+Alt+P 切换预览", "Esc 關閉預覽 · Ctrl+Alt+P 切換預覽"))
            if mime.name().startswith("image/"):
                self.renderer = ImageCanvas(path, self.content)
            elif mime.name() == "application/pdf":
                self.renderer = self.pdf_view(path)
            elif mime.name().startswith(("audio/", "video/")):
                self.renderer = self.media_view(path, mime.name().startswith("video/"))
            elif mime.inherits("text/plain") or mime.name() in ("application/json", "application/xml", "application/javascript", "application/x-desktop", "application/x-shellscript"):
                self.renderer = self.text_view(path)
            else:
                self.message(label("A preview is not available for this file.\nOpen it in its application to continue.", "此文件暂不支持预览。\n请在应用中打开。", "此檔案暫不支援預覽。\n請在應用程式中開啟。"))
                return
            self.content_layout.addWidget(self.renderer)
        except (OSError, PreviewError, ImportError) as error:
            self.message(str(error))

    def text_view(self, path):
        text, truncated = read_text(path)
        view = QTextEdit(self.content)
        view.setReadOnly(True)
        view.setAcceptRichText(False)
        view.setFrameShape(QFrame.NoFrame)
        view.document().setDocumentMargin(28)
        pixel_size, line_height = reading_metrics(text)
        font = QFont(QApplication.font())
        font.setPixelSize(pixel_size)
        font.setWeight(QFont.Normal)
        view.setFont(font)
        view.setPlainText(text)
        cursor = QTextCursor(view.document())
        cursor.select(QTextCursor.Document)
        block = QTextBlockFormat()
        # QTextBlockFormat.ProportionalHeight multiplies the font's entire
        # native line box, whereas the prose token multiplies its em size.
        # A minimum em-based line height matches CSS and avoids tall-glyph clipping.
        block.setLineHeight(pixel_size * line_height, QTextBlockFormat.MinimumHeight.value)
        cursor.mergeBlockFormat(block)
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.Start)
        view.setTextCursor(cursor)
        view.setAccessibleName(label("Read-only text preview", "只读文本预览", "唯讀文字預覽"))
        if truncated:
            self.meta.setText(label("First 1 MiB · Open to read the full file", "显示前 1 MiB · 打开以阅读全文", "顯示前 1 MiB · 開啟以閱讀全文"))
        return view

    def pdf_view(self, path):
        from PySide6.QtPdf import QPdfDocument
        from PySide6.QtPdfWidgets import QPdfView
        self.pdf = QPdfDocument(self)
        result = self.pdf.load(str(path))
        if result != QPdfDocument.Error.None_:
            if result == QPdfDocument.Error.IncorrectPassword:
                raise PreviewError(label("Open this PDF in its application to enter its password.", "请在应用中打开此 PDF 并输入密码。", "請在應用程式中開啟此 PDF 並輸入密碼。"))
            raise PreviewError(label("This PDF cannot be previewed.", "无法预览此 PDF。", "無法預覽此 PDF。"))
        view = QPdfView(self.content)
        # QPdfView paints its backing with QPalette.Dark. Use this window's
        # native chrome surface for that role; document pixels stay untouched.
        palette = view.palette()
        palette.setColor(QPalette.Dark, palette.color(QPalette.Window))
        view.setPalette(palette)
        view.setDocument(self.pdf)
        view.setPageMode(QPdfView.PageMode.MultiPage)
        view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        view.setDocumentMargins(QMargins(24, 24, 24, 24))
        view.setPageSpacing(20)
        view.setAccessibleName(label("PDF preview", "PDF 预览", "PDF 預覽"))
        return view

    def media_view(self, path, video):
        from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
        from PySide6.QtMultimediaWidgets import QVideoWidget
        container = QWidget(self.content)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(16)
        self.player = QMediaPlayer(self)
        output = QAudioOutput(self.player)
        output.setVolume(.7)
        self.player.setAudioOutput(output)
        if video:
            view = QVideoWidget(container)
            view.setAspectRatioMode(Qt.KeepAspectRatio)
            self.player.setVideoOutput(view)
        else:
            view = QLabel(container)
            view.setAlignment(Qt.AlignCenter)
            view.setPixmap(QIcon.fromTheme("audio-x-generic").pixmap(96, 96))
        layout.addWidget(view, 1)
        row = QHBoxLayout()
        play = self.button("media-playback-start", label("Play or pause (Space)", "播放或暂停（空格）", "播放或暫停（空白鍵）"), self.space)
        row.addWidget(play)
        slider = QSlider(Qt.Horizontal, container)
        slider.setRange(0, 0)
        slider.setAccessibleName(label("Playback position", "播放位置", "播放位置"))
        row.addWidget(slider, 1)
        position = QLabel("0:00 / 0:00", container)
        position.setObjectName("playbackTime")
        row.addWidget(position)
        layout.addLayout(row)
        player = self.player
        duration = lambda milliseconds: f"{milliseconds // 60000}:{milliseconds // 1000 % 60:02d}"
        def update_position(value):
            if not slider.isSliderDown():
                slider.setValue(value)
            position.setText(f"{duration(value)} / {duration(player.duration())}")
        def update_duration(value):
            slider.setRange(0, value)
            # Loading a stopped audio file or a paused video poster can discover
            # duration without changing position. Refresh both halves now.
            update_position(player.position())
        player.durationChanged.connect(update_duration)
        player.positionChanged.connect(update_position)
        player.playbackStateChanged.connect(lambda state: play.setIcon(QIcon.fromTheme("media-playback-pause" if state == QMediaPlayer.PlayingState else "media-playback-start")))
        slider.sliderMoved.connect(player.setPosition)
        player.errorOccurred.connect(lambda *_: self.meta.setText(label("This media needs a supported codec · Open in application", "此媒体需要支持的编解码器 · 请在应用中打开", "此媒體需要支援的編解碼器 · 請在應用程式中開啟")))
        player.setSource(QUrl.fromLocalFile(str(path)))
        if video:
            # Qt's FFmpeg backend decodes the first frame while paused, including
            # when pause is requested during LoadingMedia. No play() call,
            # autoplay interval, audio pre-roll or second decoder is needed.
            player.pause()
        return container

    def navigate(self, delta):
        index = self.index + delta
        if 0 <= index < len(self.paths):
            self.index = index
            self.load()

    def space(self):
        if self.player:
            from PySide6.QtMultimedia import QMediaPlayer
            self.player.pause() if self.player.playbackState() == QMediaPlayer.PlayingState else self.player.play()
        else:
            self.close()

    def open_file(self):
        if self.paths:
            if QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.paths[self.index]))):
                self.close()

    def closeEvent(self, event):
        if self.player:
            self.player.stop()
        super().closeEvent(event)


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if arguments and arguments[0] == "--":
        arguments = arguments[1:]
    app = QApplication([sys.argv[0]])
    app.setApplicationName("aven-preview")
    app.setApplicationDisplayName(label("Preview", "预览", "預覽"))
    app.setDesktopFileName("org.aven.Preview")
    try:
        window = PreviewWindow(selection(arguments))
    except PreviewError as error:
        window = PreviewWindow([], str(error))
    window.show()
    return app.exec()
