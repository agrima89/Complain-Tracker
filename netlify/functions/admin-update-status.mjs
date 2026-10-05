import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';

const VALID_STATUSES = [
  'NEW', 'FORWARDED', 'IN_PROGRESS', 'REOPENED',
  'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION', 'FINAL_RESOLVED'
];

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
    const newStatus = (body.new_status || body.status || '').trim();
    const remarks = (body.remarks || '').trim();
    const adminId = session.user.admin_id;
    const adminName = session.user.admin_username || 'Administrator';

    if (!complaintId || !newStatus || !VALID_STATUSES.includes(newStatus)) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Valid complaint ID and status are required.' })
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

    // Update complaint
    await query(`
      UPDATE complaints
      SET status = $1, last_updated = $2
      WHERE complaint_id = $3
    `, [newStatus, nowTimestamp, complaintId]);

    // Insert into status history audit trail
    await query(`
      INSERT INTO complaint_status_history (
        complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7)
    `, [complaintId, adminId, adminName, oldStatus, newStatus, remarks || 'Status updated by administrator.', nowTimestamp]);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        message: `Status updated from ${oldStatus} to ${newStatus}.`,
        data: {
          complaint_id: complaintId,
          old_status: oldStatus,
          new_status: newStatus,
          changed_at: nowTimestamp
        }
      })
    };
  } catch (err) {
    console.error('[admin-update-status] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error updating complaint status.' })
    };
  }
};
