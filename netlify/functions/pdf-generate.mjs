import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';
import { generateComplaintPdfBuffer } from './utils/pdf.mjs';
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
      body: JSON.stringify({ success: false, error: 'Complaint ID is required for PDF generation.' })
    };
  }

  try {
    await initDb();

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

    if (!isAdmin) {
      const isOwner = complaint.student_id === studentId;
      const repRes = await query(
        'SELECT 1 FROM complaint_reporters WHERE complaint_id = $1 AND student_id = $2',
        [complaintId, studentId]
      );
      if (!isOwner && repRes.rows.length === 0) {
        return {
          statusCode: 403,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ success: false, error: 'Unauthorized: You can only download PDFs for your own complaints.' })
        };
      }
    }

    complaint.ticket_id = complaint.ticket_id || formatTicketId(complaint.complaint_id, complaint.date);

    const histRes = await query(`
      SELECT * FROM complaint_status_history
      WHERE complaint_id = $1
      ORDER BY history_id ASC
    `, [complaintId]);

    const pdfBuffer = await generateComplaintPdfBuffer(complaint, histRes.rows);
    const filename = `CampusCare_Slip_${complaint.ticket_id || complaint.complaint_id}.pdf`;

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Cache-Control': 'private, no-cache'
      },
      body: pdfBuffer.toString('base64'),
      isBase64Encoded: true
    };
  } catch (err) {
    console.error('[pdf-generate] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Error generating PDF document.' })
    };
  }
};
