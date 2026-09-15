# Files and preview — first prototype

## Decision

Dolphin remains the file manager. Folder navigation, breadcrumbs, list/grid views,
selection, copy/move/rename/trash/undo, thumbnailing and opening applications stay
in KDE's maintained infrastructure. Aven adds a small disposable preview window
using Qt's maintained image, PDF, text and multimedia renderers.

The files layer does not write Plasma, KWin, palette, decoration or global font
configuration. It inherits the integrator's font and palette. It owns only
Dolphin defaults, one service menu and its small preview renderer container.

## Why this route

| Candidate | Finding | Decision |
|---|---|---|
| Dolphin Information panel | Built in, minimal overhead; useful metadata and thumbnail, but narrow for reading a PDF/paragraph. | Keep F11 as a fallback. |
| KLook | Current repository still requires KDE4 and Qt4. | Unsuitable for the current Atomic KDE base. |
| Kiview | Maintained Qt6 preview application; its global Dolphin bridge copies file locations through Klipper and may alter the selection. Raw `file://` construction also needs unusual filename testing. | Do not take on its clipboard bridge or a fork. |
| Small Qt container through KIO | Uses Dolphin's selected URLs and upstream renderers. No clipboard use, folder enumeration, custom file operations or daemon. | Prototype implementation. |

Dolphin 26.04 introduced `ServiceMenuShortcutManager`, built when KIO is at least
6.24. This registers each KIO action with an action ID of
`servicemenu_<desktop filename>::<desktop action key>`. It lets the preview use a
real Dolphin-local shortcut without a fork or a synthetic global key handler.
The pinned comparison deployment runs Dolphin 26.08.1 and KIO 6.30.0; its native
service-menu shortcut has been exercised in the booted Aven guest.

Primary sources checked 2026-09-15:

- [Dolphin service menus](https://develop.kde.org/docs/apps/dolphin/service-menus/)
- [Dolphin 26.04 shortcut manager](https://github.com/KDE/dolphin/blob/v26.04.3/src/servicemenushortcutmanager.cpp)
- [Dolphin 26.04 main window / KIO version condition](https://github.com/KDE/dolphin/blob/v26.04.3/src/dolphinmainwindow.cpp)
- [Fedora 44 Dolphin package](https://packages.fedoraproject.org/pkgs/dolphin/dolphin/fedora-44-updates.html)
- [Dolphin Information panel](https://docs.kde.org/stable_kf6/en/dolphin/dolphin/panels.html)
- [KLook build requirements](https://github.com/KDE/klook/blob/master/CMakeLists.txt)
- [Kiview bridge source](https://github.com/Nyre221/Kiview/blob/main/src/dolphinbridge.cpp)
- [Qt PDF view API](https://doc.qt.io/qtforpython-6/PySide6/QtPdfWidgets/QPdfView.html)
- [Fedora PySide6 package and modules](https://packages.fedoraproject.org/pkgs/python-pyside6/python3-pyside6/fedora-44-updates.html)
- [Fedora graphics thumbnail plugins](https://packages.fedoraproject.org/pkgs/kdegraphics-thumbnailers/kdegraphics-thumbnailers/fedora-44-updates.html)

## Interaction

- Select a local file in Dolphin and press **Ctrl+Alt+P**, or use **Preview** in
  the context menu. The selection is passed as typed URL arguments through KIO.
- **Esc** or **Ctrl+Alt+P** closes the preview. **Space** also closes images,
  PDFs and text; in audio/video it plays or pauses.
- **Enter** or **Open** sends the file to the configured application.
- When several files are selected, **Alt+Left/Right** visits only that selection.
  Closing returns to the unchanged Dolphin folder and selection.
- Space in Dolphin retains KDE's selection mode. Ctrl+Space is left available
  for Chinese input methods. No global keyboard shortcuts are installed.
- Images fit the window, respect EXIF orientation, and convert tagged color to
  sRGB. PDF uses Qt's multi-page view. Read-only text follows the owned prose
  roles: 16 logical px/1.65 for Latin and 17 logical px/1.75 for Chinese or mixed
  Chinese/Latin. The line height is based on the em size, with room for taller
  fallback glyphs, rather than multiplying Qt's already padded font line box.
  Media starts paused, with a single playback/seek row. KWin owns window motion.

There is no application menu, folder browser, file modification command, account,
search index or background service in this extension.

## Dolphin defaults

The initial style uses 22 px Places and detail icons, 48 px folder icons and
96 px grid previews. Grid captions use at most two lines. Details keep name,
size and modified date. Pictures gets a preview grid; Documents and Downloads
get details. Panels lock, hover tooltips stay quiet, and the information panel
follows selection rather than accidental hover. Existing menu commands remain
available. No toolbar replacement or custom file-manager branding is included.

### Sidebar correction from the first booted stock capture

Inspected `.cache/vm/stock-files-preupdate.png`: its approximately 90 px Places
panel truncates the Chinese Home label, recent entries and device names. This is
an observed stock defect, not a score for Aven.

There is no supported scalar `PlacesPanel/Width` setting. Dolphin gives its
native dock the object name `placesDock`, and KMainWindow stores Qt's base64
`saveState()` output under `[State] State`. The booted Fedora profile confirmed
the current location as `~/.local/state/dolphinstaterc`.

`files/layout.py` now generates the initial layout through Qt's public
`QMainWindow::resizeDocks()` and `saveState()` APIs, targeting a **224 logical px**
Places panel. Other panels begin hidden, and the existing native toolbar is
retained. It uses an offscreen native Qt layout to serialize the named panels;
it neither edits binary offsets nor adds a window hook. This layout is seeded
once, with the previous state backed up. Subsequent user resizing persists.
`QT_QPA_PLATFORM=offscreen python3 files/layout.py --reset` reapplies the candidate
width during prototype iteration, with Dolphin closed.

`files/places.py` marks only the default system Desktop, Music, Videos and Recent
Locations entries hidden through KDE's existing `IsHidden` XBEL metadata. The
bookmarks still exist and **Show Hidden Places** can reveal them. Home, Documents,
Downloads, Pictures, Trash, Recent Files, Network and device discovery remain.
Custom bookmarks are not hidden by matching their labels. This shared native
Places list also affects KDE file dialogs; it is ordinary user bookmark data,
not a Plasma change. If no native list exists yet, the step reports that it is
pending instead of inventing its initialization metadata.

Source evidence:

- [Dolphin dock object names](https://github.com/KDE/dolphin/blob/v26.08.0/src/dolphinmainwindow.cpp)
- [KMainWindow native state read/write](https://github.com/KDE/kxmlgui/blob/master/src/kmainwindow.cpp)
- [Qt main-window state and dock resizing APIs](https://doc.qt.io/qt-6/qmainwindow.html)
- [KFilePlacesItem hidden metadata](https://github.com/KDE/kio/blob/master/src/filewidgets/kfileplacesitem.cpp)
- [KFilePlacesModel default bookmarks](https://github.com/KDE/kio/blob/master/src/filewidgets/kfileplacesmodel.cpp)

Native Fedora verification still needs: launch at the normal size, confirm
Chinese Home and Recent Files are readable, reveal hidden Places, inspect device
labels, drag the sidebar to a different width, close/reopen and verify that width
persists. Repeat at 125/150/200% scaling. Long volume labels may still elide;
ordinary Chinese navigation labels should not.

## Installation on the Aven clone

The stock baseline must be captured before installing this layer.

1. Add the Fedora packages listed in `files/integration.json` through the
   integrator's Atomic image/layering process, then boot that deployment.
2. With Dolphin closed, run as the prototype user:

   ```sh
   python3 files/install.py
   ```

   A staged home can be prepared with `--home /home/aven`. The installer detects
   the local Dolphin version. For an image staging environment without Dolphin,
   `--xmlgui-version 48` targets Dolphin 26.04 and `49` targets 26.08. These are
   upstream XMLGUI versions, not a guessed schema number. Verify versions when
   the distribution changes. `--skip-layout` allows staging on a machine without
   Qt; run the native layout step later on the Fedora image before taking Aven
   captures.
3. Start Dolphin and verify the action is present in **Configure Keyboard
   Shortcuts → Context Menu Actions**. The action is
   `servicemenu_aven-preview.desktop::aven-preview`.
4. Validate images, a multi-page Chinese PDF, Chinese text and real media through
   the actual shortcut in the booted VM. Direct renderer launches alone do not
   validate this integration.

### Native toolbar regression and repair

The first booted Aven capture, `evidence/aven/round-01/files-home-1x.png`, shows
the generic New Window/Undo/Cut/Copy toolbar instead of Dolphin's Back/Forward,
view controls and hamburger. Read-only guest inspection found Dolphin 26.08.1,
KF6 KXmlGui 6.30.0, and an ActionProperties-only local `dolphinui.rc` carrying
version 49. That was an integration defect in the first installer.

KXmlGui selects the highest-version UI document. When a minimal local fragment
shares the embedded UI's version, the local document wins and the rest of the
native UI is absent. The corrected installer writes **version 0** for an
ActionProperties-only seed. KDE then upgrades it from the current embedded
Dolphin UI, carrying the Preview shortcut into that full document. Complete
existing user UI files retain their version, menus, toolbar layout and other
shortcuts. No upstream toolbar copy is maintained by Aven.

With Dolphin closed, repair just this setting using:

```sh
python3 files/install.py --shortcut-only
```

On restart, verify `~/.local/share/kxmlgui5/dolphin/dolphinui.rc` has been expanded
by KDE to include the current native `<MenuBar>` and `<ToolBar name="mainToolBar">`.
The actual toolbar must show Back/Forward, view controls, breadcrumbs, split,
search and hamburger. Select a file, press Ctrl+Alt+P, close with Esc, then reopen
Dolphin and check both toolbar and shortcut again. The staging tests verify
repair of the bad fragment and preservation of complete UI files; the native
restart and screenshot are the required runtime verification.

Sources: [KXmlGui 6.30 version selection and ActionProperties migration](https://github.com/KDE/kxmlgui/blob/v6.30.0/src/kxmlguiversionhandler.cpp),
[Dolphin 26.08.1 native UI](https://github.com/KDE/dolphin/blob/v26.08.1/src/dolphinui.rc).

The installer writes `~/.local/libexec/aven-preview`, a `~/.local/bin` symlink,
two desktop entries, Dolphin config and folder view settings. It backs up
pre-existing config files once as `*.pre-aven`. It creates absolute Desktop Exec
paths, so it also works before a new login adds `~/.local/bin` to PATH.
It also seeds native dock state once and hides four optional system Places
entries in the existing XBEL list. No mounted device is hidden.

## Implemented safeguards and limits

Local paths retain spaces, percent signs, hash marks, newlines and Chinese names.
URL percent decoding happens once. Arguments never enter a shell. Remote URLs,
directories and device/FIFO streams are rejected. The preview does not access
the clipboard. Unicode text (UTF-8 and BOM-marked UTF-16/32) is exact; unknown
legacy encodings show a concise fallback rather than guessed Chinese text.
Text reads stop at 1 MiB and partial final codepoints are omitted cleanly.

Qt limits image allocation to 256 MiB; large images are requested at no more
than 4096 px per side for preview. This is a viewing aid, not a lossless editor.
Office documents, archives, remote KIO locations and password-protected PDFs
stay with the full applications. H.264/HEVC playback depends on codecs available
in the Fedora image and must be reported from the VM, not assumed from host Qt.

## Verification status

**Code and renderer checks pass; Fedora desktop interaction and visual quality
remain unverified. No Files or typography score is claimed by this layer.**

Executed on 2026-09-15:

```sh
PYTHONPATH=preview python3 -m unittest discover -s preview/tests -p 'test_*.py' -v
QT_QPA_PLATFORM=offscreen PYTHONPATH=preview python3 preview/tests/smoke_qt.py
python3 files/install.py --home /tmp/aven-preview-install-smoke --xmlgui-version 49 --skip-layout
QT_QPA_PLATFORM=offscreen python3 files/tests/smoke_layout.py
```

Nine boundary tests passed: unusual filenames, one-time URL decoding, nonregular
file rejection, symlinks, selection order/limit, exact Chinese encodings,
bounded text, unknown/binary text fallback and a file changed into a FIFO.
The real Qt 6.11.2 smoke check decoded a Chinese filename PNG, Chinese paragraphs,
a PDF page and a WAV, navigated the selection and closed through Escape. An
offscreen text screenshot was inspected for renderer defects; it is not an Aven
OS screenshot and cannot support a visual score.

Follow-up checks exercise the actual Qt layout deserializer at 760, 1100 and
1440 px window widths, confirm 224 px Places, preserve the toolbar, and check
one-time seeding plus untouched custom bookmarks/device metadata. The renderer
smoke also checks the measured Chinese paragraph baseline interval against
17 × 1.75 = 29.75 logical px. These are integration checks, not visual approval.

The integrator/critic must still inspect:

- actual Ctrl+Alt+P dispatch on the Fedora Wayland session, focus return and
  repeated launch/close latency;
- breadcrumbs, Places, list/grid, real thumbnails and folder settings;
- copy/move/rename/trash/undo with Unicode and mixed file types;
- images, Chinese PDF/text, WebM/MP4/audio, unsupported and missing-file behavior;
- 100%, 125%, 150%, 200% scaling and mixed Chinese/Latin paragraph comfort;
- paired stock/Aven desktop captures before giving any score or pass.
