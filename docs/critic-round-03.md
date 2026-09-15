# Aven critic — round 03

**Provisional result: 8.29/10 overall; Chinese typography 8.4/10. Final pass: false.**

Aven now feels substantially more coherent across the four focused experiences. Files and preview provide the clearest improvement over stock. Firefox and Thunderbird no longer have mismatched lavender strips or duplicate running icons. Photos now has useful album thumbnails and a short navigation strip. The mail writing inset is visibly fixed, but consecutive Chinese lines still have a tighter rhythm than the reading pane.

This is an independent visual review at 1920 × 1200 and 1×. I opened all 38 original PNGs in the 19 stock/Aven pairs below, plus three supplemental images. No source, guest UI or screenshot was changed. The [manifest](../evidence/critic/round-03.json) records exact hashes and capture sidecars.

## Scores

| Category | Score | Rationale |
|---|---:|---|
| Chinese typography | 8.4 | Larger readable native UI, comfortable SC/TC reading, a useful text preview and the corrected writing inset now give Chinese a much more coherent everyday setting. Mixed Latin/numbers and punctuation remain clear. The remaining tight compose line rhythm and heavy native location emphasis keep this provisional 1x score just below 8.5; browser prose remains mostly the same as already-readable stock. |
| Latin typography | 8.4 | Native labels, filenames, browser controls and window titles use a clear coherent text size. The writing inset removes a conspicuous edge problem. Sender-address ellipsis and the tighter compose rhythm remain minor limitations. |
| Files experience | 8.4 | Readable places labels, subdued folder icons, useful grid thumbnails and compact detail rows form a clear primary experience. Removing irrelevant internal-volume noise resolves a major distraction. The remaining technical volume name and heavy active breadcrumb are local finish issues. |
| File preview | 8.5 | Useful image/PDF/text/media content, shared quiet framing, localized metadata, matching size units and the improved PDF backing now feel like one focused feature. The initial media poster still reports an incorrect zero duration; interaction and playback smoothness remain unverified. |
| Browser coherence | 8.4 | The tab strip and toolbar now share the Aven neutral palette, chrome text is readable, and one launcher represents running Firefox. Mature site rendering is preserved. The extra titlebar costs space and repeats the page title, but the application is visibly integrated. |
| Mail coherence | 8.0 | Matching neutral surfaces, jade actions, one task identity, comfortable Chinese reading and the new compose inset make mail visibly coherent. Narrow card-list sender truncation, compact outlined header actions, a mostly-empty top strip and tighter writing leading prevent a higher score. |
| Photo experience | 8.0 | The larger two-row album materially improves browsing, and the short filmstrip restores focus to the main image while exposing neighboring photos. EXIF 6 and alpha fixtures render plausibly without visible regressions. The heavy breadcrumb band and beveled/gradient thumbnail treatment remain less refined than Files. |
| Visual coherence | 8.3 | Desktop, Files, preview and both Mozilla applications now share a recognizable quiet visual language, with muted folder icons and consistent launch/task identity. Photos and mail retain some heavier native controls, so the result is coherent without being uniformly premium. |
| Perceived polish | 8.2 | The conspicuous round 02 integration defects are largely resolved: internal-volume warnings, duplicated launchers, cool Mozilla strips, preview metadata mismatch, cramped writing edge and undersized photo browsing. Remaining small inconsistencies include media zero duration, writing rhythm, sender truncation and heavy Gwenview framing. Motion is not scored from stills. |

The mean is **8.2889**. The overall numerical threshold is met provisionally; Chinese remains below 8.5. Scores describe inspected static appearance and visible usability, not verified operations or motion.

## Three-second judgment

**Yes.** The jade wallpaper, shorter light panel, softer shared decoration and readable Files layout are unmistakably different and more refined than stock at a glance. The corrected browser/mail palette makes that first impression more consistent across applications.

## What changed visibly since round 02

- Files has muted folder icons and a focused places sidebar. The unnamed red capacity warning and irrelevant internal entry are gone; the remaining volume label is readable.
- Preview uses Chinese titles/metadata, the same KiB units as Dolphin, and a gentle neutral PDF backing. Its readable content remains a major improvement over the stock information dock.
- Browser and mail now use compatible pale neutral surfaces. Each running application binds to its pinned launcher.
- Mail composition now has a real document inset. The writing edge no longer feels cramped.
- Photos shows five larger items in the first album row and three in the second. The short filmstrip restores the landscape from round-02 70% fit to 79%; stock without a filmstrip is 92%. The resulting navigation tradeoff is reasonable.

## Remaining targeted work

1. **Chinese writing rhythm.** In the actual compose frame, “周末见！” and “安宁” remain about 24–26 px apart, compared with roughly 30 px in reading/preview. The inset is now comfortable and there is no glyph failure. Reinspect a modest line-height adjustment with a wrapped Chinese paragraph and consecutive signature lines. Preserve message semantics.
2. **Initial media duration.** The inspected poster shows a real frame but says `0:00 / 0:00`; the later playback still correctly shows `0:01 / 0:05`. Show an honest unknown state or real duration before presenting it. A source-only fix earns no credit until captured.
3. **Mail finish.** Sender addresses truncate more than stock in the narrow list; header actions remain compact and outlined, and the upper strip is mostly empty. Improve only through supported native defaults if the tradeoff preserves the reading area.
4. **Photos finish.** Keep the useful larger grid and short strip. The heavy breadcrumb surround, beveled thumbnail borders and filmstrip gradients remain more dated than Files. A supported local option would help; a Gwenview fork is not warranted.
5. **Native breadcrumb weight.** Current locations remain conspicuously bold. Treat this as a minor native limitation if no maintainable local control exists. These images do not justify global Noto distortion or fontconfig remapping to chase one label.

The remaining Chinese issue is consistent writing rhythm, not missing glyphs or globally poor regular-weight rendering. Browser SC/TC prose remains very similar to already-readable stock; shared authored content spacing is not an Aven achievement. The PDF embeds fonts and is not OS fallback evidence.

## Evidence and acceptance limits

The gate accepts all 19 pairs' actual hashes, dimensions, shared booted base commit, native package versions, available fonts and 1× scale provenance. The EXIF orientation-6 waterfall is upright in both guests. Both render the tiny transparency fixture at its native 100% scale.

Current-round TC native Qt UI and the complete four-scale Chinese matrix are still missing. The independently inspected [round-02 matrix supplement](matrix-review.md) remains historical evidence; it is not silently relabeled as round 03. Root reports unchanged fonts, but that does not replace current capture coverage.

No native operations or motion were witnessed by this critic. Static frames cannot establish preview focus return, copy/move correctness, draft persistence, browser downloads, image navigation, response time or smooth animation. Final pass therefore remains false even when individual visual scores exceed 8. No macOS comparison was captured, so this is not a claim of parity with macOS.

## Direct paired observations

Every linked image below was opened at its original resolution.

### Desktop

[Stock](../evidence/stock/round-00/desktop-stable-1x.png) · [Aven](../evidence/aven/round-03/desktop-1x.png)

The broad low-contrast jade wallpaper and shorter light panel are immediately quieter than stock blue relief and nearly full-width dark panel. The desktop silhouette is unmistakably different. Application identities remain recognizable; no motion claim follows from this still.

### Files Home

[Stock](../evidence/stock/round-00/files-home-clean-1x.png) · [Aven](../evidence/aven/round-03/files-home-clean-1x.png)

Aven has full readable places labels, a focused Documents/Downloads/Pictures sidebar, subdued jade folder icons and softer decoration. The unnamed red capacity bar and extra internal volume are absent; only the readable fedora_aven-lab volume remains. Both show the same nine Home entries, but stock is a grid and Aven a details list. Current Home breadcrumb is still heavy.

### Files List

[Stock](../evidence/stock/round-00/files-list-1x.png) · [Aven](../evidence/aven/round-03/files-list-1x.png)

The same twelve mixed files are visible. Aven uses larger readable text, compact rows, smaller thumbnails and no tree-branch clutter. Chinese/Latin filenames, dates and KiB are clear without clipping. The simplified sidebar removes the stock internal-volume noise. Current 日常 · Everyday location remains conspicuously bold.

### Files Mixed

[Stock](../evidence/stock/round-00/files-mixed-clean-1x.png) · [Aven](../evidence/aven/round-03/files-mixed-1x.png)

Aven gives the twelve files four spacious columns and larger thumbnails; stock puts nine small items across its first row. Mixed-script filenames fit on one line in Aven. The jade selection and focused sidebar are calmer. Selection state differs: Aven selects the video while stock shows the Earthrise focus outline. Generic document/media icons retain their application-native colors.

### Preview Image

[Stock](../evidence/stock/round-00/preview-image-1x.png) · [Aven](../evidence/aven/round-03/preview-image-1x.png)

Aven shows the complete Earthrise image at a useful size in a restrained floating preview; stock confines it to a tiny information dock thumbnail. The owned title/footer now use Chinese 预览 and JPEG 图像; 84.1 KiB matches Dolphin. Soft chrome and the clearly spaced Open control form a coherent surface. Invocation and focus return are not established by the still.

### Preview Pdf

[Stock](../evidence/stock/round-00/preview-pdf-1x.png) · [Aven](../evidence/aven/round-03/preview-pdf-1x.png)

Aven makes the bilingual title and Chinese paragraphs readable, with a scrollable fitted-width page instead of stock tiny whole-page thumbnail. The former medium-gray backing is now a gentle pale neutral. PDF 文档 and 260.6 KiB match the Chinese preview and Dolphin. Embedded document fonts are not credited as OS fallback quality.

### Preview Text

[Stock](../evidence/stock/round-00/preview-text-1x.png) · [Aven](../evidence/aven/round-03/preview-text-1x.png)

Aven exposes the real SC paragraphs, mixed Latin/numbers, Chinese punctuation, dense-character sample and emoji instead of stock generic text icon. Its inset and line spacing make the text comfortable. 纯文本 and 1.1 KiB now make the footer consistent with the rest of the preview. No visible missing-glyph boxes or clipping appear in this sample.

### Preview Media

[Stock](../evidence/stock/round-00/preview-media-1x.png) · [Aven](../evidence/aven/round-03/preview-media-1x.png)

Aven shows a useful large flower frame with simple play/pause, seek and 0:01 / 0:05 controls; stock provides only a small metadata-dock player. Chinese WebM 视频 and 541.1 KiB match the other preview surfaces. The separately inspected initial poster still says 0:00 / 0:00 before playback, a misleading unready-duration detail. Playback moments differ and static frames cannot establish continuity or motion.

### Browser Sc

[Stock](../evidence/stock/round-00/browser-sc-1x.png) · [Aven](../evidence/aven/round-03/browser-sc-1x.png)

The same SC article is readable in both. Aven now blends its tab strip, toolbar and shared titlebar into one pale neutral family, with a single running Firefox launcher. Larger chrome text is legible. The authored article typography looks effectively unchanged and is not credited as new Aven layout. The extra native titlebar still costs about 38 logical px of content height. Stock has a transient header focus ring absent in Aven.

### Browser Tc

[Stock](../evidence/stock/round-00/browser-tc-1x.png) · [Aven](../evidence/aven/round-03/browser-tc-1x.png)

Both render TC paragraphs, corner quotes, Chinese/Latin text and numbers clearly. Aven removes the cool tab-strip clash and duplicate task icon while retaining recognizable Firefox controls. The body remains very similar to stock. This proves readable TC page content, not full TC browser localization or native TC Qt coverage.

### Browser Web

[Stock](../evidence/stock/round-00/browser-web-1x.png) · [Aven](../evidence/aven/round-03/browser-web-1x.png)

The live Chinese Firefox website retains its own graphics and readable text inside Aven shared neutral chrome. No duplicate Firefox task icon is visible. Stock has an additional background tab and a redirect query in its URL; page animation timing differs. The extra Aven titlebar reduces content height, but the chrome no longer looks like a separate lavender application skin.

### Mail List

[Stock](../evidence/stock/round-00/mail-list-1x.png) · [Aven](../evidence/aven/round-03/mail-list-1x.png)

Aven now has a coherent pale neutral toolbar and panes, jade Write action and one running Thunderbird launcher. Chinese/Latin row labels are comfortably larger than stock. Three sender addresses still truncate more than stock in the narrower card list. The broad mostly-empty upper toolbar and outlined message cards remain conventional Thunderbird rather than highly refined consumer mail.

### Mail Sc

[Stock](../evidence/stock/round-00/mail-sc-1x.png) · [Aven](../evidence/aven/round-03/mail-sc-1x.png)

Aven reading text has a useful left inset and relaxed roughly 30 px lines; Chinese, PDF, README.txt, times and 2.5 km stay naturally balanced. The main toolbar now matches the surrounding surfaces and the duplicate task icon is gone. Header actions remain compact and outlined; sender-list ellipsis persists. No missing glyphs are visible.

### Mail Tc

[Stock](../evidence/stock/round-00/mail-tc-1x.png) · [Aven](../evidence/aven/round-03/mail-tc-1x.png)

The TC message is clearly readable with comfortable margins and line spacing, including dense characters, corner quotes, the em dash and v2.1. The neutral Aven chrome is coherent and only one Thunderbird task entry appears. Smaller header actions and truncated sender addresses are remaining local finish issues. This is TC message content within the captured SC application UI.

### Mail Compose

[Stock](../evidence/stock/round-00/mail-compose-1x.png) · [Aven](../evidence/aven/round-03/mail-compose-1x.png)

The same draft and appended route confirmation are visible. Aven now places the editable document inside a real pale inset, giving Chinese writing a comfortable buffer from the window edge. Its chrome and controls blend with the main mail window. Regular Chinese text is clear, but consecutive 周末见！ / 安宁 lines remain about 24–26 px apart versus roughly 30 px in reading/preview; writing rhythm is still somewhat tighter. The screenshot does not establish save/reopen behavior.

### Photos Grid

[Stock](../evidence/stock/round-00/photos-grid-1x.png) · [Aven](../evidence/aven/round-03/photos-grid-1x.png)

The same eight Kyoto photos now form a useful two-row album with five larger items across the first row, instead of stock eight small thumbnails in one row. Image contents and Chinese filenames are much easier to browse. The gray breadcrumb surround and bold current location remain heavier than Files, and thumbnail frames are still visibly beveled. The main density problem from round 02 is fixed.

### Photos View

[Stock](../evidence/stock/round-00/photos-view-1x.png) · [Aven](../evidence/aven/round-03/photos-view-1x.png)

The same complete landscape is visible in a large clean viewing area. Aven now uses a short roughly 80 px filmstrip, and image fit is 79%, improved from round 02 70%; stock without a strip is 92%. Adjacent images are useful and no longer dominate the composition. The retained strip is a reasonable navigation tradeoff, though its gradient/beveled tiles and full-width scrollbar still feel dated.

### Photo Exif

[Stock](../evidence/stock/round-00/photo-exif-1x.png) · [Aven](../evidence/aven/round-03/photo-exif-1x.png)

The same EXIF orientation 6 waterfall is upright in both: top, bottom, left and right labels all appear in their expected positions. Aven displays the full image at 56% versus stock 65% because it reserves a short navigation strip. No visible rotation or crop regression appears in this fixture. This does not prove every EXIF case or color-management accuracy.

### Photo Alpha

[Stock](../evidence/stock/round-00/photo-alpha-1x.png) · [Aven](../evidence/aven/round-03/photo-alpha-1x.png)

Both show the same 32 × 32 transparency gradient at 100%, without artificially enlarging the tiny image. Aven visibly supplies a neutral/checkered backing where stock blends the transparent side into white. The native image remains tiny by design. This confirms a rendered transparent fixture only; it is not a comprehensive compositing or color-accuracy test.

## Supplemental images and exclusions

- [preview-media-poster-1x.png](../evidence/aven/round-03/preview-media-poster-1x.png): Initial flower poster is visible with play control, but duration reads 0:00 / 0:00. Later paired playback still correctly shows 0:01 / 0:05. Source-only correction is not visually credited in this round.
- [photo-portrait-1x.png](../evidence/stock/round-00/photo-portrait-1x.png): Stock shows the upright waterfall portrait fixture, not the Kyoto pagoda; excluded from direct portrait pairing.
- [photos-portrait-1x.png](../evidence/aven/round-03/photos-portrait-1x.png): Aven shows a complete upright Kyoto pagoda portrait, fitted at 47%, with short filmstrip. No matching stock capture among the nominated primary scenes; no comparative portrait score is assigned.

The stock waterfall portrait and Aven Kyoto pagoda are different source images, so they are excluded from direct portrait pairing. The poster is an additional Aven readiness state, not a duplicate reuse of the stock media pair.
