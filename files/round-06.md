# macOS 15 reference pass: Files, Photos and Preview

Inspected references:

- `/home/michael/Downloads/macOS15Screens/15-Sequoia-Applications.png`
- `/home/michael/Downloads/macOS15Screens/15-Sequoia-Photos.png`

Inspected real desktop evidence:

- `evidence/aven/round-05/union-files-sc-final-1x.png`
- `evidence/aven/round-05/union-preview-sc-final-1x.png`
- `evidence/aven/round-05/union-photos-native-1x.png`
- `evidence/aven/round-04/photos-grid-1x.png`

The reference Finder has a narrower gray sidebar and a simpler white content
surface. The reference Photos uses image-only thumbnail slots and a persistent
navigation sidebar. The previous Aven captures show larger toolbar text, a wide
white Places pane, photo filename captions, and a strongly framed photo path
strip. These observations motivated the changes below; they do not establish
the quality of the revised, uncaptured implementation.

## Changes

Files seeds a 184 logical pixel Places pane, 18 pixel Places/toolbar icons, 16
pixel detail icons and 24 pixel detail previews. Icon view uses 64 pixel icons
and 144 pixel previews. Both native toolbars use `IconOnly` while preserving
their actions, menus, shortcuts, tooltips and accessible names. Dolphin's
selection toggle overlay is disabled; native click, range and multiselection
remain available.

Photos keeps the 240 pixel grid target and changes its thumbnail slots to square
with no filename captions or hover buttons. Gwenview fits the original image
ratio inside each slot; this setting does not crop images. The native folders
sidebar starts at 208 pixels. Gwenview shares sidebar visibility between Browse
and windowed View modes; F4 can still hide it. Color management, EXIF orientation,
non-autoplay video handling and native operations remain enabled.

Preview uses 28 pixel footer buttons with 14/8 pixel margins. Its content face is
explicitly Noto Sans, preserving the separate 16 pixel Latin / 17 pixel Chinese
reading roles when the shell changes to a compact UI face. The asynchronous
native default-application handoff is unchanged.

## Apply to an existing profile

Close Dolphin and Gwenview first. Root owns guest deployment:

```sh
python3 files/install.py --home /home/aven --refresh-layout
python3 photos/install.py --home /home/aven --refresh
```

Without `--refresh-layout`, Files retains the user's existing dock layout.
Both installers retain the original configuration backup and unrelated keys.
No package layering, KWin configuration or Atomic deployment is changed here.

## Shared dependencies and native limits

Root supplies the neutral white content, pale gray sidebars, compact UI font,
window corners and shadows through the shared visual profile. Native Gwenview
paints its URL container with `QPalette::Mid` and paints thumbnail shadows in its
delegate; ordinary public KConfig keys do not remove those treatments. A native
folders tree also differs from Photos' semantic library navigation.

Verified upstream contracts:

- [Gwenview 26.08.1 preferences](https://github.com/KDE/gwenview/blob/v26.08.1/lib/gwenviewconfig.kcfg)
- [Shared sidebar and splitter state](https://github.com/KDE/gwenview/blob/v26.08.1/app/mainwindow.cpp)
- [Native thumbnail drawing](https://github.com/KDE/gwenview/blob/v26.08.1/lib/thumbnailview/previewitemdelegate.cpp)
- [KToolBar settings](https://github.com/KDE/kxmlgui/blob/v6.18.0/src/ktoolbar.cpp)
- [KMainWindow toolbar groups](https://github.com/KDE/kxmlgui/blob/v6.18.0/src/kmainwindow.cpp)

## Verification

26 Files unit tests, 10 preview boundary tests and 5 asynchronous handoff tests
passed. Actual offscreen Qt restored the 184 pixel Places pane at 760, 1100 and
1440 pixel window widths. Preview's existing Qt smoke passed Chinese prose,
Unicode images, PDF, stopped-audio duration, paused-video poster without autoplay,
explicit playback and Escape close. Fresh and refreshed temporary-home installs
passed Photos' semantic audit and retained unrelated keys and backup files.

Offscreen runs are engineering checks, not desktop visual evidence. Root must
capture and inspect the deployed Files, Photos grid, image view and Chinese
Preview. Revised visual scores and three-second judgment remain pending.
