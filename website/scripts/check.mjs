import assert from 'node:assert/strict';
import { readFile, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';
import { execFileSync } from 'node:child_process';
import { scenes } from '../src/content.mjs';
import { iso, downloadReady } from '../src/release.mjs';
import { update } from '../src/updates.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const dist = join(root, 'dist');
const pages = ['index.html', 'zh-cn/index.html', 'en/index.html', '404.html'];
let checked = 0;
for (const page of pages) {
  const html = await readFile(join(dist, page), 'utf8');
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
  assert.equal(ids.length, new Set(ids).size, `${page}: duplicate ID`);
  assert.match(html, /<html lang="(?:zh-CN|en)">/);
  assert.match(html, /name="viewport"/);
  for (const [, ref] of html.matchAll(/\b(?:href|src)="([^"]+)"/g)) {
    if (/^(https?:|data:|mailto:)/.test(ref)) continue;
    if (ref.startsWith('#')) { assert(ids.includes(ref.slice(1)), `${page}: missing ${ref}`); continue; }
    const localRef = ref.split('?')[0];
    const path = join(dist, localRef.endsWith('/') ? localRef + 'index.html' : localRef);
    assert((await stat(path)).isFile(), `${page}: missing asset ${ref}`);
    checked++;
  }
  for (const [, id] of html.matchAll(/aria-(?:controls|labelledby)="([^"]+)"/g)) {
    assert(ids.includes(id), `${page}: invalid ARIA target ${id}`);
  }
  if (page !== '404.html') {
    assert.equal([...html.matchAll(/<h1\b/g)].length, 1);
    assert.equal([...html.matchAll(/role="tabpanel"/g)].length, 5);
    assert.equal([...html.matchAll(/data-compare="/g)].length, 5);
    const sceneData = JSON.parse(html.match(/id="scene-data">([^<]+)</)[1]);
    assert.equal(sceneData.ids.length, 5);
    assert.equal(sceneData.details.length, 5);
    assert.match(html, /href="\/en\/"/);
    assert.match(html, /href="\/zh-cn\/"/);
    for (const [, image] of html.matchAll(/<img\b([^>]+)>/g)) assert.match(image, /alt="[^"]*"/);
    assert(!/0\.1\.0|reassemble-iso|ISO-PARTS/.test(html), `${page}: stale release instructions`);
    assert(html.includes(`href="${update.url}"`), `${page}: missing online installer`);
    assert(html.includes(update.sha256), `${page}: missing installer checksum`);
    for (const command of ['python3 aven-installer/aven.py install', '~/.local/bin/aven update', 'aven check', 'aven update --download-only', 'aven status', 'aven recover', 'aven rollback', 'aven update --reset-defaults']) {
      assert(html.includes(command), `${page}: missing update instruction ${command}`);
    }
    if (downloadReady) {
      assert(html.includes(`href="${iso.url}"`), `${page}: missing direct ISO link`);
      assert(html.includes(iso.sha256), `${page}: missing checksum`);
      assert(html.includes(iso.filename), `${page}: missing ISO filename`);
    } else {
      assert(!/href="[^"]+\.iso"/.test(html), `${page}: unpublished ISO link`);
      assert.match(html, /class="button button-pending" aria-disabled="true"/);
    }
  }
}
const assets = JSON.parse(await readFile(join(root, 'assets-manifest.json'), 'utf8'));
for (const entry of assets) {
  const bytes = await readFile(join(dist, 'assets', entry.asset));
  const hash = createHash('sha256').update(bytes).digest('hex');
  assert.equal(hash, entry.sha256, `Changed screenshot: ${entry.asset}`);
  const original = await readFile(join(dirname(root.slice(0, -1)), entry.source));
  assert(bytes.equals(original), `Original mismatch: ${entry.asset}`);
  if (entry.asset.endsWith('.png')) {
    assert.equal(bytes.readUInt32BE(16), entry.width);
    assert.equal(bytes.readUInt32BE(20), entry.height);
  }
}
for (const s of scenes) for (const source of ['aven', 'stock']) {
  const entry = assets.find(e => e.asset === `${source}-${s.id}.png`);
  assert.equal(entry.source, s[source], `${s.id}: screenshot provenance mismatch`);
  assert.equal(entry.width, 1920, `${s.id}: comparison width differs`);
  assert.equal(entry.height, 1200, `${s.id}: comparison height differs`);
}
assert.deepEqual(JSON.parse(await readFile(join(dist, 'release.json'), 'utf8')), iso);
assert.deepEqual(JSON.parse(await readFile(join(dist, 'updates.json'), 'utf8')), update);
const css = await readFile(join(dist, 'styles.css'), 'utf8');
for (const [, ref] of css.matchAll(/url\("([^"]+)"\)/g)) await stat(join(dist, ref.split('?')[0]));
assert.match(css, /prefers-reduced-motion/);
execFileSync(process.execPath, ['--check', join(dist, 'app.js')]);
console.log(`PASS: 4 pages, ${checked} local references, ARIA targets, bilingual navigation, online installer and ISO metadata, update instructions, 5 comparison pairs, ${assets.filter(e => e.asset.endsWith('.png')).length} pixel-identical screenshots, JavaScript syntax.`);
