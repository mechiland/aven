// Public, read-only release downloads. Upload credentials are never deployed here.
function etagMatches(value, etag, weak = false) {
  return value.split(',').some(item => {
    const tag = item.trim();
    return tag === '*' || (weak ? tag.replace(/^W\//, '') === etag : tag === etag);
  });
}
function modifiedSeconds(object) {
  return Math.floor(object.uploaded.getTime() / 1000) * 1000;
}
function precondition(headers, object) {
  const match = headers.get('If-Match'), none = headers.get('If-None-Match');
  const unmodified = Date.parse(headers.get('If-Unmodified-Since'));
  const modified = Date.parse(headers.get('If-Modified-Since'));
  if (match !== null) {
    if (!etagMatches(match, object.httpEtag)) return 412;
  } else if (Number.isFinite(unmodified) && modifiedSeconds(object) > unmodified) return 412;
  if (none !== null) {
    if (etagMatches(none, object.httpEtag, true)) return 304;
  } else if (Number.isFinite(modified) && modifiedSeconds(object) <= modified) return 304;
  return null;
}
function byteRange(value, size) {
  // Multiple or malformed ranges are ignored; a valid but unsatisfiable range is 416.
  const match = /^bytes=(\d*)-(\d*)$/.exec(value || '');
  if (!match || (!match[1] && !match[2])) return null;
  let start, end;
  if (!match[1]) {
    const suffix = Number(match[2]);
    if (suffix === 0 || size === 0) return false;
    start = Math.max(0, size - suffix); end = size - 1;
  } else {
    start = Number(match[1]); end = match[2] ? Number(match[2]) : size - 1;
    if (start >= size || start > end) return false;
    end = Math.min(end, size - 1);
  }
  return {offset: start, length: end - start + 1};
}
export default {
  async fetch(request, env) {
    if (!['GET', 'HEAD'].includes(request.method)) {
      return new Response('Method not allowed', {status: 405, headers: {Allow: 'GET, HEAD'}});
    }
    let key;
    try { key = decodeURIComponent(new URL(request.url).pathname.slice(1)); }
    catch { return new Response('Invalid path', {status: 400}); }
    if (!/^releases\/v[0-9][0-9A-Za-z.-]*\/[A-Za-z0-9._-]+$/.test(key) ||
        !env.PUBLISHED_PREFIX || !key.startsWith(env.PUBLISHED_PREFIX)) {
      return new Response('Not found', {status: 404});
    }
    const object = await env.RELEASES.head(key);
    if (!object) return new Response('Not found', {status: 404});
    const headers = new Headers();
    object.writeHttpMetadata(headers);
    headers.set('ETag', object.httpEtag);
    headers.set('Last-Modified', object.uploaded.toUTCString());
    headers.set('Accept-Ranges', 'bytes');
    headers.set('X-Content-Type-Options', 'nosniff');
    headers.set('Content-Disposition', `attachment; filename="${key.split('/').at(-1)}"`);
    headers.set('Cache-Control', 'public, max-age=31536000, immutable');
    if (object.customMetadata?.sha256) headers.set('X-Checksum-SHA256', object.customMetadata.sha256);
    const condition = precondition(request.headers, object);
    if (condition) return new Response(null, {status: condition, headers});
    if (request.method === 'HEAD') {
      headers.set('Content-Length', String(object.size));
      return new Response(null, {headers});
    }
    // R2 does not implement If-Range. Check it before passing a bounded range.
    const ifRange = request.headers.get('If-Range');
    const rangeAllowed = !ifRange || ifRange === object.httpEtag ||
      (!ifRange.startsWith('W/') && !ifRange.startsWith('"') && Number.isFinite(Date.parse(ifRange)) &&
       modifiedSeconds(object) === Date.parse(ifRange));
    const range = rangeAllowed ? byteRange(request.headers.get('Range'), object.size) : null;
    if (range === false) {
      headers.set('Content-Range', `bytes */${object.size}`);
      return new Response(null, {status: 416, headers});
    }
    const options = {onlyIf: {etagMatches: object.etag}};
    if (range) options.range = range;
    const result = await env.RELEASES.get(key, options);
    if (!result) return new Response('Not found', {status: 404});
    if (!('body' in result)) return new Response(null, {status: 412});
    if (range) {
      headers.set('Content-Range', `bytes ${range.offset}-${range.offset + range.length - 1}/${object.size}`);
      headers.set('Content-Length', String(range.length));
    } else headers.set('Content-Length', String(object.size));
    return new Response(result.body, {status: range ? 206 : 200, headers});
  }
};
