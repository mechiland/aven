# Typography: round 02 paired observations

Sixteen Aven screenshots were captured and inspected against the stock SC/TC matrix at 100%, 125%, 150%, and 200%. The typography agent owns these observations; **no critic scores or pass judgment are assigned here**.

This is a historical **round 02** report. The [independent matrix supplement](matrix-review.md) subsequently inspected all 32 original images and retained Chinese typography at a provisional 8.2. Round 04 will use a separate manifest and report under the [current capture plan](typography-round04-plan.md); later chrome and mail changes are not attributed to these earlier images.

The most visible typography improvement is the larger native UI text and the space for complete sidebar labels. The controlled browser paragraphs look similar to stock. These images support improved native UI readability, but do not establish a dramatic improvement in Chinese paragraph rasterization.

## Evidence

All Aven captures are in `evidence/aven/round-02/` with scenes `typography-ui-sc-matrix`, `typography-ui-tc-matrix`, `typography-prose-sc-matrix`, and `typography-prose-tc-matrix`, each at `1x`, `1.25x`, `1.5x`, and `2x`.

[Aven matrix](../typography/aven-matrix.json) records every inspected image hash, its exact stock pair, actual scale validation, Qt font/shaping information, and measured window geometry. [Stock matrix](../typography/stock-matrix.json) retains the baseline hashes and explicit exclusions. The original PNGs and sidecars are unchanged.

Representative directly inspected pairs:

| Scene | Stock | Aven |
|---|---|---|
| SC native UI, 100% | [Stock PNG](../evidence/stock/round-00/typography-ui-sc-matrix-1x.png) | [Aven PNG](../evidence/aven/round-02/typography-ui-sc-matrix-1x.png) |
| TC native UI, 100% | [Stock PNG](../evidence/stock/round-00/typography-ui-tc-matrix-1x.png) | [Aven PNG](../evidence/aven/round-02/typography-ui-tc-matrix-1x.png) |
| SC prose, 100% | [Stock PNG](../evidence/stock/round-00/typography-prose-sc-matched-1x.png) | [Aven PNG](../evidence/aven/round-02/typography-prose-sc-matrix-1x.png) |
| TC prose, 100% | [Stock PNG](../evidence/stock/round-00/typography-prose-tc-matched-1x.png) | [Aven PNG](../evidence/aven/round-02/typography-prose-tc-matrix-1x.png) |
| SC prose, 200% | [Stock PNG](../evidence/stock/round-00/typography-prose-sc-matched-2x.png) | [Aven PNG](../evidence/aven/round-02/typography-prose-sc-matrix-2x.png) |
| TC prose, 200% | [Stock PNG](../evidence/stock/round-00/typography-prose-tc-matched-2x.png) | [Aven PNG](../evidence/aven/round-02/typography-prose-tc-matrix-2x.png) |

## What changed visibly

- **Native Chinese and Latin UI:** Aven's labels and filenames are larger. The full SC “主文件夹” and TC “最近檔案” fit in the wider sidebar. Stock truncates several location names. In both products, Chinese and Latin filenames remain readable with no visible missing-glyph boxes.
- **Hierarchy:** Muted green-gray surfaces and a lighter panel remove much of stock's blue/dark visual weight. The active breadcrumb remains conspicuously bold. This is a surface and hierarchy observation, not proof of better glyph rendering.
- **Files density:** Aven's detail view shows all 12 files while stock's larger inherited thumbnails leave lower files below the viewport. Aven's thumbnails are much smaller and the rows denser. The comparison preserves each integration's defaults; the extra visible files must not be attributed to typography alone.
- **Chinese prose:** The same three SC or TC paragraphs, mixed Latin/numbers, punctuation, and TC/HK corner quotes are visible. The 17 px reading specimen retains its line breaks. At 200%, both products already have clean, well-separated Chinese text; a substantial rasterization advantage is not evident in these pairs.
- **Browser chrome:** Aven adds a server-side window title above Firefox's tab title. This duplicates the page name and moves the paragraph content down by about 38 logical pixels. It also leaves less of the following SC/TC section visible in the same outer frame. The added chrome is more apparent than a difference in prose rendering.
- **Fractional scale:** All eight Aven fractional images were inspected at original pixels. No missing punctuation, glyph boxes, or obvious layout break appeared in the sampled native UI and paragraphs. This is limited to the captured scenes and display backend.

## Runtime and matching conditions

The Aven guest was controlled exclusively for this matrix. No typography, browser, Plasma, or KWin preferences were changed. Both apps were closed between locale changes and launched with matching `LC_ALL`, `LANG`, and `LANGUAGE`, confirmed in `/proc`. Dolphin visibly uses native SC or TC UI. Firefox uses `~/.local/bin/aven-browser`, its Aven profile, one tab, and page zoom 100%. Its TC quit confirmation was still English; these prose captures do not establish complete browser UI localization.

The specimen SHA-256 is identical in both guests: `ff6f9644427439f80bd3b9f0825ec9542ed2d41dfcddb28b9fe54a6f68c9a6b5`. URLs end in `#sc` or `#tc`. Both products use physical outputs 1280×720, 1600×900, 1920×1080, and 2560×1440, respectively, for a constant 1280×720 logical workspace. Outer frames are x=40, y=28, width=1200, height=630. [Geometry records](../typography/aven-matrix-geometry.json) contain acknowledged frame/client sizes.

Outer-frame matching preserves the actual decorations. Aven's integer-scale client is 1192×588, while stock's is 1200×602 for Dolphin and 1200×630 for Firefox. This is not an identical-client-area experiment. Fractional heights can differ by 0.4 logical pixels because of physical pixel rounding.

All 16 Aven runtime scale checks pass. Integer captures use QScreen/KScreen agreement without mapping a temporary surface. Fractional captures use a real mapped QWindow and structured KScreen agreement, with original KWin focus restored after the post-capture probe. The probe reports Noto Sans **11.25 pt / 15 px, weight 400** in Aven, compared with **9.75 pt / 13 px, weight 400** in stock. These are resolved `QFontInfo` values. Both guests already shape SC/TC with the corresponding Noto Sans CJK region and report no missing glyphs in the probe sample.

After capture, Aven was restored to 1920×1200 at scale 1 and both apps were closed. No stock guest controls were used during the Aven round.

## Scope and subsequent judgment

The independent [matrix review](matrix-review.md) found that the larger native UI improves readability, while controlled prose remains similar to stock. It retained Chinese typography at 8.2; this round did not meet the required 8.5. This matrix cannot establish motion, preview behavior, macOS parity, or typography across every web page and mail message. The later [round 03 review](critic-round-03.md) assesses its own primary-scene evidence and leaves these historical observations and manifests unchanged.
