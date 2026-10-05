import { query, initDb } from './utils/db.mjs';
import { verifyPassword, createSessionToken, createSessionCookie, isValidCollegeEmail } from './utils/auth.mjs';

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

    const email = (body.email || '').trim().toLowerCase();
    const password = body.password || '';

    if (!email || !password) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Please enter both your university email and password.' })
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

    const res = await query('SELECT * FROM students WHERE LOWER(email) = $1', [email]);
    const student = res.rows[0];

    if (!student || !verifyPassword(student.password, password)) {
      return {
        statusCode: 401,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Invalid email address or password. Please verify your credentials.' })
      };
    }

    const token = createSessionToken({
      student_id: student.student_id,
      student_name: student.name,
      student_email: student.email,
      role: 'student'
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
        message: 'Login successful',
        data: {
          token,
          student: {
            id: student.student_id,
            name: student.name,
            email: student.email
          },
          redirectUrl: '/student/dashboard'
        }
      })
    };
  } catch (err) {
    console.error('[auth-login] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'An error occurred during authentication.' })
    };
  }
};
