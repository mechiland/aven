# Round 06 native typography inspection

Inspected original-resolution captures:

- [Files, Chinese, 2×](../evidence/aven/round-06/files-sc-final-2x.png)
- [Mail, Chinese, 2×](../evidence/aven/round-06/mail-sc-final-2x.png)
- [Browser, Chinese, 2×](../evidence/aven/round-06/browser-sc-final-2x.png)
- [Photos, 2×](../evidence/aven/round-06/photos-final-2x.png)
- [Files first, 1×](../evidence/aven/round-06/files-first-1x.png)
- [Files palette corrected, 1×](../evidence/aven/round-06/files-palette-corrected-1x.png)
- [Files, title 500 deployment, 1×](../evidence/aven/round-06/files-sc-accepted-1x.png)
- [Files, title 500 deployment, 2×](../evidence/aven/round-06/files-sc-accepted-2x.png)
- [Text preview, 1×](../evidence/aven/round-06/preview-text-accepted-1x.png)
- [Files after explicit KWin reconfigure, 2×](../evidence/aven/round-06/files-sc-refreshed-title-2x.png)
- [Files after live platform font refresh and wake, 2×](../evidence/aven/round-06/files-sc-awake-current-2x.png)
- [Files after fresh guest boot, final 500 title at 2×](../evidence/aven/round-06/files-sc-reboot-2x.png)

Root identifies the final captures as native 3840×2160 at 2×. The inspected
macOS Applications, Mail, Safari, and Photos references are the original PNGs
in `/home/michael/Downloads/macOS15Screens`, as recorded in
[the reference review](round06-reference-review.md). This is a visual review
of the shown states, without a score or a matched-stock acceptance decision.

The final 2× Files capture shows clean Latin contours and distinguishable
Chinese strokes in ordinary rows, including mixed-script filenames and the
Traditional Chinese filename. Names, sizes, dates, tabs, and the status line
fit their rows without visible top/bottom clipping or baseline collision.
The reduced UI size creates a more compact hierarchy than the earlier
round-05 Files capture inspected in the reference review. It does not
establish matching rasterization across the different capture scales.

The strongest remaining weight mismatch is the current-location breadcrumb:
`日常 · Everyday` in Files and `京都春日` in Photos are substantially darker
than adjacent labels. The Chinese portions of the centered window titles also
look heavier than the adjacent Latin text. The screenshots support that visible
imbalance; they do not by themselves identify an exact font instance or weight.
The known native bold breadcrumb and CJK named-weight limitation remain
relevant, and global thinning would also affect already readable regular text.

Following this inspection, `window_title.weight` is revised from 600 to 500,
keeping the 14 px size. Both Adwaita Sans and Noto CJK provide a named Medium
instance, making this a controlled compromise for mixed-script titles. Other
roles remain unchanged, and the native bold breadcrumb is unaffected.

Root subsequently deployed the requested 500 title role and supplied the
`files-sc-accepted-1x` and `files-sc-accepted-2x` captures. Both were inspected
at original resolution. The title is readable and uncut at both scales, but
the Chinese `日常` remains visibly heavier than `Everyday`. No visible weight
reduction is established by these images: the 2× title region from physical
coordinates `(1760, 166)` to `(2180, 210)` is pixel-identical to the earlier
`files-sc-final-2x` title, with zero differing pixels out of 18,480. That region
comparison used the unresized native PNGs. The configuration now requests 500,
but an effective change in the rendered title is not demonstrated. This is a
remaining fidelity issue, not a missing-glyph or readability blocker. The
current-folder breadcrumb remains the stronger, unchanged emphasis.

The subsequent `files-sc-refreshed-title-2x` capture was also inspected after
root reported a successful explicit KWin reconfigure. Its same title region
is still pixel-identical to `files-sc-final-2x` (zero of 18,480 pixels differ),
and the Chinese/Latin weight imbalance remains visible. Therefore the reload
alone did not supply visual evidence of a title-weight change. The mistakenly
named `files-sc-title500-2x` browser capture is excluded from this review.

The later `files-sc-awake-current-2x` capture supersedes that unresolved title
conclusion. Root reports sending the KDEPlatformTheme `refreshFonts` signal,
then reconfiguring KWin and waking the desktop before capture. On inspection,
the title is visibly narrower and lighter, and the Chinese portion is less
dominant beside the Latin. The unresized title region `(1700, 166)` to
`(2240, 210)` differs from the original in 5,480 of 23,760 pixels, confirming
that the rendered output now changed. The title stays readable and uncut.

There is a separate sharpness caveat in this latest image: the title's stroke
edges are visibly more stair-stepped than the earlier smooth 2× title and the
current list text. The decoration's colored dots also show coarser edges.
That screenshot supports a weight improvement, but not a title-raster clarity
improvement; the reason for the decoration-specific edge quality is not
established by that image. Intermediate font-cache/current captures reported
dimmed by idle are excluded. The earlier
1× and preview captures still document their shown reading states, but do not
validate the result of this later platform-font refresh at 1×.

The subsequent `files-sc-reboot-2x` native 3840×2160 capture is now the final
title evidence. It was inspected after root reported an actual guest restart
with the 500 title configuration. The title retains the lighter, narrower
appearance, while its contours and the colored window dots are smooth again.
The obvious decoration-only stair-stepping seen in the live-refresh capture
is absent. Chinese and Latin title text remain distinct and readable without
clipping; the Chinese portion has less excessive emphasis than the original
600-era title. This distinguishes the observed temporary live-refresh/scale
raster issue from the fresh 2× result. It does not establish the underlying
cache mechanism or guarantee every future live scale transition. The native
current-location breadcrumb is still much darker than its neighboring label.

Mail has a clear hierarchy between regular folder/subject labels, emphasized
senders, muted dates, and larger reading text. The Chinese message body has
open counters, clear punctuation, and comfortable line separation. The
Traditional Chinese list subject is also readable. A long sender address is
ellipsized without intruding into the date column. No text overlap or clipped
body lines is visible. This confirms these shown states, not all message
formats or Traditional Chinese prose.

The browser address text remains centered vertically and clear. The shown
Chinese article has distinct heading, secondary text, and body levels; mixed
Latin/numbers and Chinese punctuation remain readable. The authored page's
larger typography is separate from the 13 px browser chrome, so it should not
be treated as evidence that the chrome has identical macOS proportions.

Photos' ordinary sidebar labels and footer controls remain readable at 2×.
The long `2.0 GiB 内置驱动器 (vda2…)` sidebar label is hard-clipped by the pane
boundary. That is a real layout polish defect; changing font rasterization is
not its remedy. A smaller breadcrumb weight and a more graceful treatment of
long sidebar labels would improve this shown framework.

The two earlier 1× Files captures show readable Latin UI text and no missing
Chinese glyphs. Complex Chinese filenames remain visibly denser and coarser
than adjacent Latin at this size, particularly `瀑布横幅` and `繁體中文`.
The palette correction does not remove that density difference. Therefore,
the clean 2× result must not be generalized into equivalent 1× sharpness or an
exact match to the macOS references.

The final Chinese Files 1× capture also preserves the complete visible
filenames, column labels, tabs, and status text. Dense Chinese character
structures remain more compact than the adjacent Latin. The accepted 2× list
uses a tighter row rhythm than the earlier `files-sc-final-2x` capture, without
visible row collisions or text cropping in the displayed twelve entries.

The final 1× text preview contains continuous Chinese prose, mixed Latin file
names, numerals, currency, dense characters, punctuation, and a color emoji
sample. All displayed lines are readable, line spacing separates adjacent
strokes, and text stays clear of the footer and Open button. No missing-glyph
box, horizontal clipping, or baseline collision is visible. The title remains
more heavily weighted in Chinese than its Latin suffix. This expands the
observed 1× reading evidence, but does not establish Traditional Chinese prose
or a macOS rendering match.

No blocking missing-glyph, overlapping-line, or unreadable-control defect is
visible in these captures. The remaining heavy breadcrumb, 1× Chinese density,
and Photos sidebar clipping are concrete outstanding differences. The coarse
title edges observed during live refresh cleared in the fresh 2× boot, so they
are retained as a transition caveat rather than a defect in that final capture.
Root reports
the active guest font audit passed 59/59; that verifies resolution separately
and does not replace the visual observations above. The source references lack
equivalent Chinese UI, the final set does not contain a complete Traditional
Chinese prose comparison, and no matched current stock set was supplied for
this review. Quality scores and overall acceptance remain unassigned here.
