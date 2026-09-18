import { readFileSync } from 'node:fs';

export const iso = JSON.parse(readFileSync(new URL('../public/release.json', import.meta.url), 'utf8'));
export const downloadReady = iso.status === 'published'
  && typeof iso.url === 'string' && /^https:\/\//.test(iso.url)
  && /^[a-f0-9]{64}$/.test(iso.sha256)
  && Number.isSafeInteger(iso.bytes) && iso.bytes > 0;

if (iso.status === 'published' && !downloadReady) {
  throw new Error('Published ISO requires an HTTPS URL, SHA-256 and positive integer byte size.');
}
