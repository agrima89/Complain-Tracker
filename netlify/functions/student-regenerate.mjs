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
    const reason = (body.reason || '').trim();
    const newPhoto = (body.new_photo || '').trim();

    if (!complaintId || !reason) {
      return {
        statusCode: 400,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Complaint ID and regeneration reason are required.' })
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

    const newCount = (complaint.regeneration_count || 0) + 1;
    const currentTicket = complaint.ticket_id || `CMP-${complaint.complaint_id}`;
    const baseTicket = currentTicket.split('-R')[0];
    const newTicketId = `${baseTicket}-R${newCount}`;
    const nowTimestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);

    await query(`
      UPDATE complaints
      SET status = 'REOPENED', regenerated_by_student = 1, regeneration_count = $1,
          regeneration_reason = $2,
          previous_resolution_details = $3,
          photo_path = COALESCE(NULLIF($4, ''), photo_path),
          ticket_id = $5, last_updated = $6
      WHERE complaint_id = $7
    `, [
      newCount,
      reason,
      `Previously marked resolved by department at ${complaint.department_resolution_time || 'prior stage'}`,
      newPhoto || '',
      newTicketId,
      nowTimestamp,
      complaintId
    ]);

    await query(`
      INSERT INTO complaint_status_history (
        complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at
      ) VALUES ($1, NULL, 'Student', 'AWAITING_STUDENT_CONFIRMATION', 'REOPENED', $2, $3)
    `, [complaintId, `Student reopened complaint (Cycle ${newCount}). Reason: ${reason}`, nowTimestamp]);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        message: `Complaint regenerated and sent back for administrative action. New Ticket ID: ${newTicketId}`,
        data: {
          ticket_id: newTicketId,
          regeneration_count: newCount
        }
      })
    };
  } catch (err) {
    console.error('[student-regenerate] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error regenerating complaint.' })
    };
  }
};
