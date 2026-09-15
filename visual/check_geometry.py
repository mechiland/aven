#!/usr/bin/env python3
"""Check native QtSvg geometry after a decoration SVG change.

Run in the Fedora guest (python3-pyside6) or a Qt-equipped build environment.
No windows, compositor calls or filesystem writes. This catches the actual
FrameSvg regression where a stroke enlarges one slice but not its mask.
It does not replace desktop screenshots or native interaction verification.
"""
import sys
from pathlib import Path

from PySide6.QtSvg import QSvgRenderer


def check(data: bytes) -> None:
    renderer = QSvgRenderer(data)
    assert renderer.isValid(), "Invalid decoration SVG"
    geometry = {
        "topleft": (0, 0, 34, 34), "top": (34, 0, 92, 34), "topright": (126, 0, 34, 34),
        "left": (0, 34, 34, 92), "center": (34, 34, 92, 92), "right": (126, 34, 34, 92),
        "bottomleft": (0, 126, 34, 34), "bottom": (34, 126, 92, 34), "bottomright": (126, 126, 34, 34),
    }
    for prefix, offset in (("decoration", 0), ("decoration-inactive", 180), ("mask", 360)):
        for part, (x, y, width, height) in geometry.items():
            element = f"{prefix}-{part}"
            assert renderer.elementExists(element), f"Missing {element}"
            rect = renderer.boundsOnElement(element)
            actual = (rect.x(), rect.y(), rect.width(), rect.height())
            expected = (x + offset, y, width, height)
            assert all(abs(a - b) < 0.001 for a, b in zip(actual, expected)), (
                f"{element}: got {actual}, expected {expected}"
            )
    assert renderer.elementExists("hint-stretch-borders"), "Missing stretch hint"
    print("PASS: all 27 QtSvg slices have exact shared bounds; stretch hint present.")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "aurorae/Aven/decoration.svg"
    check(path.read_bytes())
