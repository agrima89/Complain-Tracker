import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';
import { formatTicketId } from './utils/duplicate_logic.mjs';

export const handler = async (event, context) => {
  const session = getSessionFromEvent(event);
  if (!session.authenticated) {
    return {
      statusCode: 401,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unauthorized: Authentication required.' })
    };
  }

  const complaintId = event.queryStringParameters?.id || event.queryStringParameters?.complaint_id;
  if (!complaintId) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Complaint ID is required.' })
    };
  }

  try {
    await initDb();

    // Fetch complaint with student info
    const compRes = await query(`
      SELECT c.*, s.name as student_name, s.email as student_email
      FROM complaints c
      LEFT JOIN students s ON c.student_id = s.student_id
      WHERE c.complaint_id = $1
    `, [complaintId]);

    const complaint = compRes.rows[0];
    if (!complaint) {
      return {
        statusCode: 404,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Complaint not found.' })
      };
    }

    const isAdmin = session.user.role === 'admin';
    const studentId = session.user.student_id;

    // Student authorization check
    if (!isAdmin) {
      const isOwner = complaint.student_id === studentId;
      const repRes = await query(`
        SELECT 1 FROM complaint_reporters
        WHERE complaint_id = $1 AND student_id = $2
      `, [complaintId, studentId]);

      if (!isOwner && repRes.rows.length === 0) {
        return {
          statusCode: 403,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ success: false, error: 'Unauthorized: You do not have access to this complaint.' })
        };
      }
    }

    complaint.ticket_id = complaint.ticket_id || formatTicketId(complaint.complaint_id, complaint.date);

    // Fetch status history
    const histRes = await query(`
      SELECT * FROM complaint_status_history
      WHERE complaint_id = $1
      ORDER BY history_id ASC
    `, [complaintId]);

    // Fetch notes (full notes for admin, filtered for students)
    const notesRes = await query(`
      SELECT note_id, complaint_id, admin_name, note, created_at
      FROM admin_notes
      WHERE complaint_id = $1
      ORDER BY note_id ASC
    `, [complaintId]);

    // Fetch reporters (for grouped issues)
    const repListRes = await query(`
      SELECT cr.student_id, cr.reported_at, s.name as student_name, s.email as student_email
      FROM complaint_reporters cr
      LEFT JOIN students s ON cr.student_id = s.student_id
      WHERE cr.complaint_id = $1
      ORDER BY cr.reported_at ASC
    `, [complaintId]);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        data: {
          complaint,
          history: histRes.rows,
          notes: notesRes.rows,
          reporters: repListRes.rows
        }
      })
    };
  } catch (err) {
    console.error('[complaints-get] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error retrieving complaint details.' })
    };
  }
};
