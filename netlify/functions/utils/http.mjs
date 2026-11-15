/**
 * CampusCare - shared HTTP helpers for Netlify functions.
 * Consistent JSON responses, security headers, body parsing and DB-backed rate limiting.
 */
import { query } from './db.mjs';

export const SECURITY_HEADERS = {
  'Content-Type': 'application/json',
  'Cache-Control': 'no-store',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin'
};

export function json(statusCode, payload, extraHeaders = {}) {
  return { statusCode, headers: { ...SECURITY_HEADERS, ...extraHeaders }, body: JSON.stringify(payload) };
}

export function ok(data = {}, extraHeaders = {}) {
  return json(200, { success: true, ...data }, extraHeaders);
}

export function fail(statusCode, error, extra = {}) {
  return json(statusCode, { success: false, error, ...extra });
}

/** Returns a parsed object, or null when the body is not valid JSON. */
export function parseJsonBody(event) {
  try {
    const parsed = JSON.parse(event.body || '{}');
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function clientIp(event) {
  const h = event.headers || {};
  const fwd = h['x-nf-client-connection-ip'] || h['x-forwarded-for'] || h['client-ip'] || '';
  return String(fwd).split(',')[0].trim() || 'unknown';
}

/**
 * Fixed-window rate limiter stored in the database so it works across serverless instances.
 * Returns null when allowed, or a 429 response when the limit is exceeded.
 * Fails open on DB errors so a limiter outage never blocks legitimate users.
 */
export async function rateLimit(event, bucket, { limit, windowSec }, identity = '') {
  const key = `${bucket}:${identity || clientIp(event)}`;
  const now = Math.floor(Date.now() / 1000);
  const windowStart = now - (now % windowSec);
  try {
    const res = await query('SELECT window_start, hits FROM rate_limits WHERE rl_key = $1', [key]);
    const row = res.rows[0];
    if (!row || Number(row.window_start) !== windowStart) {
      if (row) {
        await query('UPDATE rate_limits SET window_start = $1, hits = 1 WHERE rl_key = $2', [windowStart, key]);
      } else {
        await query('INSERT INTO rate_limits (rl_key, window_start, hits) VALUES ($1, $2, 1)', [key, windowStart]);
      }
      return null;
    }
    if (Number(row.hits) >= limit) {
      const retryAfter = windowStart + windowSec - now;
      return json(429, { success: false, error: `Too many attempts. Please try again in ${Math.ceil(retryAfter / 60)} minute(s).` },
        { 'Retry-After': String(retryAfter) });
    }
    await query('UPDATE rate_limits SET hits = hits + 1 WHERE rl_key = $1', [key]);
    return null;
  } catch (e) {
    console.error('[RateLimit] failing open:', e.message);
    return null;
  }
}

// A whole campus usually shares one public IP (Wi-Fi NAT), so per-IP limits must be generous
// and the tight limits must be per account.
export const LIMITS = {
  login: { limit: 10, windowSec: 900 },          // per account (+ network): stops password guessing
  loginNetwork: { limit: 1000, windowSec: 900 }, // per network: stops spraying many accounts
  register: { limit: 300, windowSec: 3600 },     // per network: a busy campus can still sign up
  createComplaint: { limit: 10, windowSec: 3600 }
};

/** Login limits: tight per account, generous per network. */
export async function limitLogin(event, account) {
  const id = String(account || '').trim().toLowerCase() || 'anonymous';
  return (await rateLimit(event, 'login-net', LIMITS.loginNetwork))
    || (await rateLimit(event, 'login', LIMITS.login, `${clientIp(event)}|${id}`));
}
