import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';

export const handler = async (event, context) => {
  const session = getSessionFromEvent(event);
  if (!session.authenticated || session.user.role !== 'admin') {
    return {
      statusCode: 401,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unauthorized: Admin access required.' })
    };
  }

  const adminId = session.user.admin_id;
  const adminName = session.user.admin_username || 'Administrator';

  try {
    await initDb();

    if (event.httpMethod === 'POST') {
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
      const note = (body.note || '').trim();

      if (!complaintId || !note) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ success: false, error: 'Complaint ID and note text are required.' })
        };
      }

      const nowTimestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);
      const res = await query(`
        INSERT INTO admin_notes (complaint_id, admin_id, admin_name, note, created_at)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING note_id
      `, [complaintId, adminId, adminName, note, nowTimestamp]);

      return {
        statusCode: 201,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          success: true,
          message: 'Note added successfully.',
          data: {
            note_id: res.lastRowId || res.rows[0]?.note_id,
            complaint_id: complaintId,
            admin_name: adminName,
            note,
            created_at: nowTimestamp
          }
        })
      };
    }

    if (event.httpMethod === 'GET') {
      const complaintId = event.queryStringParameters?.complaint_id || event.queryStringParameters?.id;
      if (!complaintId) {
        return {
          statusCode: 400,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ success: false, error: 'Complaint ID is required.' })
        };
      }

      const res = await query(`
        SELECT * FROM admin_notes
        WHERE complaint_id = $1
        ORDER BY note_id ASC
      `, [complaintId]);

      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          success: true,
          data: res.rows
        })
      };
    }

    return {
      statusCode: 405,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Method Not Allowed' })
    };
  } catch (err) {
    console.error('[admin-notes] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error handling admin note.' })
    };
  }
};
