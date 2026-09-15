# Consumer photo album: 京都春日

Eight natural, unannotated travel photographs form a small springtime Kyoto
album: tree-lined paths, a temple garden, river views, cherry blossoms and
ordinary streets. All photographs are CC0, published by their photographers on
Wikimedia Commons. The five landscape and three portrait images total
**2,909,642 bytes**. They were individually inspected for content, orientation
and absence of diagnostic labels or watermarks.

The existing `fixtures/photos/` EXIF, alpha, Earthrise and video fixtures remain
unchanged. Use them for functional tests. Use this album for consumer browsing
and viewing screenshots, with identical content in stock and Aven.

After copying the repository into either guest:

```sh
python3 photos/copy-album.py --home /home/aven
python3 photos/copy-album.py --home /home/aven --verify
gwenview /home/aven/Pictures/京都春日
```

Suggested ordinary viewer captures:

```sh
gwenview /home/aven/Pictures/京都春日/06-山间河流.jpg
gwenview /home/aven/Pictures/京都春日/03-庭院倒影.jpg
```

This helper changes no desktop/application settings and refuses to overwrite
an existing modified photo. Credits, CC0 terms and hashes accompany the guest
album in `.attribution/`. Its source files live in `fixtures/photos-album/`.

Use the same folder, image and window bounds for each stock/Aven comparison.
The thumbnails' Chinese filenames are real UI text; signs photographed in the
street scenes are image pixels and must not be scored as Aven font rendering.
The album is fixture content, not evidence that the desktop is visually polished.
