# Typography: round 04 paired observations

**All 16 current Aven images and their 16 canonical stock counterparts were opened at original resolution.** All image hashes, PNG dimensions, runtime scales, native package versions, font packages and booted/base commits match the recorded comparison conditions. This typography-agent report assigns no critic scores or product pass.

The final profile retains readable SC/TC native text and now gives Firefox chrome a coherent neutral surface. The controlled Chinese prose remains very similar to stock. These images support a visible improvement in native UI size and application integration; they do not establish a dramatic improvement in paragraph rasterization.

## Evidence

- [Round 04 matrix manifest](../typography/aven-round04-matrix.json): 16 exact image hashes, stock pairings, original-pixel inspection observations, runtime font/shaping results and integrity checks.
- [Acknowledged capture geometry](../typography/aven-round04-matrix-geometry.json), [process locales](../typography/aven-round04-process-locales.json), and [restoration evidence](../typography/aven-round04-restoration.json).
- [Executed capture plan](typography-round04-plan.md) and [canonical stock protocol](typography-stock-matrix.md).
- Historical [round 02 findings](typography-paired-findings.md), [manifest](../typography/aven-matrix.json) and images remain unchanged.

## Observations

**Native SC and TC UI:** the larger labels remain readable at 100%, 125%, 150% and 200%. The full SC 主文件夹 and TC 最近檔案 fit in the wider sidebar. TC uses actual localized labels including 家目錄, 垃圾桶, 名稱 and 已變更. Chinese filenames, Latin extensions, dates and KiB values show no visible missing-glyph boxes or clipped label glyphs in these frames. All 12 files fit because Aven uses smaller thumbnails and denser detail rows; that density benefit is not a font-rendering result.

**Regular weight and emphasis:** ordinary native text remains balanced and readable. The current `日常 · Everyday` breadcrumb is conspicuously darker than surrounding labels at every scale. The separate [native weight investigation](typography-bold-investigation.md) confirmed real 700 shaping, distinct from 900; no ineffective fontconfig remap was installed. These images do not justify globally thinning Noto.

**Chinese paragraphs:** all three SC or Taiwan TC paragraphs are visible at each scale. The TC views also show the complete Hong Kong paragraph. Corner quotes, book-title marks, dates, times, Latin and MB retain clear spacing and stable wraps. Both guests render this identical 17 px / 1.75 fixture cleanly; a material Aven rasterization advantage is not evident. The authored reading rhythm belongs to the shared fixture.

**Fractional scales:** 125% has ordinary antialiased edge softness, without an obvious whole-window blur failure in the inspected samples. At 150%, native mixed-script rows and prose remain clear, with no conspicuous baseline jumps or punctuation collisions. At 200%, dense SC/TC strokes and Latin counters are distinct in both products. This observation is limited to the actual VM display backend and captured scenes.

**Browser integration:** Firefox's tabs, toolbar and shared decoration now use compatible neutral surfaces. The extra server-side titlebar still repeats the page title and shifts content down by about 38 logical pixels compared with stock. The matched outer frame therefore exposes less following-section content. Browser page typography itself remains very similar to stock. The TC process environment was correct, but its quit confirmation remained English; this does not prove complete TC browser UI localization.

## Matching and runtime facts

Both apps were closed and relaunched for each locale with explicit `LC_ALL`, `LANG` and `LANGUAGE`, verified through `/proc`. Firefox used the installed Aven wrapper/profile, a single tab and 100% page zoom. Dolphin used one tab, native detail view and the same mixed fixture folder at the top. A restored Home tab was closed before the first retained SC capture. No font, profile, styling or power-management preference was changed during the matrix.

The fixture SHA-256 is `ff6f9644427439f80bd3b9f0825ec9542ed2d41dfcddb28b9fe54a6f68c9a6b5`. Physical outputs were 1280×720, 1600×900, 1920×1080 and 2560×1440, producing a constant 1280×720 logical workspace. All 16 current outer frames acknowledged x=40, y=28, width=1200, height=630; their client areas were 1192×588. Stock retains its actual decorations and larger client area. This is an equal-outer-frame comparison, not an equal-client-area experiment.

Every current runtime probe reports Noto Sans **11.25 pt / 15 px, weight 400**, with the corresponding Noto Sans CJK SC or TC Regular shaping run and no missing glyphs in its sample. Stock resolves **9.75 pt / 13 px, weight 400** and already has correct SC/TC fallback. Integer scale checks use QScreen/KScreen agreement without mapping a window. Fractional checks use a real mapped QWindow DPR agreeing with KScreen at 1.25 or 1.5; QScreen remains honestly 2. Original focus UUID restoration is verified after each fractional probe. No menu/popover was open in these scenes.

SC Aven has a first-row focus outline at all four scales; canonical stock SC has it only at integer scales. TC has no visible selected row. This recorded state difference is not evidence about Aven selection design.

After capture, the display was restored to **1920×1200 at scale 1**. Both apps were arranged to their normal **1440×900 outer frames at (240,100)** before native quit. KWin inventory and process checks confirm both apps were closed before GUI control returned to root.

## Scope

The independent critic must judge the current matrix alongside the current primary scenes. This report does not revise earlier scores. The separate mail compose leading correction is outside these 16 frames. These still images cannot establish motion, file-operation reliability, rendering on every physical panel, arbitrary web/mail content, or macOS parity.

## Exact inspected pairs

The matrix manifest contains per-pair observations and complete hashes. Every link below points to an original PNG opened during this review.

| Scene | Scale | Stock | Aven round 04 |
|---|---:|---|---|
| SC native UI | 1× | [Stock](../evidence/stock/round-00/typography-ui-sc-matrix-1x.png) | [Aven](../evidence/aven/round-04/typography-ui-sc-matrix-1x.png) |
| SC native UI | 1.25× | [Stock](../evidence/stock/round-00/typography-ui-sc-final-1.25x.png) | [Aven](../evidence/aven/round-04/typography-ui-sc-matrix-1.25x.png) |
| SC native UI | 1.5× | [Stock](../evidence/stock/round-00/typography-ui-sc-final-1.5x.png) | [Aven](../evidence/aven/round-04/typography-ui-sc-matrix-1.5x.png) |
| SC native UI | 2× | [Stock](../evidence/stock/round-00/typography-ui-sc-matrix-2x.png) | [Aven](../evidence/aven/round-04/typography-ui-sc-matrix-2x.png) |
| SC prose | 1× | [Stock](../evidence/stock/round-00/typography-prose-sc-matched-1x.png) | [Aven](../evidence/aven/round-04/typography-prose-sc-matrix-1x.png) |
| SC prose | 1.25× | [Stock](../evidence/stock/round-00/typography-prose-sc-final-1.25x.png) | [Aven](../evidence/aven/round-04/typography-prose-sc-matrix-1.25x.png) |
| SC prose | 1.5× | [Stock](../evidence/stock/round-00/typography-prose-sc-final-1.5x.png) | [Aven](../evidence/aven/round-04/typography-prose-sc-matrix-1.5x.png) |
| SC prose | 2× | [Stock](../evidence/stock/round-00/typography-prose-sc-matched-2x.png) | [Aven](../evidence/aven/round-04/typography-prose-sc-matrix-2x.png) |
| TC native UI | 1× | [Stock](../evidence/stock/round-00/typography-ui-tc-matrix-1x.png) | [Aven](../evidence/aven/round-04/typography-ui-tc-matrix-1x.png) |
| TC native UI | 1.25× | [Stock](../evidence/stock/round-00/typography-ui-tc-final-1.25x.png) | [Aven](../evidence/aven/round-04/typography-ui-tc-matrix-1.25x.png) |
| TC native UI | 1.5× | [Stock](../evidence/stock/round-00/typography-ui-tc-final-1.5x.png) | [Aven](../evidence/aven/round-04/typography-ui-tc-matrix-1.5x.png) |
| TC native UI | 2× | [Stock](../evidence/stock/round-00/typography-ui-tc-matrix-2x.png) | [Aven](../evidence/aven/round-04/typography-ui-tc-matrix-2x.png) |
| TC prose | 1× | [Stock](../evidence/stock/round-00/typography-prose-tc-matched-1x.png) | [Aven](../evidence/aven/round-04/typography-prose-tc-matrix-1x.png) |
| TC prose | 1.25× | [Stock](../evidence/stock/round-00/typography-prose-tc-final-1.25x.png) | [Aven](../evidence/aven/round-04/typography-prose-tc-matrix-1.25x.png) |
| TC prose | 1.5× | [Stock](../evidence/stock/round-00/typography-prose-tc-final-1.5x.png) | [Aven](../evidence/aven/round-04/typography-prose-tc-matrix-1.5x.png) |
| TC prose | 2× | [Stock](../evidence/stock/round-00/typography-prose-tc-matched-2x.png) | [Aven](../evidence/aven/round-04/typography-prose-tc-matrix-2x.png) |
