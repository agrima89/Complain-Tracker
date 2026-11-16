import { toV2 } from './utils/v2.mjs';
/**
 * Staff accounts, managed by the main (all-departments) admin only.
 * GET  -> list accounts
 * POST { action: 'create', username, department } -> new account + one-time password
 * POST { action: 'reset', admin_id }               -> new one-time password
 * POST { action: 'disable' | 'enable', admin_id }
 */
import crypto from 'crypto';
import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent, hashPassword } from './utils/auth.mjs';
import { json, parseJsonBody } from './utils/http.mjs';

const DEPARTMENTS = ['Electrical', 'Cleaning', 'Classroom', 'Hostel', 'Wi-Fi/Internet', 'Library', 'Infrastructure', 'Transport', 'Other'];

// Readable one-time password: no look-alike characters (0/O, 1/l/I).
function oneTimePassword() {
  const chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  const bytes = crypto.randomBytes(14);
  return Array.from(bytes, b => chars[b % chars.length]).join('').replace(/(.{4})(?=.)/g, '$1-');
}

async function audit(session, eventType, details) {
  try {
    await query(
      `INSERT INTO soc_audit_logs (event_type, user_email, complaint_id, department, severity, timestamp, details)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [eventType, session.user.admin_username || 'admin', '', '', 'MEDIUM', new Date().toISOString().replace('T', ' ').slice(0, 19), details]
    );
  } catch (e) { console.warn('[admin-staff] audit log failed:', e.message); }
}

const handler = async (event) => {
  const session = getSessionFromEvent(event);
  if (!session.authenticated || session.user.role !== 'admin') return json(401, { success: false, error: 'Admin access required.' });
  if (session.user.admin_department) return json(403, { success: false, error: 'Only the main administrator can manage staff accounts.' });

  await initDb();

  if (event.httpMethod === 'GET') {
    const res = await query('SELECT admin_id, username, department, role, is_active FROM admins ORDER BY department, username');
    return json(200, {
      success: true,
      data: {
        departments: DEPARTMENTS,
        me: session.user.admin_id,
        staff: res.rows.map(a => ({ ...a, is_active: !(a.is_active === 0 || a.is_active === false) }))
      }
    });
  }

  if (event.httpMethod !== 'POST') return json(405, { success: false, error: 'Method Not Allowed' });
  const body = parseJsonBody(event);
  if (!body) return json(400, { success: false, error: 'Invalid request.' });

  if (body.action === 'create') {
    const username = String(body.username || '').trim().toLowerCase();
    const department = String(body.department || '').trim();
    if (!/^[a-z0-9._-]{3,40}$/.test(username)) return json(400, { success: false, error: 'Username must be 3-40 letters, digits, dots, dashes or underscores.' });
    if (department && !DEPARTMENTS.includes(department)) return json(400, { success: false, error: 'Choose a valid department.' });
    const taken = await query('SELECT 1 FROM admins WHERE LOWER(username) = $1', [username]);
    if (taken.rows.length) return json(409, { success: false, error: 'That username is already taken.' });
    const password = oneTimePassword();
    await query('INSERT INTO admins (username, password, role, department, is_active) VALUES ($1, $2, $3, $4, 1)',
      [username, hashPassword(password), department ? 'Department Admin' : 'Super Admin', department]);
    await audit(session, 'STAFF_CREATED', `${username} (${department || 'all departments'})`);
    return json(201, { success: true, data: { username, password } });
  }

  const adminId = parseInt(body.admin_id, 10);
  if (!adminId) return json(400, { success: false, error: 'Staff account is required.' });
  const target = (await query('SELECT admin_id, username FROM admins WHERE admin_id = $1', [adminId])).rows[0];
  if (!target) return json(404, { success: false, error: 'Staff account not found.' });

  if (body.action === 'reset') {
    const password = oneTimePassword();
    await query('UPDATE admins SET password = $1 WHERE admin_id = $2', [hashPassword(password), adminId]);
    await audit(session, 'STAFF_PASSWORD_RESET', target.username);
    return json(200, { success: true, data: { username: target.username, password } });
  }

  if (body.action === 'disable' || body.action === 'enable') {
    if (adminId === session.user.admin_id) return json(400, { success: false, error: "You can't disable your own account." });
    await query('UPDATE admins SET is_active = $1 WHERE admin_id = $2', [body.action === 'enable' ? 1 : 0, adminId]);
    await audit(session, body.action === 'enable' ? 'STAFF_ENABLED' : 'STAFF_DISABLED', target.username);
    return json(200, { success: true });
  }

  return json(400, { success: false, error: 'Unknown action.' });
};

// Modern Netlify Function (gets the Netlify Database connection).
export default toV2(handler);
