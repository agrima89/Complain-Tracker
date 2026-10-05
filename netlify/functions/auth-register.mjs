import { query, initDb } from './utils/db.mjs';
import { hashPassword, createSessionToken, createSessionCookie, isValidCollegeEmail } from './utils/auth.mjs';

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

    const name = (body.name || '').trim();
    const email = (body.email || '').trim().toLowerCase();
    const password = body.password || '';

    if (!name || name.length < 2) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Please enter your full legal name.' })
      };
    }

    const emailCheck = isValidCollegeEmail(email);
    if (!emailCheck.valid) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: emailCheck.message })
      };
    }

    if (!password || password.length < 4) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Password must be at least 4 characters long.' })
      };
    }

    // Check if email already registered
    const existing = await query('SELECT student_id FROM students WHERE LOWER(email) = $1', [email]);
    if (existing.rows.length > 0) {
      return {
        statusCode: 409,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'This university email is already registered. Please sign in.' })
      };
    }

    const hashedPassword = hashPassword(password);
    const insertRes = await query(
      'INSERT INTO students (name, email, password) VALUES ($1, $2, $3) RETURNING student_id',
      [name, email, hashedPassword]
    );

    const studentId = insertRes.lastRowId || insertRes.rows[0]?.student_id;

    const token = createSessionToken({
      student_id: studentId,
      student_name: name,
      student_email: email,
      role: 'student'
    });

    const cookieHeader = createSessionCookie(token);

    return {
      statusCode: 201,
      headers: {
        'Content-Type': 'application/json',
        'Set-Cookie': cookieHeader
      },
      body: JSON.stringify({
        success: true,
        message: 'Account registered successfully.',
        data: {
          token,
          student: {
            id: studentId,
            name,
            email
          },
          redirectUrl: '/student/dashboard'
        }
      })
    };
  } catch (err) {
    console.error('[auth-register] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'An error occurred during registration.' })
    };
  }
};
