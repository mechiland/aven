# Aven Union website

A bilingual static website: Simplified Chinese at `/` and `/zh-cn/`, English
at `/en/`. It remains in the owner's existing Cloudflare account and uses the
native Wrangler project; no hosting migration is involved.

Live: https://aven-website.mechiland.workers.dev

## Work locally

```sh
cd website
npm ci
npm run dev
```

Wrangler serves the local preview. Run `npm run build` after changing content
or assets, then reload the page.

```sh
npm run build
npm run check
npm run deploy
```

`wrangler.jsonc` deploys only `dist/` to the existing `aven-website` Worker.
Credentials, VM disks, source archives and OS configuration are excluded.

## Release information

`public/release.json` is the single source for the ISO download URL, filename,
version, byte count and SHA-256. The download button stays disabled while its
status is `pending`. Set `status` to `published` only after upload and download
verification; published metadata must contain an HTTPS URL, a complete SHA-256
and a positive integer byte count. The build fails on incomplete published
metadata. The page exposes the exact size and checksum next to the single-file
ISO link. No multipart reconstruction is required.

`public/updates.json` records the separately verified 0.4.0 online installer,
its direct GitHub download, SHA-256, byte count and update channel. `src/updates.mjs`
validates that metadata and contains the bilingual installation, update and
recovery copy. The 0.3.1 ISO remains a separate release; it has not been rebuilt
with the latest panel. Routine updates retain the user's layout; adopting new
layout defaults requires the explicit `--reset-defaults` option.

The ISO is stored in Cloudflare R2. Its public read-only download Worker and
release verification are managed separately from this static website. Update
the release-notes link in `src/content.mjs` if the release tag changes.

## Content and assets

- `src/content.mjs`: Chinese/English copy and per-scene screenshot provenance.
- `src/page.mjs`: shared semantic HTML, metadata, sections and image dialog.
- `public/app.js`: accessible tabs, comparison slider, mobile menu and lightbox.
- `public/styles.css`: responsive styles and Chinese 500 Medium emphasis.
- `assets-manifest.json`: original screenshot paths and SHA-256 hashes; also published.
- `public/credits.txt`: image sources, attribution and font licensing.

All 13 screenshots are exact copies of native PNG captures. The hero and Files
use round-08 Chinese/Latin filenames with the full-width bottom panel; the panel
section uses round-08's desktop capture. Mail and Photos remain round 07, while
Browser, Preview and typography remain round 06. The older captures show floating
Docks and are labeled accordingly. Stock comparisons remain round 00. All five
comparison pairs are 1920 × 1200; the separate online installation proof is an
unmodified 1440 × 900 capture from `evidence/verification/online-updates/`.

Each asset has its original path, hash and native dimensions in the manifest.
Capture rounds, online update verification and ISO fresh-install validation are
kept distinct. Union remains experimental with Plasma 6.8 Beta. Its overall and
Chinese visual scores and three-second differentiation judgment remain pending.
Historical Breeze scores are not reused. The live type specimen is website text,
not a desktop screenshot.

The bundled Noto Sans CJK SC subsets retain original outlines and metrics,
with renamed subset families and the full SIL Open Font License. Regenerate
after changing Chinese copy using `scripts/subset-fonts.py` with fontTools,
brotli and Debian's fonts-noto-cjk installed. Generated WOFF2 assets are tracked;
normal builds do not require Python. Website headings use genuine Medium 500
for Chinese; regular copy remains 400.

## Validation

`npm run check` validates routes, local references, ARIA targets, bilingual
navigation, five comparison pairs, exact screenshot hashes and pixel dimensions,
ISO and online installer metadata, update instructions, screenshot provenance, stale multipart instructions and JavaScript syntax.
These checks are separate from real browser inspection and OS visual review.
`deployment.json` describes the last recorded deployment; rebuilding locally
does not update or republish that record.
