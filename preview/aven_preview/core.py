"""Local-file boundary and bounded text loading for the Aven preview extension."""

from __future__ import annotations

import codecs
import os
from pathlib import Path
import re
import stat
from urllib.parse import unquote, urlsplit

MAX_TEXT_BYTES = 1024 * 1024
MAX_SELECTION = 64
CJK_TEXT = re.compile(r"[\u2e80-\ua000\uf900-\ufaff\uff00-\uffef\U00020000-\U000323af]")


def reading_metrics(text: str) -> tuple[int, float]:
    """Owned prose roles from typography/roles.json, in Qt logical pixels."""
    return (17, 1.75) if CJK_TEXT.search(text) else (16, 1.65)


class PreviewError(ValueError):
    """A user-readable reason a preview cannot be loaded."""


def local_path(argument: str) -> Path:
    """Decode a file URL once; literal paths retain %, #, newline and Unicode."""
    if argument.startswith("file:"):
        url = urlsplit(argument)
        if url.netloc not in ("", "localhost") or url.query or url.fragment:
            raise PreviewError("This preview supports local files only.")
        try:
            path = Path(unquote(url.path, encoding="utf-8", errors="strict"))
        except UnicodeError as error:
            raise PreviewError("This file name cannot be decoded.") from error
    elif "://" in argument:
        raise PreviewError("Save this file locally to preview it.")
    else:
        path = Path(argument)
    if not str(path) or "\x00" in str(path):
        raise PreviewError("This file name is not valid.")
    path = path.absolute()
    try:
        info = path.stat()
    except OSError as error:
        raise PreviewError("This file is unavailable or cannot be read.") from error
    if not stat.S_ISREG(info.st_mode):
        raise PreviewError("Select a file to preview.")
    if not os.access(path, os.R_OK):
        raise PreviewError("This file cannot be read.")
    return path


def selection(arguments: list[str]) -> list[Path]:
    if not arguments:
        raise PreviewError("Select a file in Files, then press Ctrl+Alt+P.")
    if len(arguments) > MAX_SELECTION:
        raise PreviewError("Select up to 64 files to preview together.")
    return list(dict.fromkeys(local_path(argument) for argument in arguments))


def read_text(path: Path) -> tuple[str, bool]:
    # O_NONBLOCK prevents a file replaced by a FIFO between validation and open
    # from hanging the preview. fstat validates the actual opened descriptor.
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise PreviewError("Select a regular file to preview.")
        data = stream.read(MAX_TEXT_BYTES + 1)
    truncated = len(data) > MAX_TEXT_BYTES
    data = data[:MAX_TEXT_BYTES]
    encoding = "utf-8-sig"
    if data.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        encoding = "utf-32"
    elif data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        encoding = "utf-16"
    try:
        # final=False preserves a partial codepoint at the intentional size limit.
        decoder = codecs.getincrementaldecoder(encoding)(errors="strict")
        text = decoder.decode(data, final=not truncated)
    except UnicodeError as error:
        raise PreviewError("This text encoding needs the full application.") from error
    if "\x00" in text:
        raise PreviewError("A text preview is not available for this file.")
    return text, truncated


def human_size(byte_count: int) -> str:
    """IEC units, matching Dolphin's default file-size convention."""
    size = float(byte_count)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"):
        if size < 1024 or unit == "EiB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
