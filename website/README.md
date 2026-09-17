# Aven website

A bilingual product website with Simplified Chinese at `/` and `/zh-cn/`, and
English at `/en/`. Built as static HTML, CSS and JavaScript. Hosted directly in
the owner's Cloudflare account with Wrangler, as requested.

Live: https://aven-website.mechiland.workers.dev

- Simplified Chinese: https://aven-website.mechiland.workers.dev/zh-cn/
- English: https://aven-website.mechiland.workers.dev/en/

## Work locally

```sh
cd website
npm ci
npm run dev
```

The local preview is served by Wrangler. Run `npm run build` after editing
content or assets; reload the preview to see the new build.

```sh
npm run build
npm run check
npm run deploy
```

`wrangler.jsonc` deploys only `dist/` to the `aven-website` Worker. No credentials,
VM data, source archives or OS configuration are included in the deployment.

## Content and assets

- `src/content.mjs`: both translations, release links and screenshot provenance.
- `src/page.mjs`: shared semantic HTML, metadata, product sections and dialog.
- `public/app.js`: application tabs, comparison slider, mobile menu and image viewer.
- `public/styles.css`: responsive styles, typography and reduced motion support.
- `assets-manifest.json`: source paths and SHA-256 hashes of the original images.
- `public/credits.txt`: image sources, attribution and font licensing.

All 11 screenshots are exact copies of native 1920 × 1200 PNG captures. Aven
captures come from the installed candidate5 ISO; stock captures come from
round-00. The page discloses differences in window layouts and interaction
states. The type specimen is live website text; the linked Chinese screenshot
is the original desktop capture. This site assigns no new product review scores.

The bundled Noto Sans CJK SC website subsets retain original glyph outlines and
metrics, with renamed subset families and the full font license. Regenerate
after changing Chinese copy using `scripts/subset-fonts.py` with fontTools,
brotli and Debian's fonts-noto-cjk installed. Generated WOFF2 assets are tracked;
ordinary builds do not need Python.

## Validation

`npm run check` validates bilingual routes, all local HTML references, ARIA
targets, five comparison pairs, image dimensions and screenshot identity against
both their source files and the recorded hashes. It also checks JavaScript
syntax. These checks do not constitute a visual quality score or a browser test.

The Aven OS, shared Plasma/KWin configuration and `docs/STATUS.json` are outside
this website's scope and are unchanged.
