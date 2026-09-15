# Files and preview refinement — round 03

Source changes address the round-02 critic. **Installed desktop screenshots still require root's next build/boot review.** No guest preferences or GUI were changed while developing these changes.

## Preview

- File sizes now use 1024-based KiB/MiB/GiB, matching Dolphin. The 86,100-byte example is 84.1 KiB.
- Common supported image, PDF, plain text, JSON/XML, video and audio descriptions have Simplified/Traditional Chinese labels. Other languages and formats retain Qt's native MIME comment.
- QPdfView's local `Dark` palette role inherits the window surface; Qt paints that role behind pages. Document pixels and embedded typography are unchanged.
- Video calls `pause()` immediately after `setSource()`. Qt 6.11.2's FFmpeg backend accepts the paused request during loading and decodes a first frame without calling `play()`. It stays at position zero until an explicit playback action. Audio-only files remain stopped.

The actual Qt backend smoke test decoded the bundled VP8/Vorbis Flower video, obtained a valid first frame while paused, observed no PlayingState before Space, verified a stationary position zero, then verified explicit playback and Escape stop. This is engineering evidence, not an OS visual or audio-quality judgment.

### Follow-up: duration before playback

The actual round-03 poster screenshot exposed a stale `0:00 / 0:00` label: duration discovery updated the seek range but the label waited for a position change. The source now refreshes the label on `durationChanged` too. Qt 6.11.2 smoke verifies `0:00 / 0:01` for stopped WAV audio and `0:00 / 0:05` for the paused Flower poster before any playback. This follow-up awaits root's next installation and screenshot; it is not present in the original round-03 capture.

## Native Places defaults

`system_places.py` reads Solid's public diagnostic inventory and `findmnt` JSON. It only classifies an Atomic read-only root and positively identified fixed boot volumes at `/boot` or `/boot/efi`. Unknown/removable/hot-pluggable devices stay visible. Any block device with another mount, including `/home` or `/var/home`, stays visible.

The observed Aven guest classifies exactly:

- `/org/kde/fstab/overlay/` → read-only composefs root `/` (the unnamed red capacity bar).
- `/org/freedesktop/UDisks2/block_devices/vda2` → `/boot`, UUID `4b830106-0b30-4312-8465-64918a4e031a`.

The Btrfs device containing `/var/home` is retained. No label, mount, device-access rule, capacity-warning policy or udev configuration changes.

`places.py` writes native XBEL device separators containing `UDI`, `uuid`, `isSystemItem` and `IsHidden`. UUID matching takes precedence over reusable device identifiers. Explicit `IsHidden=false` choices and custom bookmarks survive. The original XBEL is backed up once. KDE's Show Hidden Places can reveal these system entries.

Solid 6.30's CLI returns its successful `hwList()` boolean directly as exit status 1; the reader accepts that documented source behavior only with a valid typed inventory. Missing or unrecognized inventory produces no device defaults.

## Validation and remaining inspection

- 10 preview boundary tests passed.
- 12 Files tests passed, including custom-bookmark/explicit-visibility preservation, UUID reuse, shared root/home storage, removable/hot-pluggable/unknown drives, and native shortcut preservation.
- Qt 6.11.2 offscreen render/decode smoke passed. No offscreen image is counted as a desktop screenshot.
- Read-only actual guest inventory selected only `/` and `/boot`.

After root installs and reboots: inspect SC and TC preview footers, settled PDF backing, video poster before Space, keyboard playback/close, and native sidebar. Confirm hidden system entries can be revealed and the Btrfs user-volume capacity indication remains available. Recheck preview launch and focus return through Dolphin.

## Primary implementation references

- [KIO 6.30 device bookmark schema and IsHidden](https://github.com/KDE/kio/blob/v6.30.0/src/filewidgets/kfileplacesitem.cpp).
- [KIO 6.30 UUID-first matching](https://github.com/KDE/kio/blob/v6.30.0/src/filewidgets/kfileplacesmodel.cpp).
- [Solid 6.30 diagnostic command and return behavior](https://github.com/KDE/solid/blob/v6.30.0/src/tools/solid-hardware/solid-hardware.cpp).
- [Qt 6.11.2 PDF backing palette](https://github.com/qt/qtwebengine/blob/v6.11.2/src/pdfwidgets/qpdfview.cpp).
- [Qt 6.11.2 FFmpeg pause handling](https://github.com/qt/qtmultimedia/blob/v6.11.2/src/plugins/multimedia/ffmpeg/qffmpegmediaplayer.cpp).
