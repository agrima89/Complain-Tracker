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
    const department = (body.department || '').trim();
    const reason = (body.reason || '').trim();
    const adminId = session.user.admin_id;
    const adminName = session.user.admin_username || 'Administrator';

    if (!complaintId || !department) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Complaint ID and target department are required.' })
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
      SET department = $1, forwarded_to = $2, forwarded_by = $3, forwarded_at = $4,
          status = 'FORWARDED', last_updated = $5
      WHERE complaint_id = $6
    `, [department, department, adminName, nowTimestamp, nowTimestamp, complaintId]);

    await query(`
      INSERT INTO complaint_status_history (
        complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at
      ) VALUES ($1, $2, $3, $4, 'FORWARDED', $5, $6)
    `, [complaintId, adminId, adminName, oldStatus, `Forwarded to ${department}. Reason: ${reason || 'Inter-departmental dispatch'}`, nowTimestamp]);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        message: `Complaint successfully forwarded to ${department}.`
      })
    };
  } catch (err) {
    console.error('[admin-forward] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error forwarding complaint.' })
    };
  }
};
