# R2 release downloads

`worker.mjs` is the read-only public download endpoint for Aven releases. The
dedicated `aven-releases` bucket stores immutable objects under
`releases/v<version>/`. `PUBLISHED_PREFIX` controls which tested release is public;
an empty value keeps every candidate unavailable. GET and HEAD stream R2 objects
with download filenames, byte-range support and SHA-256 metadata.

```sh
node --test release/worker.test.mjs
cd release
../website/node_modules/.bin/wrangler deploy
```

Use the authenticated Cloudflare account already configured for the website.
Do not place credentials in this directory. Large ISOs require R2 multipart
upload. Upload the ISO, checksum file and immutable build manifest; verify all
parts and the completed object before enabling the public prefix. The upload
endpoint and its credential are separate, temporary infrastructure and must be
removed after publication. The public Worker never accepts writes.

Fill `website/public/release.json` with the verified filename, version, URL,
SHA-256, byte count and publication time. Set its status to `published` only after
the public download is verified, then build and deploy the website. The website
disables the download button for an incomplete or pending manifest.

The current release's evidence and limitations live in
[the Union ISO report](../docs/UNION-ISO-0.3.1.md).
