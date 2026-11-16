/**
 * Runs a classic Lambda-style handler (event -> { statusCode, headers, body }) as a modern
 * Netlify Function (Request -> Response). Modern functions receive platform settings such as the
 * Netlify Database connection, which classic handlers don't.
 */
const TEXT_TYPES = /^(application\/(json|x-www-form-urlencoded)|text\/)/i;

export function toV2(handler) {
  return async (req, context) => {
    const url = new URL(req.url);
    const headers = Object.fromEntries(req.headers);
    let body = null;
    let isBase64Encoded = false;
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      const buf = Buffer.from(await req.arrayBuffer());
      if (TEXT_TYPES.test(headers['content-type'] || '')) body = buf.toString('utf8');
      else { body = buf.toString('base64'); isBase64Encoded = true; }
    }
    // Rewrites in netlify.toml (e.g. /complaints/:id/evidence -> evidence-get?complaint_id=:id) don't
    // pass their query string to modern functions, so recover those parameters from the original path.
    const query = Object.fromEntries(url.searchParams);
    let m;
    if ((m = url.pathname.match(/^\/complaints\/(\d+)\/evidence\/?$/))) query.complaint_id ??= m[1];
    else if ((m = url.pathname.match(/^\/(?:student|admin)\/complaint\/(\d+)\/(?:download-pdf|pdf)\/?$/))) query.id ??= m[1];
    else if (/^\/admin\/report\/(?:download-pdf|pdf)\/?$/.test(url.pathname)) query.report ??= 'summary';

    const event = {
      httpMethod: req.method,
      headers,
      queryStringParameters: query,
      path: url.pathname,
      rawUrl: req.url,
      body,
      isBase64Encoded
    };

    const res = (await handler(event, context)) || {};
    const out = new Headers();
    for (const [k, v] of Object.entries(res.headers || {})) out.set(k, String(v));
    for (const [k, vals] of Object.entries(res.multiValueHeaders || {})) for (const v of vals) out.append(k, String(v));
    const payload = res.body == null ? null : (res.isBase64Encoded ? Buffer.from(res.body, 'base64') : res.body);
    return new Response(payload, { status: res.statusCode || 200, headers: out });
  };
}
