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

All 11 screenshots are exact copies of native 1920 × 1200 PNG captures.
Union Mail and Photos use round-07 captures of the latest translucent Dock.
Files, Browser, Preview and the linked typography view use round-06 captures
with the earlier Dock. Stock captures remain from round-00. The page clearly
discloses capture rounds and differences in content, layout and interaction
state. These themed test-VM captures are separate from fresh-install evidence
for the downloadable ISO. They are not retouched or used to assign a new visual
review score. Union remains an experimental Plasma 6.8 Beta prototype, with its
visual score and three-second differentiation judgment pending. Historical Breeze
scores are not reused. The type specimen is live website text, not a desktop screenshot.

The bundled Noto Sans CJK SC subsets retain original outlines and metrics,
with renamed subset families and the full SIL Open Font License. Regenerate
after changing Chinese copy using `scripts/subset-fonts.py` with fontTools,
brotli and Debian's fonts-noto-cjk installed. Generated WOFF2 assets are tracked;
normal builds do not require Python. Website headings use genuine Medium 500
for Chinese; regular copy remains 400.

## Validation

`npm run check` validates routes, local references, ARIA targets, bilingual
navigation, five comparison pairs, exact screenshot hashes and pixel dimensions,
release metadata consistency, stale multipart instructions and JavaScript syntax.
These checks are separate from real browser inspection and OS visual review.
`deployment.json` describes the last recorded deployment; rebuilding locally
does not update or republish that record.
