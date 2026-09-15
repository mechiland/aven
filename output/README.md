# Aven prototype handoff

- `aven-prototype-round04.qcow2`: standalone compressed 48 GiB virtual disk.
- `aven-source-and-evidence-round04.tar.gz`: source, fixtures, original before/after
  screenshots, operation and motion records, and independent reviews.
- `BUILD.json`: build identity, artifact hashes, disk checks and acceptance result.

Read [TRY.md](../docs/TRY.md) to boot a writable test overlay or connect to the
existing laboratory guest. Start the visual review with
[COMPARISON.md](../docs/COMPARISON.md). The evidence archive extracts into an
`aven/` directory; place this handoff's disk and manifest in its `output/`
directory to use the documented commands.

The image is a focused laboratory prototype on Fedora Kinoite. It retains the
native Dolphin, Firefox, Thunderbird and Gwenview applications and adds a small
read-only file-preview extension. Lab autologin and passwordless sudo are
recorded in the build guide. Private VM SSH keys and the downloaded Fedora ISO
are excluded from the archive.
