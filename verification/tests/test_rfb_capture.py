"""RFB protocol tests with a local fake server; these are never desktop evidence."""
from pathlib import Path
import socket
import struct
import sys
import threading
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rfb_capture import capture, png_bytes, read_exact


class RFBTest(unittest.TestCase):
    def run_server(self, broken=False):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        failures = []
        def server():
            try:
                with listener, listener.accept()[0] as stream:
                    stream.settimeout(2)
                    stream.sendall(b"RFB 003.008\n")
                    self.assertEqual(read_exact(stream, 12), b"RFB 003.008\n")
                    stream.sendall(b"\x01\x01")
                    self.assertEqual(read_exact(stream, 1), b"\x01")
                    stream.sendall(b"\x00\x00\x00\x00")
                    self.assertEqual(read_exact(stream, 1), b"\x01")
                    name = b"unit-test-only"
                    stream.sendall(struct.pack(">HH", 2, 1) + bytes(16) + struct.pack(">I", len(name)) + name)
                    self.assertEqual(read_exact(stream, 20)[:4], b"\x00\x00\x00\x00")
                    self.assertEqual(read_exact(stream, 12), struct.pack(">BBHii", 2, 0, 2, 0, -223))
                    self.assertEqual(read_exact(stream, 10), struct.pack(">BBHHHH", 3, 0, 0, 0, 2, 1))
                    if broken:
                        return
                    # Two raw rectangles, red then green, in little-endian BGRX.
                    stream.sendall(struct.pack(">BBH", 0, 0, 2))
                    stream.sendall(struct.pack(">HHHHi", 0, 0, 1, 1, 0) + b"\x00\x00\xff\x00")
                    stream.sendall(struct.pack(">HHHHi", 1, 0, 1, 1, 0) + b"\x00\xff\x00\x00")
            except Exception as error:
                failures.append(error)
        thread = threading.Thread(target=server, daemon=True)
        thread.start()
        return port, thread, failures

    def test_raw_pixels_keep_numeric_rgb_values(self):
        port, thread, failures = self.run_server()
        rgb, metadata = capture(port, timeout=2)
        thread.join(2)
        self.assertFalse(failures)
        self.assertEqual(rgb, b"\xff\x00\x00\x00\xff\x00")
        self.assertEqual((metadata["width"], metadata["height"]), (2, 1))
        self.assertEqual(metadata["input_events_sent"], 0)
        png = png_bytes(2, 1, rgb)
        offset = 8
        while offset < len(png):
            length = struct.unpack(">I", png[offset:offset + 4])[0]
            if png[offset + 4:offset + 8] == b"IDAT":
                self.assertEqual(zlib.decompress(png[offset + 8:offset + 8 + length]), b"\x00" + rgb)
                break
            offset += length + 12
        else:
            self.fail("PNG has no pixel data")

    def test_incomplete_frame_never_becomes_image(self):
        port, thread, failures = self.run_server(broken=True)
        with self.assertRaisesRegex(RuntimeError, "complete framebuffer"):
            capture(port, timeout=2)
        thread.join(2)
        self.assertFalse(failures)


if __name__ == "__main__":
    unittest.main()
