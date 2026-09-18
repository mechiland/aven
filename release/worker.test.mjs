import test from 'node:test';
import assert from 'node:assert/strict';
import implementation from './worker.mjs';
const url = 'https://download.invalid/releases/v0.3.1/Aven.iso';
const uploaded = new Date('2026-09-17T07:00:00.500Z');
function fixture() {
  return {size: 10, etag: 'test', httpEtag: '"test"', uploaded,
    customMetadata: {sha256: 'a'.repeat(64)},
    writeHttpMetadata(headers) {headers.set('Content-Type', 'application/x-iso9660-image');}};
}
function environment(extra = {}) {
  return {PUBLISHED_PREFIX: 'releases/v0.3.1/', RELEASES: {
    head: async () => fixture(),
    get: async (_, options) => {
      assert.deepEqual(options.onlyIf, {etagMatches: 'test'});
      const {offset = 0, length = 10} = options.range || {};
      return {...fixture(), body: '0123456789'.slice(offset, offset + length)};
    }
  }, ...extra};
}
const fetch = (headers = {}, method = 'GET', env = environment()) =>
  implementation.fetch(new Request(url, {headers, method}), env);
test('refuses writes and non-release paths', async () => {
  assert.equal((await fetch({}, 'PUT', {})).status, 405);
  assert.equal((await implementation.fetch(new Request('https://download.invalid/private'), {})).status, 404);
});
test('missing object returns 404', async () => {
  assert.equal((await fetch({}, 'GET', environment({RELEASES: {head: async () => null}}))).status, 404);
});
test('candidates remain unavailable until publication', async () => {
  assert.equal((await fetch({}, 'GET', {PUBLISHED_PREFIX: ''})).status, 404);
});
test('full stream exposes identity and exact size', async () => {
  const r = await fetch();
  assert.equal(r.status, 200); assert.equal(r.headers.get('Content-Length'), '10');
  assert.equal(r.headers.get('X-Checksum-SHA256'), 'a'.repeat(64));
  assert.equal(await r.text(), '0123456789');
});
for (const [range, expected, contentRange] of [
  ['bytes=4-7', '4567', 'bytes 4-7/10'],
  ['bytes=7-', '789', 'bytes 7-9/10'],
  ['bytes=-3', '789', 'bytes 7-9/10'],
  ['bytes=7-99', '789', 'bytes 7-9/10'],
  ['bytes=-99', '0123456789', 'bytes 0-9/10']
]) test('serves ' + range, async () => {
  const r = await fetch({Range: range});
  assert.equal(r.status, 206); assert.equal(r.headers.get('Content-Range'), contentRange);
  assert.equal(r.headers.get('Content-Length'), String(expected.length));
  assert.equal(await r.text(), expected);
});
test('HEAD reads metadata only and ignores Range', async () => {
  const r = await fetch({Range: 'bytes=4-7'}, 'HEAD', environment({RELEASES: {head: async () => fixture()}}));
  assert.equal(r.status, 200); assert.equal(r.headers.get('Content-Length'), '10');
  assert.equal(await r.text(), '');
});
for (const method of ['GET', 'HEAD']) test(method + ' evaluates conditional requests in protocol order', async () => {
  assert.equal((await fetch({'If-None-Match': 'W/"test"'}, method)).status, 304);
  assert.equal((await fetch({'If-Modified-Since': 'Thu, 17 Sep 2026 07:00:00 GMT'}, method)).status, 304);
  assert.equal((await fetch({'If-Match': '"stale"', 'If-None-Match': '"test"'}, method)).status, 412);
  assert.equal((await fetch({'If-Unmodified-Since': 'Wed, 16 Sep 2026 07:00:00 GMT'}, method)).status, 412);
  assert.equal((await fetch({'If-None-Match': '"other"', 'If-Modified-Since': 'Fri, 18 Sep 2026 07:00:00 GMT'}, method)).status, 200);
});
test('If-Range permits only matching strong tags or current dates', async () => {
  for (const value of ['"stale"', '"2030"', 'W/"test"', 'Wed, 16 Sep 2026 07:00:00 GMT', 'Fri, 18 Sep 2026 07:00:00 GMT']) {
    const r = await fetch({Range: 'bytes=4-7', 'If-Range': value});
    assert.equal(r.status, 200); assert.equal(await r.text(), '0123456789');
  }
  for (const value of ['"test"', 'Thu, 17 Sep 2026 07:00:00 GMT'])
    assert.equal((await fetch({Range: 'bytes=4-7', 'If-Range': value})).status, 206);
});
test('unsatisfiable ranges return 416 with the full size', async () => {
  for (const value of ['bytes=10-', 'bytes=8-3', 'bytes=-0']) {
    const r = await fetch({Range: value});
    assert.equal(r.status, 416); assert.equal(r.headers.get('Content-Range'), 'bytes */10');
  }
});
test('unsupported and multiple ranges are ignored', async () => {
  for (const value of ['items=1-2', 'bytes=0-2,5-7', 'bytes=-'])
    assert.equal((await fetch({Range: value})).status, 200);
});
