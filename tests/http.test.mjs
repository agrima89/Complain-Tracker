import { test } from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';

process.env.DATABASE_PATH = path.join(os.tmpdir(), `cc_test_${process.pid}_${Date.now()}.db`);
process.env.ADMIN_PASSWORD = 'test-only-admin-password-123';
delete process.env.DATABASE_URL;
delete process.env.NETLIFY_DB_URL;
delete process.env.NETLIFY_DATABASE_URL;

const { initDb } = await import('../netlify/functions/utils/db.mjs');
const { json, parseJsonBody, clientIp, rateLimit } = await import('../netlify/functions/utils/http.mjs');

test('json() adds security headers', () => {
  const r = json(201, { a: 1 });
  assert.equal(r.statusCode, 201);
  assert.equal(r.headers['X-Content-Type-Options'], 'nosniff');
  assert.deepEqual(JSON.parse(r.body), { a: 1 });
});

test('parseJsonBody rejects invalid and non-object bodies', () => {
  assert.equal(parseJsonBody({ body: '{bad' }), null);
  assert.equal(parseJsonBody({ body: '[1]' }), null);
  assert.deepEqual(parseJsonBody({ body: '{"x":1}' }), { x: 1 });
  assert.deepEqual(parseJsonBody({}), {});
});

test('clientIp uses first forwarded address', () => {
  assert.equal(clientIp({ headers: { 'x-forwarded-for': '1.2.3.4, 5.6.7.8' } }), '1.2.3.4');
  assert.equal(clientIp({}), 'unknown');
});

test('rateLimit blocks after the limit within a window', async () => {
  await initDb();
  const event = { headers: { 'x-forwarded-for': '9.9.9.9' } };
  const cfg = { limit: 3, windowSec: 3600 };
  for (let i = 0; i < 3; i++) assert.equal(await rateLimit(event, 'unit', cfg), null);
  const blocked = await rateLimit(event, 'unit', cfg);
  assert.equal(blocked.statusCode, 429);
  assert.ok(Number(blocked.headers['Retry-After']) > 0);
  // a different identity is unaffected
  assert.equal(await rateLimit(event, 'unit', cfg, 'student:42'), null);
});
