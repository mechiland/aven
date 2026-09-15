# Photos — native Gwenview integration

## Decision

Use Fedora's native **Gwenview** for folder browsing and everyday viewing. It
already provides KDE file operations, thumbnail browsing, fit/zoom, EXIF
orientation, color management and fullscreen viewing. It inherits Aven's native
Noto font, icons, palette and window decoration. Its quality and integration are
inspected in paired native screenshots. Round 4 photo experience scored **8.0**;
native navigation and paired transitions are verified in [the final review](critic-round-04.md).

| Candidate | Scope fit | Prototype decision |
| --- | --- | --- |
| [Gwenview](https://apps.kde.org/gwenview/) | Folder browser/viewer, small edits, native KDE integration | Selected. Small configuration profile; no fork. |
| [Loupe](https://apps.gnome.org/Loupe/) | Focused viewing and quick edits; [sibling-file navigation](https://help.gnome.org/loupe/opening-images.html) | Credible viewing alternative. Its GNOME/GTK chrome would need separate integration, and Gwenview already covers the folder scenario. |
| [digiKam](https://www.digikam.org/about/features/) | Catalog/database, RAW workflow, collection search and extensive editing | Mature, but the catalog workflow adds scope this prototype does not need. |

These are capability and integration decisions based on current primary sources,
not scored visual comparisons of applications we have not booted.

## Profile

`photos/profile.py` uses public Gwenview settings checked against KDE's
[25.12.3 schema](https://github.com/KDE/gwenview/blob/v25.12.3/lib/gwenviewconfig.kcfg)
and the installed [26.08.1 schema](https://github.com/KDE/gwenview/blob/v26.08.1/lib/gwenviewconfig.kcfg).

- Thumbnail grid follows the shared `icon.photoGrid` token (240 logical pixels).
  Filenames remain visible; the hover overlay offers only the selection button.
- A single horizontal thumbnail strip provides context while viewing a photo.
  The metadata sidebar is available on demand. Breadcrumb navigation stays native.
- The viewing surface follows the current KDE palette; fullscreen uses black.
  The image's pixels are never tinted to match the theme.
- Every new photo fits in the viewport. Small files do not upscale by default.
  EXIF orientation and upstream color management remain enabled.
- Transparency gets a checkerboard so alpha is understandable. Wheel scrolling
  pans at zoom; keyboard/thumbnail controls move between images. Videos appear
  in the folder but do not start playing merely by being selected.
- Standard profile retains Gwenview's software crossfade. The checked
  [upstream source](https://github.com/KDE/gwenview/blob/v25.12.3/lib/documentview/documentview.cpp#L98)
  sets **250 ms**; the 120 ms Aven token is a target that this configuration cannot
  apply. Reduced-motion installation disables image animation. A recording must
  decide whether the upstream fade is acceptable before any motion claim.

Menu/control metrics remain native Breeze. There is no custom photo app, QSS,
binary patch, cloned macOS theme or separate photo-specific Noto override. Root
owns shared Plasma/KWin defaults, global fonts, icons and colors.

## Baseline and integration

Use exactly the same native package versions and fixtures in both guests. If
Gwenview or `qt6-qtimageformats` is missing, root must add and record it through
the Atomic image/package workflow **before capturing the stock photos scenario**.
Do not bypass rpm-ostree or replace a deployment for this profile.

Inside stock, once the repository is copied into the guest:

```sh
python3 photos/copy-fixtures.py --home /home/aven
gwenview /home/aven/Pictures/日常影像
gwenview /home/aven/Pictures/日常影像/00-地出-Earthrise.jpg
```

Capture the folder and ordinary photo view before installing preferences.
The root can also reuse the JPEG, transparent PNG and WebM bytes in Dolphin's
mixed-file folder and file-preview checks. Provenance is in
[`fixtures/photos/ATTRIBUTION.md`](../fixtures/photos/ATTRIBUTION.md).

Inside Aven **after the stock evidence is complete**, close Gwenview:

```sh
python3 photos/install.py --home /home/aven
python3 photos/audit.py --home /home/aven --active
```

Install seeds once, preserves all unrelated keys, and backs up a previous
`gwenviewrc`. Repeat use retains user changes; `--refresh` reapplies only the
managed defaults. Pass `--reduced-motion --refresh` to disable fades. To undo,
close Gwenview and restore the `.config/gwenviewrc.pre-aven-*` backup; if no
previous config existed, remove the seeded config and the photos marker.

Root sets image JPEG/PNG/WebP associations to `org.kde.gwenview.desktop` through
its shared integration. Do not assume optional HEIC/AVIF decoders are present;
record and test those separately if needed, without replacing system codecs.

## Verification protocol and observed coverage

Use matched viewports and scales for future platform or image-format checks:

1. Browse `Pictures/日常影像`: Chinese filenames, no clipping, selected/hovered
   thumbnails, toolbar/breadcrumb coherence and portrait/landscape balance.
2. Open Earthrise from Dolphin, move to the next photo and back, toggle the
   thumbnail strip, and enter/exit fullscreen. Record the transition, including
   a cold image load. A screenshot does not prove responsiveness or motion.
3. Confirm EXIF-6 is landscape with “top” above; fit the portrait vertically;
   inspect PNG checkerboard at 800%; open WebM and start playback deliberately.
4. Zoom/pan, open the metadata sidebar, then move to the next photo to verify
   autofit. Copy a fixture to a disposable folder before testing rotate/save,
   delete/undo or other editing operations. Do not mutate the evidence originals.
5. Inspect real Chinese menus and mixed filenames under the same Chinese locale
   as the other Aven evidence. Judge text from UI glyphs, not EXIF label pixels.

Current round 4 evidence includes the native album, landscape, EXIF-6 and alpha
fixtures, plus a matched 800% alpha view. Native next/previous and fullscreen
checks passed, and the critic inspected the paired image transitions. See the
[comparison index](COMPARISON.md) and
[native operation report](../evidence/interaction/aven-round04-native-verification.json).
Photo comparisons use 1×; the four-scale typography matrix uses Dolphin and
Firefox. Rotation/save and every possible image format were not tested. Source
keys and fixture hashes establish reproducibility, not calibrated color accuracy.
The VM has no calibrated physical display.

## Round3 native sizing correction

Browse thumbnails now seed240 logicalpx. `[ImageView] ThumbnailSplitterSizes=680,88` seeds a smaller horizontal filmstrip while keeping it visible. Gwenview saves actual window-dependent splitter sizes; the audit treats these as mutable layout state. Confirmed against native26.08.1 schema and `app/viewmainpage.cpp`. Screenshot comparison must judge actual photo size and both landscape/portrait layouts.
