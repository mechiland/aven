# Aven critic — round 02

**Provisional result: 7.59/10 overall; Chinese typography 8.2/10. Not passing.**

Aven is immediately quieter than stock, and Files plus preview show meaningful improvement. Browser and mail still have visible integration gaps. Photos is the weakest experience: browsing remains a small row of thumbnails, and the large viewer filmstrip takes too much space from the photograph.

## Inspection

Independent critic: `/root/critic`. Inspection completed 2026-09-15T05:32:08.362203+00:00. I opened all 34 unmodified PNGs in the 17 pairs below and compared them directly. I did not modify source, operate either guest, or update shared status.

This is a visual review at 1920 × 1200 and 1× scaling. It is not final acceptance. The complete Chinese scaling matrix, native operation evidence and motion review remain pending. The manifest records exact screenshot hashes and capture sidecars: [round-02.json](../evidence/critic/round-02.json).

The evidence gate accepted the cited framebuffers, hashes, shared base commit, native package versions, font availability and integer-scale provenance. It rejects final acceptance for the scores below the requested thresholds and incomplete coverage. The ready PDF capture is used; the premature `preview-pdf` image is excluded.

## Scores

| Category | Score | Judgment |
|---|---:|---|
| Chinese typography | 8.2 | The larger native Chinese UI and readable preview/mail prose are a clear improvement. Simplified and Traditional Chinese body samples have balanced Latin/numerals and no visible missing glyphs. Heavy current breadcrumbs, uneven reading-versus-composing rhythm, and only modest differentiation in browser content keep the observed 1x result below the 8.5 premium reading target. |
| Latin typography | 8.3 | Native filenames, window titles and labels are calmer and more legible than the small stock UI. Mixed English/Chinese text has a natural size balance. Mail sender ellipsis and uneven editor margins still interrupt the rhythm. |
| Files experience | 8.0 | The wider places sidebar, quieter details view, larger image grid and readable filenames make Files visibly more useful. Internal volume labels and the unnamed red capacity bar remain a distracting unfinished detail. |
| File preview | 8.4 | The strongest improvement: actual readable content replaces tiny thumbnails or a generic icon, with a restrained shared window and obvious Open control. Minor finish issues are inconsistent size units, English metadata in Chinese chrome and the darker PDF backing. |
| Browser coherence | 7.0 | Firefox retains mature browsing and adopts shared external decoration, but the lavender tab strip visibly clashes with Aven chrome. The duplicate pinned/running icon is an integration defect. Web typography is good but mostly already good in the stock fixture. |
| Mail coherence | 7.3 | Reading gains useful margins and line spacing, and the jade accent connects it to Files. The empty cool-colored upper strip, cramped composer body edge, compact outlined header actions and duplicate task icon still make it feel only partially integrated. |
| Photo experience | 6.5 | Shared fonts and surfaces improve the frame, but browsing remains a small single thumbnail row. The oversized filmstrip reduces the main photograph from stock 92% fit to 70% fit. This is the least convincing everyday-experience improvement. |
| Visual coherence | 7.3 | Wallpaper, panel, decoration, Files and preview form a recognizable restrained visual language. Mozilla interior chrome and duplicated task entries break the single-product impression. Gwenview retains an overly heavy breadcrumb surround and thumbnail strip. |
| Perceived polish | 7.3 | Aven is visibly more intentional and useful, especially in Files and preview. Duplicate launch/task icons, the internal-volume alarm-like bar, uneven text margins and unbalanced photo browsing are conspicuous enough to prevent product-grade overall finish. |

**Mean of all nine scores: 7.5889. Required: ≥8 overall and ≥8.5 Chinese.**

## Three-second question

**Yes.** The desktop and primary Files surfaces are unmistakably different and more refined within a glance. The broad jade wallpaper, shorter light panel, softer decoration and legible Files layout establish a distinct direction. This affirmative first impression does not mean all four application experiences are product-grade.

## Fix next

1. **Photos — priority 1.** Increase browse thumbnails enough for a useful multi-row album (try 240–280 logical px), and reduce the viewer filmstrip to roughly 84–100 logical px. Recheck both landscape and portrait before choosing the final defaults.
2. **Browser/Mail launcher identity — priority 1.** Make each running native application bind to its pinned Aven launcher so one icon represents one app. Retain the real Firefox/Thunderbird application identity.
3. **Mozilla chrome — priority 1.** Bring the lavender tab/toolbar strips into the same neutral surface family as the shared titlebar using the smallest supported theme/configuration change. Keep site and message content rendering independent.
4. **Mail writing typography — priority 1.** Give the compose body a modest reading-like inset, around 24 px, and verify comfortable Chinese line/paragraph rhythm without changing message semantics.
5. **Files sidebar — priority 2.** Hide only known irrelevant internal/immutable system-volume entries by default or give useful volumes meaningful labels. Do not suppress a real user-volume capacity warning or remove device access.
6. **Chinese UI weight — priority 2.** Check the actual current-breadcrumb weight against the regular Chinese UI. Reduce the visually heavy emphasis only if a small maintainable native adjustment is available; avoid global fake bold or font distortion.
7. **Preview details — priority 2.** Use the same byte-size convention as Dolphin and a gentler neutral PDF backing. Localize owned metadata labels consistently where feasible.

The visible application brands are not a defect. The concrete launcher defect is that a running Firefox or Thunderbird appears as a second task next to its pinned launcher. Fix the association while preserving application identity.

## Direct paired observations

Every linked stock and Aven image in this section was opened and inspected. The filenames identify the exact immutable capture, including the cleaned browser frames and ready PDF frame.

### Desktop

[Stock](../evidence/stock/round-00/desktop-stable-1x.png) · [Aven](../evidence/aven/round-02/desktop-1x.png)

Aven replaces the busy blue relief wallpaper and nearly full-width dark panel with broad low-contrast jade forms and a shorter light panel. Its overall silhouette is immediately quieter. Application identities remain recognizable.

### Files Home

[Stock](../evidence/stock/round-00/files-home-clean-1x.png) · [Aven](../evidence/aven/round-02/files-home-1x.png)

Aven uses a readable 224 px places sidebar, larger UI text, calmer selection, and softer decoration. Stock truncates ordinary sidebar labels. Aven Home is a list while stock is a grid; Aven also contains an extra thunderbird folder, so this pair is a default-presentation comparison, not identical directory state. An unnamed red capacity bar and internal device identifiers remain conspicuous.

### Files List

[Stock](../evidence/stock/round-00/files-list-1x.png) · [Aven](../evidence/aven/round-02/files-list-1x.png)

The same 12 files are visible. Aven removes visual tree-branch clutter, increases label size, and reduces the oversized stock rows. Mixed Chinese/Latin filenames remain readable without clipping. The current breadcrumb is markedly heavy compared with regular row text. Fixed-volume capacity bars distract from everyday places.

### Files Mixed

[Stock](../evidence/stock/round-00/files-mixed-clean-1x.png) · [Aven](../evidence/aven/round-02/files-mixed-1x.png)

Aven presents four larger previews per row instead of nine small items across the first stock row. Long mixed-language filenames now fit on a single line and image contents are much easier to distinguish. The native generic media/document icons remain recognizable. The wide sidebar is useful; internal volume entries still add unrelated visual noise.

### Preview Image

[Stock](../evidence/stock/round-00/preview-image-1x.png) · [Aven](../evidence/aven/round-02/preview-image-1x.png)

Stock shows only a small image in a narrow metadata dock. Aven shows the complete image at a useful size in a restrained floating preview, preserving the selected file behind it. The native Open action is legible. The footer says 86.1 KB while Dolphin says 84.1 KiB for the same bytes.

### Preview Pdf

[Stock](../evidence/stock/round-00/preview-pdf-1x.png) · [Aven](../evidence/aven/round-02/preview-pdf-ready-1x.png)

The ready Aven preview makes the title and Chinese paragraphs readable; stock only offers a tiny whole-page thumbnail. Aven fits page width and exposes a scrollbar for the rest of the page. The medium-gray PDF backing is harsher than the other Aven preview surfaces. Embedded document typography is not evidence that the OS font fallback improved. The premature Aven preview-pdf capture is excluded.

### Preview Text

[Stock](../evidence/stock/round-00/preview-text-1x.png) · [Aven](../evidence/aven/round-02/preview-text-1x.png)

Stock displays a generic text icon and metadata without the document text. Aven displays actual paragraphs, mixed Latin and numbers, Chinese punctuation and emoji. Regular Chinese text has comfortable leading and clear counters. English metadata in the footer is less integrated with the Chinese Open action; binary-versus-decimal sizes differ from Dolphin.

### Preview Media

[Stock](../evidence/stock/round-00/preview-media-1x.png) · [Aven](../evidence/aven/round-02/preview-media-1x.png)

Aven provides a large video surface and clearly spaced play/pause, seek and time controls. Stock confines playback to its narrow information dock. The captured video frame differs because playback time differs. A static image proves a rendered frame, not continuous playback, latency, audio quality or smooth motion.

### Browser Sc

[Stock](../evidence/stock/round-00/browser-sc-1x.png) · [Aven](../evidence/aven/round-02/browser-sc-clean-1x.png)

The same article remains readable with balanced Chinese/Latin text. Most page typography was already good in stock; its authored layout must not be credited as an Aven redesign. Aven adds the shared native titlebar, but the Firefox tab strip retains a cool lavender-gray fill against the warmer window chrome. The panel shows separate pinned and running Firefox icons. The stock header focus ring is absent in Aven, a transient focus-state difference.

### Browser Tc

[Stock](../evidence/stock/round-00/browser-tc-1x.png) · [Aven](../evidence/aven/round-02/browser-tc-clean-1x.png)

Traditional Chinese paragraphs, corner quotes and mixed Latin/numbers render clearly in both versions. Aven chrome text is larger and its window surface is calmer, but the tab strip remains visibly separate from the Aven palette. Aven has a duplicate Firefox panel icon. This is Traditional Chinese page content, not evidence of Traditional Chinese native Qt UI.

### Browser Web

[Stock](../evidence/stock/round-00/browser-web-1x.png) · [Aven](../evidence/aven/round-02/browser-web-1x.png)

Both images show the live firefox.com Chinese page with its own design and graphics intact. Aven provides consistent external window controls but has three visibly different chrome bands and a duplicate task icon. The extra titlebar consumes some content height. Page animation and the first background tab differ; no site behavior or loading-performance judgment is made from these frames.

### Mail List

[Stock](../evidence/stock/round-00/mail-list-1x.png) · [Aven](../evidence/aven/round-02/mail-list-1x.png)

Aven enlarges and softens UI text and uses the shared jade accent. Its narrower message list truncates more sender addresses than stock. The broad empty lavender-gray toolbar band conflicts with the warmer panels below. A second Thunderbird task icon is visible beside the pinned launcher.

### Mail Sc

[Stock](../evidence/stock/round-00/mail-sc-1x.png) · [Aven](../evidence/aven/round-02/mail-sc-1x.png)

Aven adds useful body margins and more comfortable paragraph leading. Chinese text and embedded times, PDF, README.txt and 2.5 km remain legible and naturally balanced. The header actions remain compact and heavily outlined. The upper toolbar color and duplicate task icon weaken product coherence.

### Mail Tc

[Stock](../evidence/stock/round-00/mail-tc-1x.png) · [Aven](../evidence/aven/round-02/mail-tc-1x.png)

The Traditional Chinese body is comfortably readable in Aven, with clear dense characters, corner quotation marks, numbers and em dash. Body margins and leading are better than stock. The message-list width causes extra ellipsis, and the cool upper band remains discordant. No missing glyphs are visible in this text sample.

### Mail Compose

[Stock](../evidence/stock/round-00/mail-compose-1x.png) · [Aven](../evidence/aven/round-02/mail-compose-1x.png)

Both show the same draft text and appended confirmation. Aven decoration, labels and controls are calmer, but the writing body still begins only a few pixels from the left edge, unlike the comfortable reading pane. Compose leading is also tighter than the reading view. The large form/formatting area still feels like conventional Thunderbird. This pair does not itself establish successful saving or sending.

### Photos Grid

[Stock](../evidence/stock/round-00/photos-grid-1x.png) · [Aven](../evidence/aven/round-02/photos-grid-1x.png)

Aven makes text slightly larger and shares the soft chrome, but the eight photos still form one small row at the top of a mostly empty window. The 144 px-style thumbnails are too small to make browsing feel substantially better than stock. The active Chinese breadcrumb looks disproportionately bold.

### Photos View

[Stock](../evidence/stock/round-00/photos-view-1x.png) · [Aven](../evidence/aven/round-02/photos-view-1x.png)

The same complete landscape is displayed without a visible orientation problem. Aven exposes useful adjacent images, but its roughly 150 px-tall filmstrip consumes too much space: the title reports 70% versus stock 92%, and the main image is substantially smaller. The strip is visually heavier than the image-viewing chrome. A shorter strip would retain navigation while restoring focus to the photograph.

## Typography conclusions and limits

The actual Chinese material includes Dolphin labels and mixed filenames, a native Qt text preview, Simplified and Traditional Chinese browser paragraphs, and Simplified and Traditional Chinese email bodies. The preview shows punctuation, dense characters, mixed Latin/numbers and emoji. The larger native UI is easier to read than stock; the mail reading pane gains useful margins and leading. No missing glyphs are visible in these samples.

The remaining concern is consistent reading rhythm and weight across surfaces. Current breadcrumbs look heavier than surrounding text; the compose editor remains tight against its edge and more compressed than the reading pane. The browser article typography is already good in stock, so its authored page design cannot be counted as a new Aven achievement. The PDF embeds its own fonts and is evidence of useful preview sizing, not OS-wide font fallback.

This review does not establish Traditional Chinese native Qt UI quality or any fractional/HiDPI result. Those must be judged from their own paired screenshots. No inference from fontconfig output substitutes for that inspection.

## Pending before acceptance

- Complete paired Simplified/Traditional Chinese prose and native Qt UI at 1x, 1.25x, 1.5x and 2x.
- Witness native operations and inspect their evidence.
- Inspect paired motion recordings or observe motion live.
- Reinspect corrected Photos, Firefox/Thunderbird chrome and launcher identity, composer margins and Files sidebar.

EXIF orientation, transparency and full-screen behavior also need their corresponding paired evidence. Static video frames and window screenshots cannot establish animation smoothness, playback continuity, audio quality or preview latency. Native operation results from another agent may be valid engineering evidence, but this critic has not yet inspected or witnessed them in this round.
