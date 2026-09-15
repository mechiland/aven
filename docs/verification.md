# Verification and critic protocol

Verification owns `verification/`, this document, and `evidence/verification/`.
The integrator owns shared Plasma/KWin changes and `docs/STATUS.json`. None of
the tools below assigns visual quality from source code, fonts, or file hashes.

## Runtime evidence

In the logged-in guest, run:

```sh
~/aven/scripts/guest-session.sh python3 ~/aven/verification/guest_probe.py --guest stock
```

Use `aven` for the candidate. Save stdout as JSON on the host. The probe reads
OSTree deployments, versions, font matches, actual Qt mixed-text shaping faces,
Qt screen and mapped-window scale, locale, KWin loaded/active effects and compositor support,
default MIME handlers and configuration hashes. It makes no configuration
changes. A temporary Qt client must connect to Wayland rather than `offscreen`.
Missing PySide6 or a session connection is a failed probe, not
evidence that the target application renders correctly.

On Wayland, a bare QScreen reports integer scale even when the compositor uses
125% or 150%. The [Qt QScreen documentation](https://doc.qt.io/qt-6/qscreen.html#devicePixelRatio-prop)
therefore recommends QWindow's device-pixel ratio for a specific surface. At
integer scales, the probe creates no window: QScreen must agree with structured
KScreen output, and the result explicitly records `surface_mapped:false`.
A disagreement fails without mapping a fallback window. This preserves native
menus and popovers during the ordinary 1× capture workflow.

At fractional scales only, the probe submits an alpha-zero 4×4 native window buffer after screenshot capture,
samples its actual fractional DPR after 700 ms, and closes the client. The window
is input-transparent; KWin can briefly focus it despite Qt's no-focus hint. The
probe records that state honestly and verifies the original active-window UUID
returns afterward, using read-only KWin inventory. It sends no activation request.
A failed focus check invalidates the probe; it does not manipulate the application
to conceal the failure. This measurement surface is not part of captured pixels.
Restored active-window UUID does not imply restored popup state: the temporary
focus change can dismiss native menus and popovers. The probe records that limit
and `popup_state_restored:null`. Reopen the popup through the application before
further interaction; do not treat a vanished popup as an application failure.

Structured `kscreen-doctor -j` output must agree with the mapped window's DPR.
The separate QScreen DPR remains recorded as observed, including its integer
rounding. A submitted surface can subsequently report `exposed:false` when the
compositor occludes its fully transparent pixels; `exposed_once`, `visible`, and
the submitted-buffer count establish that the native surface was actually mapped.
The gate checks those fields and focus restoration. Original integer-scale
captures without a mapped window remain usable only when their captured KScreen
output agrees, with an explicit legacy warning. Old fractional QScreen-only
captures require recapture; their metadata is never rewritten to imply a new
measurement.

Each capture sidecar may embed this JSON in `runtime_probe`. Alternatively, the
critic pair can name `stock_probe` and `aven_probe` JSON paths. Each probe must
be within 120 seconds of its capture. Make each display scale change before
probing. Capture actual Chinese Qt UI in both SC and TC, plus real paragraphs,
at 100%, 125%, 150%, and 200%. A browser's `lang` attribute does not prove Qt's
Han fallback. Record mixed punctuation, baseline balance and Latin/CJK weight.

The gate checks matching framebuffer sizes, actual Qt surface scale, base OSTree
commit, native app/runtime versions, and available font packages. Root must also
check matching fixture content and window states; a shared
`content_id` identifies the same document/view. Package additions and display
geometry belong in the baseline record. Hashes establish integrity, not image
authenticity; an honest inspection of real framebuffer captures remains required.

## GPU framebuffer capture

QEMU 10.2.1's `qemu_console_surface()` returns null for GL texture/DMABUF scanout,
which explains the observed QMP `no surface` response after Wayland starts.
The EGL headless backend still copies GPU output into its display surface, which
QEMU's VNC server reads. These are distinct code paths. Sources:
[console.c](https://github.com/qemu/qemu/blob/v10.2.1/ui/console.c#L1488),
[egl-headless.c](https://github.com/qemu/qemu/blob/v10.2.1/ui/egl-headless.c#L142),
[vnc.c](https://github.com/qemu/qemu/blob/v10.2.1/ui/vnc.c#L825).

The read-only RFB helper requests raw true-color pixels from QEMU's loopback VNC.
It changes only byte channel packing for lossless PNG encoding. It does not crop,
resize, adjust colors, composite content, or inject mouse/keyboard/clipboard input.
The server's actual pixels remain authoritative. A real 1920×1200 installer
console capture was inspected in `evidence/verification/installer-rfb-probe.png`;
that proves capture transport, not the desktop's visual quality or GL operation.

```sh
python3 verification/rfb_capture.py --port 5920 \
  --output evidence/verification/transport-check.png
```

The helper writes PNG plus `.rfb.json` transport metadata. The integrator's full
capture sidecar embeds that metadata as `framebuffer_transport`, uses the RFB
`method` string, and pairs it with guest runtime data as usual. The critic gate
accepts both genuine QMP and RFB captures.

For motion, start a short capture while operating the real guest in another
terminal. The command itself sends no input:

```sh
python3 verification/record_frames.py --guest stock \
  --output-dir evidence/verification/stock-preview-motion-01 --seconds 8 --fps 10
```

It saves untouched PNGs, per-frame hashes/timestamps, actual sampling rate,
largest gap, and `replay.ffconcat` for playback at observed host intervals.
Sampling can miss compositor frames, so inspect the replay for observed behavior
and acknowledge its limits. Frame sequences or contact sheets cannot establish
physical frame pacing. A clip may be encoded for convenient playback, while
the original PNGs and `recording.json` remain the primary evidence.

## Temporary window inventory and matched arrangement

Inside the guest, use the existing session wrapper:

```sh
bash ~/aven/scripts/guest-session.sh python3 ~/aven/verification/window_tool.py inventory
bash ~/aven/scripts/guest-session.sh python3 ~/aven/verification/window_tool.py inventory --app dolphin
```

Inventory returns actual KWin IDs, captions, desktop/resource names, frame and
client geometry, output scale and active/minimized state. It does not change
geometry or focus. `--include-special` also reports panels and desktop windows.
The native stock 44 inventory was exercised successfully; DBus inspection after
the call confirmed no temporary Script object remained. The recorded result is
`evidence/verification/stock-native-window-inventory.json`.

When root is ready to arrange a scene, explicitly choose one existing window:

```sh
bash ~/aven/scripts/guest-session.sh python3 ~/aven/verification/window_tool.py arrange \
  --app dolphin --geometry 180 120 1200 850 --activate
```

`--app` exactly matches desktop file name, resource class or resource name.
`--caption` adds a literal title substring; `--id` selects the reported UUID.
Zero or multiple matching windows fail before changing anything. `--geometry`
specifies the entire outer frame in logical pixels, including the titlebar;
values must fit the current output work area and the application's minimum size.
`--maximize` is an alternative to explicit geometry. `--activate` unminimizes and
focuses the selected window, and can be used alone. No other window is hidden or
closed. Capture the resulting actual geometry; Wayland size changes can be
asynchronous, so the tool waits 600 ms by default and reports acknowledgment.
Native arrangement has been exercised on real Dolphin, Firefox and Thunderbird windows. Round-04 composer captures record requested and acknowledged outer geometry, including 720×840 and 1000×840 frames, through temporary public KWin scripts. No persistent window rules were installed.

The helper loads only its own one-shot script, receives JSON through a private
temporary DBus callback, and unloads it immediately. It never invokes global
`Scripting.start`, installs shortcuts, or writes KWin rules/settings. This avoids
changing baseline configuration merely to place a comparison window. It uses
Fedora's `qdbus-qt6` and stock Python GObject bindings. Window operations follow
the [public KWin scripting API](https://develop.kde.org/docs/plasma/kwin/api/).

## Files operations through Dolphin

Use the same sequence in stock and Aven. In the guest, prepare one fresh fixture:

```sh
python3 ~/aven/verification/file_operations.py prepare \
  --root "$HOME/Documents/Aven operation check 01" \
  --source "$HOME/Documents/日常 · Everyday/旅行清单.txt"
```

Open that folder in Dolphin. The helper only seeds files and verifies bytes;
it does not perform the operations being tested.

1. Open `01 原件`, select `周末 清单 100% #1.txt`, copy using Dolphin, then
   paste into `02 复制`. Check stage `copied`.
2. Cut the copy in Dolphin, then paste into `03 移动`. Check stage `moved`.
3. Rename the moved file to `已整理 · Weekend.txt` using Dolphin. Check `renamed`.
4. Move it to Trash using Dolphin. Check `trashed`. Inspect the real Trash
   location so disappearance alone cannot masquerade as successful trashing.
5. Restore it from Dolphin's Trash view. Check `restored`. Verify the original
   in `01 原件` still exists with the same contents.

After each step, save the helper's output outside the operation fixture:

```sh
python3 ~/aven/verification/file_operations.py verify \
  --root "$HOME/Documents/Aven operation check 01" --stage copied
```

Capture or explicitly witness each native operation, including feedback and
focus. A passing helper output has `ui_verified: false`: it says only that the
filesystem result is correct. Screenshots/observations establish the UI route.

Also exercise folder open, breadcrumbs, sidebar, Downloads/Documents/Pictures,
grid/list view, multi-selection, default opening, preview invocation, preview
next/previous, Escape returning focus to the selected Dolphin file, and opening
the preview in its full application. Test a long Chinese filename, a missing
file, unsupported file, and media playback. Count actions from selected file to
preview and back; record whether repeated preview accumulates windows.

## Browser, mail, photos and motion

- Firefox: an ordinary real website, SC and TC reading, download and reveal in
  Dolphin, upload/file chooser, mail-link to Firefox. Confirm the chosen profile
  receives links rather than silently opening another browser profile.
- Thunderbird: fixture message list, SC/TC reading, compose and save draft,
  reopen the saved draft. The mailbox is fictional and offline; do not send.
- Gwenview: thumbnail grid, fitted landscape, portrait with EXIF rotation,
  transparency, next/previous, fullscreen entry/exit, and return to Files.
- Motion: directly observe or record open/close, Alt+Tab, menus/popovers, preview,
  image transition and overview. Static screenshots cannot establish smoothness.
  Describe any VM limitation separately from an implementation defect.
- Atomic: record the pinned stock deployment and candidate deployment; confirm
  normal status and boot selection. Exercise rollback on a disposable copy when
  practical. Do not treat configuration changes in `/etc` or `$HOME` as rolled
  back automatically by OSTree; record the configuration backup/restore route.

## Critic manifest and pass gate

Start a round record without scores:

```sh
python3 verification/evidence_gate.py --template > evidence/verification/round-01.json
```

After direct visual inspection, add `pairs`. One pair may carry multiple tags;
do not duplicate the same screenshot into several pairs. Paths are relative to
the repository, pointing to existing `scripts/capture.py` sidecars:

```json
{
  "id": "files-home-100",
  "content_id": "home-fixture-v1",
  "tags": ["files_home", "files_list"],
  "stock": "evidence/stock/round-00/files-home-1x.json",
  "aven": "evidence/aven/round-01/files-home-1x.json",
  "inspection": {
    "by": "critic-agent-name",
    "stock_sha256": "exact-inspected-PNG-hash",
    "aven_sha256": "exact-inspected-PNG-hash",
    "notes": "Concrete visible comparison, including defects and limits."
  }
}
```

Each score record supplies a number, pair IDs, rationale and limitations. Required
tags per category are defined in `CATEGORIES` in `verification/evidence_gate.py`.
Chinese requires `typography_sc`, `typography_tc`, `qt_sc`, and `qt_tc` at all four
actual scales. Each operation includes `id`, `passed`, `method: "native-ui"`,
`observation`, and pair IDs. Copy/move/rename/trash/restore also name `stock_check`
and `aven_check` helper output paths. Each motion entry includes `id`, `passed`,
`method: "live-observation"` or `"recording"`, `observer`, `observation`, and pair
IDs. A recording additionally cites each guest's file and SHA-256.

Run the read-only gate:

```sh
python3 verification/evidence_gate.py evidence/verification/round-01.json
python3 -m unittest discover -s verification/tests -v
```

Passing requires complete evidence, all nine assigned scores, their arithmetic
mean ≥8, Chinese ≥8.5, and the critic's affirmative three-second judgment citing
paired desktops. Missing/failed observations cannot pass. `docs/STATUS.json`
keeps unverified scores null and is updated only by the root integrator.

## Source review findings

- **Fixed by root:** an Aven qcow2 overlay originally used the writable stock
  disk as backing. Booting stock later could invalidate its backing data. The
  harness now creates an independent disk with `qemu-img convert`.
- **Fixed by root:** source synchronization originally omitted `verification/`.
- Source review and isolated tests are engineering evidence only. No desktop
  polish scores exist until real paired screenshots are inspected.

## Completed native operation evidence

The stock source report is
[`stock-native-verification.json`](../evidence/interaction/stock-native-verification.json).
It covers all 17 required operations and six recorded motion scenarios. Stock's
Space quick-preview failure and Escape behavior in Dolphin's information panel
remain recorded baseline findings.

The round-04 Aven source report is
[`aven-round04-native-verification.json`](../evidence/interaction/aven-round04-native-verification.json).
All 17 required native operations passed, including copy/move/rename/trash/restore,
selected-file preview and focus return, browser download/reveal and native file
chooser, draft save/reopen, and image navigation. Every tested file mutation used
Dolphin's UI on a fresh disposable fixture. Read-only checks separately confirm
file bytes and the downloaded file hash. Mail remained offline and no message was
sent; the file chooser selected a local name without uploading it.

The [integrity report](../evidence/verification/aven-round04-native-evidence-validation.json)
validates 35 accepted screenshots and all 359 motion frames. Original screenshots
and representative motion frames were inspected; nine startup or operator-miss
captures are explicitly excluded. The six Aven recordings sample approximately
8.4–9.75 frames per second. They demonstrate the recorded behavior, while physical
display frame pacing and the paired visual-quality verdict remain separate.

The unchanged mail fixture was captured before the draft test at 1000×840 and
720×840 outer window sizes. The narrower frame exposes wrapping of the existing
Chinese paragraph. The subsequent save/reopen check preserves the newly added
Chinese sentence in the offline draft and uses separate operation screenshots.
