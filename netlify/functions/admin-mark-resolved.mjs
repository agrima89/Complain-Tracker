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
  if (!session.authenticated || session.user.role !== 'admin') {
    return {
      statusCode: 401,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unauthorized: Admin access required.' })
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

    const complaintId = body.complaint_id;
    const remarks = (body.remarks || '').trim();
    const adminId = session.user.admin_id;
    const adminName = session.user.admin_username || 'Department Officer';

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

    const oldStatus = complaint.status;
    const nowTimestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);

    await query(`
      UPDATE complaints
      SET resolved_by_department = 1, department_resolution_time = $1,
          status = 'AWAITING_STUDENT_CONFIRMATION', last_updated = $2
      WHERE complaint_id = $3
    `, [nowTimestamp, nowTimestamp, complaintId]);

    await query(`
      INSERT INTO complaint_status_history (
        complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at
      ) VALUES ($1, $2, $3, $4, 'AWAITING_STUDENT_CONFIRMATION', $5, $6)
    `, [complaintId, adminId, adminName, oldStatus, `Resolved by department. Remarks: ${remarks || 'Resolution submitted for student verification'}`, nowTimestamp]);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        message: 'Complaint marked as resolved by department. Awaiting student confirmation.'
      })
    };
  } catch (err) {
    console.error('[admin-mark-resolved] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error marking complaint as resolved.' })
    };
  }
};
