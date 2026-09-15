# Stock typography matrix

The typography agent booted only the independent stock guest and captured native SC/TC Dolphin UI and real SC/TC browser paragraphs. Root owns the Aven guest. No Aven fontconfig, theme, font role, browser preference, or KWin effect was applied to stock.

All imagery comes from `scripts/capture.py`, with lossless QEMU framebuffer PNGs and capture-time guest sidecars. `typography/stock-matrix.json` records the 16 exact inspected image hashes and exclusions. All canonical captures pass the runtime scale check. These are baseline observations, not quality scores or a stock/Aven comparison.

Canonical scene names in `evidence/stock/round-00/`:

| Content | 1× and 2× | 1.25× and 1.5× |
|---|---|---|
| SC native Dolphin | `typography-ui-sc-matrix` | `typography-ui-sc-final` |
| TC native Dolphin | `typography-ui-tc-matrix` | `typography-ui-tc-final` |
| SC prose | `typography-prose-sc-matched` | `typography-prose-sc-final` |
| TC prose | `typography-prose-tc-matched` | `typography-prose-tc-final` |

Append `-1x.png`, `-1.25x.png`, `-1.5x.png`, or `-2x.png`; each image has its original `.json` sidecar.

## Matched display and geometry

| Compositor scale | Physical framebuffer | Logical output | Stock mode ID |
|---:|---:|---:|---:|
| 1 | 1280×720 | 1280×720 | 27 |
| 1.25 | 1600×900 | 1280×720 | 28 |
| 1.5 | 1920×1080 | 1280×720 | 13 |
| 2 | 2560×1440 | 1280×720 | 29 |

IDs are specific to the current stock output; use the actual `kscreen-doctor -o` inventory in Aven. Three test modes were added through the stock display API:

```sh
bash ~/aven/scripts/guest-session.sh kscreen-doctor \
  output.1.addCustomMode.1280.720.60000.reduced \
  output.1.addCustomMode.1600.900.60000.reduced \
  output.1.addCustomMode.2560.1440.60000.reduced
```

The generated modes report 59.74, 59.83, and 59.95 Hz respectively. At 150%, the existing 1920×1080@60 mode is used. Switch mode and scale in one command, for example:

```sh
bash ~/aven/scripts/guest-session.sh kscreen-doctor output.1.mode.28 output.1.scale.1.25
```

Both applications use **outer frame x=40, y=28, width=1200, height=630 logical pixels**, with one tab/window. Arrange through the transient verification helper:

```sh
bash ~/aven/scripts/guest-session.sh python3 ~/aven/verification/window_tool.py arrange \
  --app dolphin --geometry 40 28 1200 630 --activate
```

Use `--app firefox` for the browser. At 125%, Dolphin acknowledges height 630.4 and Firefox may acknowledge 629.6 or 630.4, because physical pixels cannot represent the requested half-pixel height. Other dimensions and all other scales acknowledge exactly. This rounding is recorded as a measurement, not corrected by resampling images.

## Native UI

Close any existing Dolphin process before changing language. Launch the same directory in each language:

```sh
env LC_ALL=zh_CN.UTF-8 LANG=zh_CN.UTF-8 LANGUAGE=zh_CN \
  bash ~/aven/scripts/guest-session.sh dolphin "$HOME/Documents/日常 · Everyday"
```

For Traditional Chinese, substitute `zh_TW.UTF-8` and `zh_TW`. The SC and TC process environments were inspected under `/proc`; all three variables match the intended locale. Native menus, sidebar and column labels visibly change language.

Use native `Ctrl+3` for detail view, ascending name sort, at the top of the same mixed fixture folder. Keep a single tab (close restored extra tabs through the native UI if needed). The stock view retains its inherited thumbnail zoom and narrow sidebar. The original SC integer captures have a thin first-row focus outline. After restarting for fractional recaptures, SC has no visible selected row; TC also has no visible selected row. Do not interpret that difference as an Aven selection design. Native locale collation changes where Chinese-only filenames appear after the six numbered images; match SC against SC and TC against TC.

The baseline application probe reports Noto Sans 9.75 pt, weight 400. Its mixed-text shaping sample uses Noto Sans CJK SC in the SC locale and Noto Sans CJK TC in TC, with no missing glyphs. This separate client supports fallback provenance; the actual Dolphin screenshots remain the evidence for appearance.

## Browser prose

Use the normal stock native Firefox profile. Close Firefox completely before changing its process locale, including the native quit confirmation if shown. The active SC and TC processes were separately launched with the matching three locale variables. No browser typography preferences were added.

Open one tab at page zoom 100%:

```text
file:///home/aven/aven/fixtures/typography/specimen.html#sc
file:///home/aven/aven/fixtures/typography/specimen.html#tc
```

`#sc` and `#tc` were added only as section IDs to the shared specimen. The fixture's text and visual CSS did not change. Synchronize the same file to Aven before capture. The SC view shows all three Simplified Chinese paragraphs and the beginning of the TC section. The TC view shows all three Traditional Chinese paragraphs and the full HK paragraph. The generic CSS family lets the actual browser and OS fallback stack choose the fonts.

To navigate an existing tab, activate Firefox, use native `Ctrl+L`, paste the file URL with `scripts/input.py`, and press Return. On this guest, `Ctrl+1` did **not** select tab 1; two provisional close-tab operations therefore removed the wrong tabs. The resulting provisional screenshot is explicitly excluded. No screenshot was edited to disguise that navigation error.

## Observed baseline limits

All four native UI scales show real SC/TC labels and Latin filenames without visible missing-glyph boxes. The sidebar truncates several location labels, and the bold current breadcrumb has strong visual weight. At 100%, UI text is small compared with the reading specimen; the prose's 17 px text remains fully readable in the inspected image. At higher scales, the Chinese paragraphs preserve their line breaks and spacing in the matched logical viewport. The TC prose includes mixed Latin filenames/numbers and corner quotes; no missing punctuation was visible.

These observations do not establish premium quality. The independent [round 02 matrix review](matrix-review.md) subsequently inspected every exact stock/Aven pair. Root fixed the initial Aven manual QFont serialization error (legacy strings clamping weight to 900) before those Aven matrix captures. The captured application probe resolves regular UI at 400; the later [native weight investigation](typography-bold-investigation.md) also distinguishes native bold 700 from the explicit 900 control.

### Fractional probe correction

The first capture-time Qt probe created no window and read `QScreen.devicePixelRatio()`. It reports 2 at compositor scales 1.25 and 1.5. The captured KScreen output and KWin window inventory correctly report 1.25/1.5, and the physical framebuffers are 1600×900/1920×1080 with a 1280×720 logical workspace.

Qt explicitly documents that screen and window DPR may differ under fractional Wayland scaling and recommends the window's DPR when a window is known. Verification added a mapped native surface DPR observation and structured compositor output. All eight canonical fractional captures were then taken afresh: their actual QWindow DPR agrees with compositor 1.25/1.5 while QScreen remains honestly 2. The original fractional PNGs are real imagery, but their old QScreen-only sidecars remain excluded. No recorded value was rewritten. [Qt QScreen documentation](https://doc.qt.io/qt-6/qscreen.html#devicePixelRatio-prop).

The probe maps an alpha-zero 4×4 Qt surface **after** taking the screenshot. Wayland may temporarily activate it despite the no-focus hint. Each canonical fractional sidecar confirms a real submitted buffer and that the original KWin active window UUID returned when the probe closed, with no activation requests. The original integer captures pass with their original QScreen/KScreen agreement and an explicit legacy measurement warning. See [verification](verification.md) for the probe and gate.

### Display wake and rejected frames

Stock's normal idle DPMS timeout occurred while the fractional probe was being corrected. Four `*-tc-verified-1.25x/1.5x` captures have passing scale metadata but visibly contain only “Display output is not active.” They were inspected, rejected, retained as excluded artifacts, and replaced by visible `*-tc-final` captures. Runtime provenance cannot replace looking at the pixels.

After an idle interval, send a native Shift key using `scripts/input.py` to wake the display, then take and inspect a temporary screenshot before starting a capture sequence. Do not disable stock power management or reuse an old frame. Inspect each retained screenshot after capture.

Stock was restored to its original 1920×1200@75 mode at scale 1 after the matrix, confirmed with `kscreen-doctor -o`. The test custom modes remain available for repeat capture; stock styling and font configuration remain untouched.
