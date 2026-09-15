# Independent Chinese matrix review — round 02 supplement

**All 16 pairs / 32 original PNGs inspected. Chinese typography remains provisionally 8.2/10. Final pass: false.**

Aven is clearly easier to read in native Chinese UI at every tested scale. The improvement comes mainly from larger regular text, readable places labels and better use of detail rows. Simplified and Traditional Chinese prose is clean, but the same stock specimen is already clean and looks very similar. Completing the matrix increases confidence; it does not automatically increase the quality score.

This supplement leaves [the round-02 critique](critic-round-02.md) and [its manifest](../evidence/critic/round-02.json) unchanged. Exact image hashes, runtime-scale facts and pair-by-pair notes are in [matrix-review.json](../evidence/critic/matrix-review.json).

## Inspection and comparability

Independent critic: `/root/critic`. All 32 files were opened with `view_image(detail=original)`, including every SC/TC native UI and prose frame at 1×, 1.25×, 1.5× and 2×. No screenshot was edited or rescaled for judgment. No source or guest UI was changed.

The matrix uses a constant 1280 × 720 logical workspace, with native PNGs of 1280 × 720, 1600 × 900, 1920 × 1080 and 2560 × 1440 respectively. Both outer windows are 1200 × 630 logical px at (40, 28). Product decorations reduce Aven's client area relative to stock; the comparison is not an equal-client-area or font-only experiment. Native Aven text is 15 logical px versus stock 13 px according to the captured Qt font probe. The prose fixture is identical in both guests.

The evidence gate checked all new pairs against their actual bytes and sidecars: hashes, PNG dimensions, shared booted base commit, native application/runtime packages, available fonts and observed scale match. Fractional provenance uses mapped QWindow DPR with KScreen agreement, not rounded QScreen DPR alone. All four Chinese tags now have all four scales in the in-memory combined review. This integrity/coverage result does not grant visual acceptance.

## Findings

- **Native SC and TC:** full places labels, mixed-script filenames, dates and size units are readable at every scale. The actual TC Dolphin labels include 名稱, 家目錄, 最近檔案, 垃圾桶 and 裝置. No missing-glyph boxes, clipped label glyphs, overlap or conspicuous baseline jumps appeared in these samples.
- **Fractional scaling:** 125% has ordinary antialiased softness; neither 125% nor 150% shows an obvious whole-window blur failure. At 2×, dense TC strokes and Latin counters are clearly separated. Stock remains readable too.
- **Prose:** SC paragraphs and TC zh-TW/zh-HK material preserve comfortable leading, corner quotes, book-title marks, dates, numerals and MB. Both versions look very similar. The fixture's authored spacing must not be counted as new Aven system typography.
- **Weight:** the current `日常 · Everyday` breadcrumb remains conspicuously darker than the regular Chinese UI at every scale. This is local emphasis; the regular Chinese body weight does not call for global thinning.
- **Space and rhythm:** Aven's extra Firefox titlebar shifts content down and costs vertical space. This matrix does not resolve the earlier round-02 composer edge/leading mismatch. Browser page content also does not establish full TC browser UI localization.

## Scoring impact and next fixes

Keep **Chinese typography at 8.2 provisionally**. This matrix closes the SC/TC scale evidence gap. It does not establish a dramatic paragraph-rendering advantage over stock, and the observed weight/rhythm issues still prevent an 8.5 judgment for round 02. No new overall score is assigned; the historical 7.5889 mean remains unchanged.

The smallest useful next checks are the current-breadcrumb emphasis, the actual Chinese mail writing surface after its inset/leading fix, and the revised Mozilla chrome. Keep the current regular Noto rendering unless new pixels expose a concrete rasterization problem. Do not add global font distortion to chase a score.

Final pass stays false. Operations and motion have not been witnessed by this critic, and round-03 changes require their own inspected frames. No macOS comparison exists here, so this is not proof of macOS parity.

## Exact paired inspection notes

Every stock/Aven link below points to a PNG actually opened at original resolution. Hashes for both are recorded in the supplemental JSON.

### SC native UI — 1×

[Stock](../evidence/stock/round-00/typography-ui-sc-matrix-1x.png) · [Aven](../evidence/aven/round-02/typography-ui-sc-matrix-1x.png)

Aven native SC labels and mixed filenames are visibly larger and more comfortable than stock. Full sidebar labels fit. Twelve files fit the smaller detail rows; this is layout density, not a font-rendering improvement. Current 日常 · Everyday breadcrumb is conspicuously bold. No missing glyph boxes or clipped Chinese label glyphs observed.

### SC native UI — 1.25×

[Stock](../evidence/stock/round-00/typography-ui-sc-final-1.25x.png) · [Aven](../evidence/aven/round-02/typography-ui-sc-matrix-1.25x.png)

At 125%, Aven SC sidebar labels, filenames, dates and KiB remain readable without overlap. Antialiased edges have ordinary fractional softness, with no obvious whole-window resampling blur. Stock labels remain smaller and some places labels are truncated. Bold current breadcrumb remains heavier than the surrounding regular text.

### SC native UI — 1.5×

[Stock](../evidence/stock/round-00/typography-ui-sc-final-1.5x.png) · [Aven](../evidence/aven/round-02/typography-ui-sc-matrix-1.5x.png)

At 150%, Aven mixed SC/Latin filenames and numeric columns are clear with comfortable regular weight. Sidebar labels fit and rows do not collide. Stock also remains readable but has smaller text and oversized rows. Current breadcrumb emphasis is still too strong.

### SC native UI — 2×

[Stock](../evidence/stock/round-00/typography-ui-sc-matrix-2x.png) · [Aven](../evidence/aven/round-02/typography-ui-sc-matrix-2x.png)

At 2x, Aven SC strokes and Latin counters are clean and distinct. Larger native UI and full sidebar labels remain a useful improvement over stock. Both use readable Noto shaping; the visible improvement is primarily sizing and layout. Dense bold breadcrumb remains darker than the rest of the UI.

### SC prose — 1×

[Stock](../evidence/stock/round-00/typography-prose-sc-matched-1x.png) · [Aven](../evidence/aven/round-02/typography-prose-sc-matrix-1x.png)

All three SC paragraphs are visible in both images, including Chinese quotes, book-title punctuation, 3.6 MB and mixed dates/times. Body weight, line breaks and leading look very similar. Aven adds a titlebar and shifts the same prose down, reducing following-section visibility. No missing glyphs or conspicuous baseline jumps observed.

### SC prose — 1.25×

[Stock](../evidence/stock/round-00/typography-prose-sc-final-1.25x.png) · [Aven](../evidence/aven/round-02/typography-prose-sc-matrix-1.25x.png)

At 125%, SC paragraphs and mixed numerals remain comfortably legible in both versions. Punctuation has normal full-width spacing and no observed dropped or clipped marks. There is no compelling visible Aven paragraph-rasterization advantage; authored content layout is effectively shared.

### SC prose — 1.5×

[Stock](../evidence/stock/round-00/typography-prose-sc-final-1.5x.png) · [Aven](../evidence/aven/round-02/typography-prose-sc-matrix-1.5x.png)

At 150%, SC prose remains clear and balanced against Latin/digits in both captures. The same paragraph wraps and reading rhythm largely persist. Aven chrome is larger but consumes more vertical space. No visible missing glyphs, collision or gross blur in the specimen.

### SC prose — 2×

[Stock](../evidence/stock/round-00/typography-prose-sc-matched-2x.png) · [Aven](../evidence/aven/round-02/typography-prose-sc-matrix-2x.png)

At 2x, both stock and Aven SC prose are clean, with well-separated strokes and comfortable line spacing. The specimen does not establish a major Aven font-rasterization improvement. Native Aven titlebar and tab repeat the long mixed-script title; the tab label fades near its close button.

### TC native UI — 1×

[Stock](../evidence/stock/round-00/typography-ui-tc-matrix-1x.png) · [Aven](../evidence/aven/round-02/typography-ui-tc-matrix-1x.png)

Actual TC native labels such as 名稱, 家目錄, 最近檔案, 垃圾桶 and 裝置 are visible. Aven labels are larger and fit its wider sidebar, with readable mixed-script filenames and date columns. Current location remains unusually heavy. No missing glyph boxes or label overlap observed.

### TC native UI — 1.25×

[Stock](../evidence/stock/round-00/typography-ui-tc-final-1.25x.png) · [Aven](../evidence/aven/round-02/typography-ui-tc-matrix-1.25x.png)

At 125%, Aven TC native labels and mixed filenames remain clear without obvious clipping or baseline problems. Dense Chinese forms retain readable internal space at this size. Stock remains smaller with truncated places text. Heavy active breadcrumb and technical volume labels remain the conspicuous UI details.

### TC native UI — 1.5×

[Stock](../evidence/stock/round-00/typography-ui-tc-final-1.5x.png) · [Aven](../evidence/aven/round-02/typography-ui-tc-matrix-1.5x.png)

At 150%, TC file names and actual localized UI are clear, with regular Chinese/Latin weight balanced in the rows. Aven sidebar names fit fully. Neither frame shows a missing-glyph failure; Aven improves usable text size and detail-view density. Current breadcrumb remains excessively dark relative to row labels.

### TC native UI — 2×

[Stock](../evidence/stock/round-00/typography-ui-tc-matrix-2x.png) · [Aven](../evidence/aven/round-02/typography-ui-tc-matrix-2x.png)

At 2x, dense TC characters have clean distinct strokes in both versions. Aven labels and filenames are easier to scan through size and spacing, without visible clipping. The visibly heavier current breadcrumb remains an isolated emphasis problem, not evidence that regular Chinese body weight should be reduced globally.

### TC prose — 1×

[Stock](../evidence/stock/round-00/typography-prose-tc-matched-1x.png) · [Aven](../evidence/aven/round-02/typography-prose-tc-matrix-1x.png)

The full zh-TW paragraphs and zh-HK paragraph are visible in both captures. Corner quotes around 圖片 and 可以參加, book-title brackets, dates and MB combine naturally with TC text. Line breaks and weight look nearly identical. Aven moves content down with its titlebar; no missing glyphs observed.

### TC prose — 1.25×

[Stock](../evidence/stock/round-00/typography-prose-tc-final-1.25x.png) · [Aven](../evidence/aven/round-02/typography-prose-tc-matrix-1.25x.png)

At 125%, TC dense characters, corner quotation marks and mixed 3.6 MB / 17:30 remain clear in both frames. The same reading rhythm and paragraph wraps are retained. No clipping, collision or conspicuous punctuation-metric defect appears. Aven does not show a material prose-rendering advantage over already-readable stock.

### TC prose — 1.5×

[Stock](../evidence/stock/round-00/typography-prose-tc-final-1.5x.png) · [Aven](../evidence/aven/round-02/typography-prose-tc-matrix-1.5x.png)

At 150%, zh-TW and zh-HK prose remains comfortably readable in both versions; dense strokes are distinct and Latin/numerals have a natural scale. Quotes and book-title marks do not appear stranded by a rendering error. Aven titlebar reduces content height; the page typography itself remains very similar.

### TC prose — 2×

[Stock](../evidence/stock/round-00/typography-prose-tc-matched-2x.png) · [Aven](../evidence/aven/round-02/typography-prose-tc-matrix-2x.png)

At 2x, both TC prose renderings have clean dense-character strokes and balanced regular text. Corner quotes, 《九月行程》, numerals and MB remain visually coherent. The Aven specimen shows no missing glyphs or baseline jumps, but no dramatic improvement over stock paragraph rasterization either. This is page content, not proof of TC browser-chrome localization.
