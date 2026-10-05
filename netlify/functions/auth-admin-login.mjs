import { query, initDb } from './utils/db.mjs';
import { verifyPassword, createSessionToken, createSessionCookie } from './utils/auth.mjs';

export const handler = async (event, context) => {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Method Not Allowed' })
    };
  }

  try {
    await initDb();
    let body = {};
    try {
      body = JSON.parse(event.body || '{}');
    } catch {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Invalid JSON request body' })
      };
    }

    const username = (body.username || '').trim().toLowerCase();
    const password = body.password || '';

    if (!username || !password) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Please enter administrator username and password.' })
      };
    }

    const res = await query('SELECT * FROM admins WHERE LOWER(username) = $1', [username]);
    const admin = res.rows[0];

    if (!admin || !verifyPassword(admin.password, password)) {
      return {
        statusCode: 401,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Invalid administrative credentials.' })
      };
    }

    const token = createSessionToken({
      admin_id: admin.admin_id,
      admin_username: admin.username,
      admin_role: admin.role || 'Super Admin',
      admin_department: admin.department || '',
      role: 'admin'
    });

    const cookieHeader = createSessionCookie(token);

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Set-Cookie': cookieHeader
      },
      body: JSON.stringify({
        success: true,
        message: 'Admin authorization granted',
        data: {
          token,
          admin: {
            id: admin.admin_id,
            username: admin.username,
            role: admin.role || 'Super Admin',
            department: admin.department || ''
          },
          redirectUrl: '/admin/dashboard'
        }
      })
    };
  } catch (err) {
    console.error('[auth-admin-login] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'An error occurred during administrative login.' })
    };
  }
};
