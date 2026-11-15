import { test } from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';

process.env.DATABASE_PATH = path.join(os.tmpdir(), `cc_match_${process.pid}_${Date.now()}.db`);
process.env.ADMIN_PASSWORD = 'test-only-admin-password-123';
delete process.env.DATABASE_URL;
delete process.env.NETLIFY_DB_URL;
delete process.env.NETLIFY_DATABASE_URL;

const { getCanonicalLocationKey, isSimilarIssue } = await import('../netlify/functions/utils/duplicate_logic.mjs');
const { detectRoomAndFloor } = await import('../netlify/functions/utils/smart_complaint.mjs');
const { initDb } = await import('../netlify/functions/utils/db.mjs');
const { limitLogin, LIMITS } = await import('../netlify/functions/utils/http.mjs');

test('same fault in different words at the same room is a match', () => {
  const place = (o) => getCanonicalLocationKey({ category: 'Electrical', ...o });
  assert.equal(place({ block: 'Block C', room_no: '204' }), place({ block: 'block-c', room_no: 'Room 204' }));
  assert.ok(isSimilarIssue('The tube light in room 204 is sparking', 'Sparks from the tube light fitting', '204'));
  assert.ok(!isSimilarIssue('Fan not working', 'Light flickering', '204'));
});

test('block-only reports have no exact place, so they are never fuzzy-merged', () => {
  assert.ok(getCanonicalLocationKey({ category: 'Cleaning', block: 'Block C', room_no: '' }).endsWith('::'));
});

test('room and floor are detected from the description', () => {
  assert.deepEqual(detectRoomAndFloor('Fan not working in lab 3 on the 2nd floor'), { room: '3', floor: '2nd Floor' });
  assert.deepEqual(detectRoomAndFloor('tube light in room 204 is sparking'), { room: '204', floor: '' });
  assert.deepEqual(detectRoomAndFloor('leak near the ground floor washroom'), { room: '', floor: 'Ground Floor' });
  assert.deepEqual(detectRoomAndFloor('wifi down in hostel'), { room: '', floor: '' });
});

test('login limit is per account, so a shared campus IP does not lock everyone out', async () => {
  await initDb();
  const campus = { headers: { 'x-forwarded-for': '10.20.30.40' } };
  for (let i = 0; i < LIMITS.login.limit; i++) assert.equal(await limitLogin(campus, 'guess@uni.edu'), null);
  assert.equal((await limitLogin(campus, 'guess@uni.edu')).statusCode, 429, 'same account is blocked');
  assert.equal(await limitLogin(campus, 'someone.else@uni.edu'), null, 'other students on the same IP still get in');
});
