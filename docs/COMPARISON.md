# Native before / after comparison

This index points to the current **round 4** booted prototype. The independent
final review passes: **8.33 overall / 8.5 Chinese**, with three-second refinement
judged **yes**. Each link opens an original, unmodified guest
framebuffer. Open images at their native size to inspect text.

| Experience | Stock Fedora Kinoite | Aven |
| --- | --- | --- |
| Desktop | [Before](../evidence/stock/round-00/desktop-stable-1x.png) | [After](../evidence/aven/round-04/desktop-1x.png) |
| Files: Home | [Before](../evidence/stock/round-00/files-home-clean-1x.png) | [After](../evidence/aven/round-04/files-home-final-1x.png) |
| Files: mixed folder | [Before](../evidence/stock/round-00/files-mixed-clean-1x.png) | [After](../evidence/aven/round-04/files-mixed-1x.png) |
| Files: details | [Before](../evidence/stock/round-00/files-list-1x.png) | [After](../evidence/aven/round-04/files-list-1x.png) |
| Preview: image | [Before](../evidence/stock/round-00/preview-image-1x.png) | [After](../evidence/aven/round-04/preview-image-1x.png) |
| Preview: PDF | [Before](../evidence/stock/round-00/preview-pdf-1x.png) | [After](../evidence/aven/round-04/preview-pdf-1x.png) |
| Preview: Chinese text | [Before](../evidence/stock/round-00/preview-text-1x.png) | [After](../evidence/aven/round-04/preview-text-1x.png) |
| Preview: media | [Before](../evidence/stock/round-00/preview-media-1x.png) | [After](../evidence/aven/round-04/preview-media-1x.png) |
| Browser: Simplified Chinese | [Before](../evidence/stock/round-00/browser-sc-1x.png) | [After](../evidence/aven/round-04/browser-sc-1x.png) |
| Browser: Traditional Chinese | [Before](../evidence/stock/round-00/browser-tc-1x.png) | [After](../evidence/aven/round-04/browser-tc-1x.png) |
| Browser: real HTTPS site | [Before](../evidence/stock/round-00/browser-web-1x.png) | [After](../evidence/aven/round-04/browser-web-1x.png) |
| Mail: Inbox | [Before](../evidence/stock/round-00/mail-list-1x.png) | [After](../evidence/aven/round-04/mail-list-1x.png) |
| Mail: Simplified Chinese | [Before](../evidence/stock/round-00/mail-sc-1x.png) | [After](../evidence/aven/round-04/mail-sc-1x.png) |
| Mail: Traditional Chinese | [Before](../evidence/stock/round-00/mail-tc-1x.png) | [After](../evidence/aven/round-04/mail-tc-1x.png) |
| Mail: compose | [Before](../evidence/stock/round-00/mail-compose-1x.png) | [After](../evidence/aven/round-04/mail-compose-1x.png) |
| Photos: album | [Before](../evidence/stock/round-00/photos-grid-1x.png) | [After](../evidence/aven/round-04/photos-grid-1x.png) |
| Photos: landscape | [Before](../evidence/stock/round-00/photos-view-1x.png) | [After](../evidence/aven/round-04/photos-view-1x.png) |
| Photos: EXIF orientation | [Before](../evidence/stock/round-00/photo-exif-1x.png) | [After](../evidence/aven/round-04/photo-exif-1x.png) |
| Photos: transparency | [Before](../evidence/stock/round-00/photo-alpha-1x.png) | [After](../evidence/aven/round-04/photo-alpha-1x.png) |

The [final independent critic report](critic-round-04.md) explains the visible
gains and remaining rough edges. The [integrator's strict gate result](../evidence/verification/round04-final-gate.json)
reports zero errors. The 27 warnings preserve original stock integer-scale
probes; their evidence was not rewritten. [Earlier round 3](critic-round-03.md)
remains available as historical review.

## Supplemental matched details

| Detail | Stock | Aven |
| --- | --- | --- |
| Chinese compose at 720px window width | [Before](../evidence/stock/round-00/mail-compose-wrapped-720-1x.png) | [After](../evidence/aven/round-04/op-mail-compose-wrapped-720-1x.png) |
| Transparency at native 800% image zoom | [Before](../evidence/stock/round-00/photo-alpha-zoom-1x.png) | [After](../evidence/aven/round-04/photo-alpha-zoom-1x.png) |

The [paused video preview](../evidence/aven/round-04/preview-media-poster-1x.png)
shows the decoded poster and duration before playback. The
[native operation report](../evidence/interaction/aven-round04-native-verification.json)
records all 17 successful operations and six motion sequences.

The [current paired Chinese matrix](typography-round04-findings.md) covers
16 current Aven and 16 stock native SC/TC interface and paragraph captures at
100%, 125%, 150% and 200%. All actual-scale checks pass. The
[historical matrix review](matrix-review.md) remains available separately.

[Current status](STATUS.json) · [Build and runtime](BUILD.md) · [Restore](restore.md)
