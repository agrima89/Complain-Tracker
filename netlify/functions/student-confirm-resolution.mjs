import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';

export const handler = async (event, context) => {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Method Not Allowed' })
    };
  }

  const session = getSessionFromEvent(event);
  if (!session.authenticated || !session.user.student_id) {
    return {
      statusCode: 401,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unauthorized: Student authentication required.' })
    };
  }

  const studentId = session.user.student_id;

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

    const complaintId = body.complaint_id;
    if (!complaintId) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Complaint ID is required.' })
      };
    }

    const compRes = await query('SELECT * FROM complaints WHERE complaint_id = $1', [complaintId]);
    const complaint = compRes.rows[0];
    if (!complaint) {
      return {
        statusCode: 404,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Complaint not found.' })
      };
    }

    // Verify student is associated
    const isOwner = complaint.student_id === studentId;
    const repRes = await query(
      'SELECT 1 FROM complaint_reporters WHERE complaint_id = $1 AND student_id = $2',
      [complaintId, studentId]
    );
    if (!isOwner && repRes.rows.length === 0) {
      return {
        statusCode: 403,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Unauthorized: You are not associated with this complaint.' })
      };
    }

    const nowTimestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);

    await query(`
      UPDATE complaints
      SET student_confirmation = 'confirmed', student_confirmation_time = $1,
          final_resolution_time = $2, status = 'FINAL_RESOLVED', last_updated = $3
      WHERE complaint_id = $4
    `, [nowTimestamp, nowTimestamp, nowTimestamp, complaintId]);

    await query(`
      INSERT INTO complaint_status_history (
        complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at
      ) VALUES ($1, NULL, 'Student', 'AWAITING_STUDENT_CONFIRMATION', 'FINAL_RESOLVED', 'Student confirmed resolution and closed ticket.', $2)
    `, [complaintId, nowTimestamp]);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        message: 'Resolution confirmed. Ticket officially marked as FINAL RESOLVED.'
      })
    };
  } catch (err) {
    console.error('[student-confirm-resolution] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error confirming resolution.' })
    };
  }
};
