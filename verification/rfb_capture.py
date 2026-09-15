#!/usr/bin/env python3
"""Capture unmodified QEMU VNC pixels with a read-only, raw-encoding RFB client.

For QEMU GL scanout where QMP screendump reports 'no surface'. Sends no keys,
pointer events or clipboard. PNG encoding is lossless and performs no resizing,
color correction, cropping, overlay or annotation. This is real VM evidence.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import socket
import struct
import time
import zlib

METHOD = "QEMU VNC RFB raw framebuffer; unmodified guest pixels, lossless PNG"
MAX_PIXELS = 32_000_000


def read_exact(stream, count):
    chunks = bytearray()
    while len(chunks) < count:
        chunk = stream.recv(count - len(chunks))
        if not chunk:
            raise RuntimeError("RFB connection closed before a complete framebuffer")
        chunks.extend(chunk)
    return bytes(chunks)


def png_bytes(width, height, rgb, compression=6):
    if len(rgb) != width * height * 3:
        raise ValueError("Invalid framebuffer length")
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    rows = b"".join(b"\x00" + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, compression)) + chunk(b"IEND", b"")


def capture(port, timeout=20):
    deadline = time.monotonic() + timeout
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as stream:
        def read(count):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("RFB capture exceeded deadline")
            stream.settimeout(remaining)
            return read_exact(stream, count)
        version = read(12)
        if version != b"RFB 003.008\n":
            raise RuntimeError(f"Expected QEMU RFB 3.8, got {version!r}")
        stream.sendall(b"RFB 003.008\n")
        count = read(1)[0]
        if count == 0:
            raise RuntimeError("QEMU rejected RFB connection")
        security_types = read(count)
        if 1 not in security_types:
            raise RuntimeError("Requires loopback QEMU lab VNC with no authentication")
        stream.sendall(b"\x01")
        if struct.unpack(">I", read(4))[0] != 0:
            raise RuntimeError("RFB security negotiation failed")
        stream.sendall(b"\x01")  # Shared viewer; never disconnect other clients.
        initial = read(24)
        width, height = struct.unpack(">HH", initial[:4])
        name_length = struct.unpack(">I", initial[20:24])[0]
        if name_length > 4096:
            raise RuntimeError("Unexpected RFB desktop name size")
        server_name = read(name_length).decode("utf-8", errors="replace")
        # Request true-color RGB in explicit little-endian 32bpp storage.
        pixel_format = struct.pack(">BBBBHHHBBBxxx", 32, 24, 0, 1, 255, 255, 255, 16, 8, 0)
        stream.sendall(b"\x00\x00\x00\x00" + pixel_format)
        stream.sendall(struct.pack(">BBHii", 2, 0, 2, 0, -223))  # Raw + desktop resize.
        for attempt in range(3):
            if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
                raise RuntimeError("Unexpected framebuffer dimensions")
            rgb = bytearray(width * height * 3)
            covered = bytearray(width * height)
            stream.sendall(struct.pack(">BBHHHH", 3, 0, 0, 0, width, height))
            resized = False
            while True:
                message = read(1)[0]
                if message == 2:  # Server bell; no client input response.
                    continue
                if message == 3:  # Ignore server clipboard contents.
                    length = struct.unpack(">I", read(7)[3:])[0]
                    if length > 1024 * 1024:
                        raise RuntimeError("Unexpected RFB clipboard size")
                    read(length)
                    continue
                if message != 0:
                    raise RuntimeError(f"Unsupported RFB server message {message}")
                rectangles = struct.unpack(">H", read(3)[1:])[0]
                for _ in range(rectangles):
                    x, y, w, h, encoding = struct.unpack(">HHHHi", read(12))
                    if encoding == -223:
                        width, height, resized = w, h, True
                        continue
                    if encoding != 0:
                        raise RuntimeError(f"Unexpected RFB encoding {encoding}; raw was requested")
                    if w * h > MAX_PIXELS:
                        raise RuntimeError("Unexpected RFB rectangle size")
                    raw = read(w * h * 4)
                    if resized:
                        continue
                    if x + w > width or y + h > height:
                        raise RuntimeError("RFB rectangle exceeds framebuffer")
                    # Channel packing only. Numeric color values are untouched.
                    packed = bytearray(w * h * 3)
                    packed[0::3], packed[1::3], packed[2::3] = raw[2::4], raw[1::4], raw[0::4]
                    for row in range(h):
                        start = ((y + row) * width + x) * 3
                        rgb[start:start + w * 3] = packed[row * w * 3:(row + 1) * w * 3]
                        begin = (y + row) * width + x
                        covered[begin:begin + w] = b"\x01" * w
                if resized:
                    break
                if all(covered):
                    return bytes(rgb), {"method": METHOD, "width": width, "height": height,
                        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "rfb_version": version.decode().strip(), "server_name": server_name,
                        "endpoint": f"127.0.0.1:{port}", "encoding": "raw 32-bit true-color converted losslessly to PNG RGB24",
                        "input_events_sent": 0}
                # Some servers split a non-incremental request into updates.
                stream.sendall(struct.pack(">BBHHHH", 3, 0, 0, 0, width, height))
        raise RuntimeError("Display kept changing size during capture")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, choices=[5920, 5921], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args()
    if args.timeout <= 0 or args.timeout > 60:
        parser.error("timeout must be between 0 and 60 seconds")
    if args.output.exists() or args.output.with_suffix(".rfb.json").exists():
        parser.error("Refusing to overwrite existing capture or provenance")
    try:
        rgb, metadata = capture(args.port, args.timeout)
        encoded = png_bytes(metadata["width"], metadata["height"], rgb)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as output:
            output.write(encoded)
        metadata.update(image=str(args.output), sha256=hashlib.sha256(encoded).hexdigest())
        args.output.with_suffix(".rfb.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
