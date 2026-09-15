# ISO candidate 5 — independent visual review

**Pass for the installed ISO at 1×: 8.27 overall, Chinese typography 8.5.** Aven is unmistakably different and more refined than stock in the three-second comparison. No blocking visual defect was observed in this scope. Files density and photo-viewer sizing are less consistent than the accepted prototype and reduce the scores below round04’s 8.33.

This is a fresh judgment of the installed candidate, based on **47 original candidate5 PNGs** and **18 comparison groups with 18 stock and 18 accepted-round04 originals**. Every used image was opened at original resolution, including genuine Simplified Chinese and Traditional Chinese interfaces and paragraphs. The critic performed no guest input, source changes or screenshot editing. Exact hashes, per-frame observations, comparisons and limitations are in the [manifest](../evidence/critic/iso-candidate5.json).

ISO SHA256: `ae91559362ecfb87fa4f630882a78c41f699540d0ffda25ccea66c7be00e34e0`. Embedded source commit: `9500b72a79320ce062a8b7360eac5806b142c93a`. Identity is provenance; it does not substitute for the new screenshots.

## Scores

These scores cover current 1× visual quality and observed operation results. They do not imply a candidate5 fractional-scale or motion rerun.

| Category | Score | Evidence and judgment |
|---|---:|---|
| Chinese typography | **8.5** | SC/TC Files, preview, Firefox and mail retain readable weight, mixed-script baselines and punctuation. Mail reading and writing have comfortable inset and roughly 30px leading, including wrapped and reopened text. The current breadcrumb remains too heavy. |
| Latin typography | 8.4 | Native labels, filenames, addresses and mixed runs have a coherent readable scale. Narrow sender cards still truncate text. |
| Files experience | 8.2 | Automatically focused Places and the large four-by-three mixed-file grid remain substantially clearer than stock. Initial Everyday details density differs from its later state. |
| File preview | 8.6 | Large Earthrise preview, readable SC/TC text, width-fit PDF and correct media poster/duration preserve the strongest improvement. Three native viewer handoff results were inspected. |
| Browser coherence | 8.4 | Neutral Firefox chrome fits the shared decoration. Actual Chinese HTTPS content, download and native picker work within that surface. The extra titlebar costs content height. |
| Mail coherence | 8.1 | Quiet surfaces and comfortable Chinese reading/composition survive the ISO install. Narrow cards and a mostly empty upper strip remain less resolved. |
| Photo experience | **7.8** | The large album grid is useful. A taller filmstrip after native resize reduces the exact river photo from accepted 79% fit to 73%; native beveled cells remain prominent. |
| Visual coherence | 8.3 | Jade/cream wallpaper, short light panel, shared chrome and readable UI scale establish one recognizable product across the focused apps. |
| Perceived polish | 8.1 | Preview and compose improvements survive. Initial Files density, photo sizing and native first-window geometry leave visible roughness. Current motion is unscored. |
| **Mean** | **8.2667** | Meets overall ≥8 and Chinese ≥8.5 for this scoped review. |

## Direct comparison findings

The exact stock/accepted/candidate mapping for all 18 groups is in the manifest. These links show the decisive originals.

### Desktop and Files

[Stock desktop](../evidence/stock/round-00/desktop-stable-1x.png), [accepted desktop](../evidence/aven/round-04/desktop-1x.png), [candidate first desktop](../evidence/verification/iso-candidate5/first-desktop.png) and [second desktop](../evidence/verification/iso-candidate5/second-desktop.png) show a clear change from blue relief and a nearly full-width dark panel to broad quiet jade curves and a shorter light panel. The Files and preview hierarchy makes this refinement more than a wallpaper change. The three-second answer is **yes**; this is a critic’s visual judgment, not a blinded user study.

[Stock details](../evidence/stock/round-00/files-list-1x.png), [accepted details](../evidence/aven/round-04/files-list-1x.png), [candidate initial details](../evidence/verification/iso-candidate5/files-sc-list-initial.png) and [candidate after grid](../evidence/verification/iso-candidate5/files-sc-list-after-grid.png) preserve the real density difference. Candidate5 initially has approximately **26px rows with small icons**, changing to **36px after visiting grid**. The initial state still has full-size, legible Chinese/Latin text, aligned metadata and no observed clipping. It is a nonblocking consistency defect. The later state must not be presented as the untouched default. Accepted **Home** itself also used compact rows; the regression concerns the Everyday primary comparison.

[Stock grid](../evidence/stock/round-00/files-mixed-clean-1x.png), [accepted grid](../evidence/aven/round-04/files-mixed-1x.png) and [candidate grid](../evidence/verification/iso-candidate5/files-sc-grid.png) show the same twelve files: Aven’s four-by-three large thumbnails are much more useful than stock’s nine-plus-three small items. The first-user sidebar is correctly focused; the prior root/boot-volume clutter is absent. A retained `fedora_fedora` label and heavy current breadcrumb remain technical-looking.

### Chinese, preview and mail

[Stock text preview](../evidence/stock/round-00/preview-text-1x.png), [accepted text preview](../evidence/aven/round-04/preview-text-1x.png) and [candidate SC preview](../evidence/verification/iso-candidate5/preview-text-sc.png) show the concrete gain from metadata to readable paragraphs. The [full TC preview](../evidence/verification/iso-candidate5/preview-text-tc.png) also contains real Traditional Chinese text and localized controls; it is supplemental because no exact stock/round04 TC text-preview counterpart exists. Dense characters, corner quotes, punctuation, Latin, paths, currency and emoji remain readable without observed missing glyphs or collisions.

[Stock Earthrise](../evidence/stock/round-00/preview-image-1x.png) versus [candidate Earthrise](../evidence/verification/iso-candidate5/preview-earthrise.png) shows the strongest immediate gain: roughly 160px information-panel image versus an approximately 832px focused image. The candidate’s separately captured waterfall is not substituted for this exact-content pair. PDF content is readable at width fit, but its embedded fonts do not establish system-font improvement. Paused and playing media frames visibly show correct `0:00 / 0:05` and advancing `0:02 / 0:05` states; they do not establish smoothness or audio.

[Stock TC mail](../evidence/stock/round-00/mail-tc-1x.png), [accepted TC mail](../evidence/aven/round-04/mail-tc-1x.png) and [candidate TC mail](../evidence/verification/iso-candidate5/mail-tc.png) retain the clearer inset and roughly 30px reading rhythm against stock’s tighter 24px. The same improvement survives [candidate wrapped composition](../evidence/verification/iso-candidate5/mail-compose-wrapped.png), compared with [stock at 720px](../evidence/stock/round-00/mail-compose-wrapped-720-1x.png) and [accepted at 720px](../evidence/aven/round-04/op-mail-compose-wrapped-720-1x.png). Shared reply paragraphs match; candidate5’s operation-added sentence differs from the historical addition, so complete message identity is not claimed. The saved Chinese addition remains visible after reopening.

The Chinese score reflects reading comfort and coherent UI scale. Stock already has clean authored Firefox prose; these screenshots do **not** demonstrate dramatic font-rasterization gains or literal macOS equivalence.

### Browser and photos

[Stock HTTPS page](../evidence/stock/round-00/browser-web-1x.png), [accepted page](../evidence/aven/round-04/browser-web-1x.png) and [candidate HTTPS page](../evidence/verification/iso-candidate5/browser-https.png) show the same official Firefox Chinese hero. Candidate5 retains neutral coherent chrome around the site’s own purple/orange identity. The [initial capture](../evidence/verification/iso-candidate5/browser-https-initial.png) preserves native translation and restore-session notices; these were dismissed for the comparison. The navigation record attributes actual HTTPS redirect without certificate override to the operator. This is ordinary rendered browsing evidence, not a TLS audit. SC and TC City Notes pairs were also inspected; their authored paragraph spacing is not credited as an Aven change.

[Stock album](../evidence/stock/round-00/photos-grid-1x.png), [accepted album](../evidence/aven/round-04/photos-grid-1x.png) and [candidate album](../evidence/verification/iso-candidate5/photos-grid.png) show the same eight photos. The approximately 240px five-plus-three grid remains a clear gain. However, [stock river](../evidence/stock/round-00/photos-view-1x.png), [accepted river](../evidence/aven/round-04/photos-view-1x.png) and [candidate exact river](../evidence/verification/iso-candidate5/photos-river-exact.png) confirm a real viewing regression: the candidate’s roughly **118px filmstrip**, against accepted **66px**, reduces fit from **79% to 73%**. Stock fits at 92% with its strip hidden. The candidate image remains intact and uncropped; the smaller main-photo area warrants the photo/polish deduction. No configuration repair was applied to conceal the native resize result.

## Verification and limits

The critic inspected native operation endpoints and read the [independent smoke review](../evidence/verification/iso-candidate5/native-smoke-review.json), [three-handoff review](../evidence/verification/iso-candidate5/preview-handoff-review.json) and [second-boot persistence review](../evidence/verification/iso-candidate5/second-boot/persistence-review.json). Input was operated by the integrator; verification independently checked original screenshots and persisted bytes. Copy, rename/move/trash, download, picker return, local draft edit/save/reopen, photo navigation/fullscreen and preview handoffs have corroborated results. The second boot retains the visual defaults and checked runtime/font state.

The [accepted round04 review](critic-round-04.md), its 16-pair four-scale SC/TC matrix and six sampled paired-motion sequences remain historical evidence. **Candidate5’s full fractional-scale and motion rerun stays null.** Current stills do not establish physical frame pacing, calibrated display rendering or audio. Live mail send/receive, candidate5 Trash restore and repeated alpha/EXIF6 checks are not claimed. First-run notices and window-placement differences are retained in the evidence.

**Recommendation:** accept this installed-ISO 1× visual regression review with the two documented nonblocking polish issues. The critic does not set ISO boot/install or release acceptance; those remain the integrator’s separate decision.
