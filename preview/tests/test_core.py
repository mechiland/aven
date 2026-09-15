import codecs
import os
from pathlib import Path
import tempfile
import unittest

from aven_preview.core import MAX_TEXT_BYTES, PreviewError, human_size, local_path, read_text, selection


class PreviewBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def file(self, name, data=b"hello"):
        path = self.root / name
        path.write_bytes(data)
        return path

    def test_unicode_spaces_percent_hash_newline_and_shell_metacharacters(self):
        for name in ("中文 空格 100%#?.txt", "繁體中文\n第二行.txt", "$(touch NEVER);`id` 'quoted'.txt", "--help.txt"):
            with self.subTest(name=name):
                path = self.file(name)
                self.assertEqual(local_path(str(path)), path)
                self.assertEqual(local_path(path.as_uri()), path)
        self.assertFalse((self.root / "NEVER").exists())

    def test_encoded_filename_is_decoded_once(self):
        path = self.file("%23.txt")
        self.assertEqual(local_path(path.as_uri()).name, "%23.txt")

    def test_remote_urls_and_nonregular_files_are_rejected(self):
        os.mkfifo(self.root / "pipe")
        for argument in ("https://example.com/a.txt", "smb://server/a.txt", "file://server/etc/passwd", str(self.root), str(self.root / "pipe"), "/dev/zero", str(self.root / "missing")):
            with self.subTest(argument=argument), self.assertRaises(PreviewError):
                local_path(argument)

    def test_regular_file_symlink_is_supported(self):
        path = self.file("中文.txt")
        link = self.root / "alias.txt"
        link.symlink_to(path)
        self.assertEqual(local_path(str(link)), link)
        self.assertEqual(read_text(link), ("hello", False))

    def test_selection_preserves_order_and_deduplicates(self):
        a, b = self.file("a"), self.file("b")
        self.assertEqual(selection([b.as_uri(), a.as_uri(), b.as_uri()]), [b, a])
        with self.assertRaises(PreviewError):
            selection([])
        with self.assertRaises(PreviewError):
            selection([a.as_uri()] * 65)

    def test_chinese_unicode_encodings_are_exact(self):
        text = "Aven：清晰的日常。繁體中文，Latin + 中文。😀\n"
        for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-32"):
            with self.subTest(encoding=encoding):
                self.assertEqual(read_text(self.file(encoding, text.encode(encoding))), (text, False))

    def test_large_text_is_bounded_at_a_codepoint(self):
        data = b"a" * (MAX_TEXT_BYTES - 1) + "中文".encode()
        text, truncated = read_text(self.file("large.txt", data))
        self.assertTrue(truncated)
        self.assertEqual(len(text), MAX_TEXT_BYTES - 1)
        self.assertNotIn("�", text)

    def test_binary_and_unknown_encoding_are_not_rendered_as_garbled_text(self):
        for data in (b"\x00\x01\x02", "中文".encode("gb18030")):
            with self.subTest(data=data), self.assertRaises(PreviewError):
                read_text(self.file("unknown.txt", data))

    def test_file_replaced_by_fifo_is_rejected_without_blocking(self):
        path = self.file("replaced.txt")
        local_path(str(path))
        path.unlink()
        os.mkfifo(path)
        with self.assertRaises(PreviewError):
            read_text(path)

    def test_sizes_match_dolphin_binary_units_at_boundaries(self):
        for count, expected in ((0, "0 B"), (1023, "1023 B"), (1024, "1.0 KiB"), (86100, "84.1 KiB"), (1048576, "1.0 MiB"), (1073741824, "1.0 GiB")):
            with self.subTest(count=count):
                self.assertEqual(human_size(count), expected)


if __name__ == "__main__":
    unittest.main()
