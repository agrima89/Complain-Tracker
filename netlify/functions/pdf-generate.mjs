import { toV2 } from './utils/v2.mjs';
import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent, adminCanAccessComplaint } from './utils/auth.mjs';
import { generateComplaintPdfBuffer, generateSummaryReportPdfBuffer } from './utils/pdf.mjs';
import { formatTicketId } from './utils/duplicate_logic.mjs';
import { getEvidenceBlob } from './utils/blobs.mjs';

const handler = async (event, context) => {
  const session = getSessionFromEvent(event);
  if (!session.authenticated) {
    return {
      statusCode: 401,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unauthorized: Authentication required.' })
    };
  }

  if (event.queryStringParameters?.report) {
    return summaryReport(session);
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

    if (isAdmin && !adminCanAccessComplaint(session.user, complaint)) {
      return {
        statusCode: 403,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'This complaint belongs to another department.' })
      };
    }

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

    let photo = null;
    if (complaint.photo_path) {
      try { photo = await getEvidenceBlob(complaint.photo_path); }
      catch (e) { console.warn('[pdf-generate] evidence lookup failed:', e.message); }
    }

    // Link to the photo on this site (Netlify sets URL in production; otherwise use the request host).
    const h = event.headers || {};
    const base = process.env.URL || (h.host ? `${h['x-forwarded-proto'] || (h.host.startsWith('localhost') ? 'http' : 'https')}://${h.host}` : '');
    const photoUrl = base ? `${base}/complaints/${complaint.complaint_id}/evidence` : '';

    const pdfBuffer = await generateComplaintPdfBuffer(complaint, histRes.rows, photo, photoUrl);
    const filename = `CampusCare_Slip_${complaint.ticket_id || complaint.complaint_id}.pdf`;

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Cache-Control': 'private, no-store'
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

async function summaryReport(session) {
  if (session.user.role !== 'admin') {
    return { statusCode: 403, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ success: false, error: 'Admin access required.' }) };
  }
  try {
    await initDb();
    const dept = session.user.admin_department || '';
    const where = dept ? 'WHERE (LOWER(department) = LOWER($1) OR LOWER(category) = LOWER($1))' : '';
    const params = dept ? [dept] : [];
    const totals = await query(`SELECT status, COUNT(*) AS count FROM complaints ${where} GROUP BY status`, params);
    const stats = { total: 0, pending: 0, in_progress: 0, resolved: 0 };
    for (const r of totals.rows) {
      const n = parseInt(r.count, 10) || 0;
      const st = String(r.status || '').toLowerCase();
      stats.total += n;
      if (st.includes('resolved') || st === 'closed') stats.resolved += n;
      else if (st.includes('progress') || st.includes('forward') || st.includes('awaiting')) stats.in_progress += n;
      else stats.pending += n;
    }
    const byCategory = (await query(`SELECT category, COUNT(*) AS count FROM complaints ${where} GROUP BY category ORDER BY count DESC`, params)).rows;
    const byPriority = (await query(`SELECT priority, COUNT(*) AS count FROM complaints ${where} GROUP BY priority ORDER BY count DESC`, params)).rows;
    const recent = (await query(`SELECT * FROM complaints ${where} ORDER BY complaint_id DESC LIMIT 100`, params)).rows
      .map(c => ({ ...c, ticket_id: c.ticket_id || formatTicketId(c.complaint_id, c.date) }));
    const pdf = await generateSummaryReportPdfBuffer({ stats, byCategory, byPriority, recent, scope: dept ? `${dept} department` : 'All departments' });
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/pdf', 'Content-Disposition': `attachment; filename="CampusCare_Summary_${new Date().toISOString().slice(0, 10)}.pdf"`, 'Cache-Control': 'private, no-store' },
      body: pdf.toString('base64'),
      isBase64Encoded: true
    };
  } catch (err) {
    console.error('[pdf-generate] summary error:', err);
    return { statusCode: 500, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ success: false, error: 'Error generating report.' }) };
  }
}

// Modern Netlify Function (gets the Netlify Database connection).
export default toV2(handler);
