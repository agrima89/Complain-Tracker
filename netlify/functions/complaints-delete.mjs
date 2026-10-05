import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';

export const handler = async (event, context) => {
  if (event.httpMethod !== 'POST' && event.httpMethod !== 'DELETE') {
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
  let body = {};
  try {
    body = JSON.parse(event.body || '{}');
  } catch {
    body = {};
  }

  const complaintId = body.complaint_id || event.queryStringParameters?.id || event.queryStringParameters?.complaint_id;

  if (!complaintId) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Complaint ID is required for deletion.' })
    };
  }

  try {
    await initDb();

    // 1. Fetch complaint
    const compRes = await query('SELECT * FROM complaints WHERE complaint_id = $1', [complaintId]);
    const complaint = compRes.rows[0];

    if (!complaint) {
      return {
        statusCode: 404,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Complaint not found.' })
      };
    }

    // 2. Authorization check
    const isOwner = complaint.student_id === studentId;
    const repRes = await query(
      'SELECT 1 FROM complaint_reporters WHERE complaint_id = $1 AND student_id = $2',
      [complaintId, studentId]
    );
    const isReporter = repRes.rows.length > 0;

    if (!isOwner && !isReporter) {
      return {
        statusCode: 403,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: false, error: 'Unauthorized: You can only delete your own complaints.' })
      };
    }

    // 3. Status check
    if (complaint.status !== 'NEW') {
      return {
        statusCode: 403,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          success: false,
          error: 'This complaint can no longer be deleted because it is already being processed by the administration.'
        })
      };
    }

    // 4. Check reporter count
    const countRes = await query('SELECT COUNT(*) as cnt FROM complaint_reporters WHERE complaint_id = $1', [complaintId]);
    const reportersCount = parseInt(countRes.rows[0]?.cnt || 1, 10);
    const affectedCount = parseInt(complaint.affected_student_count || 1, 10);

    if (reportersCount <= 1 && affectedCount <= 1) {
      // Safe to delete completely
      await query('DELETE FROM complaint_reporters WHERE complaint_id = $1', [complaintId]);
      await query('DELETE FROM complaint_status_history WHERE complaint_id = $1', [complaintId]);
      await query('DELETE FROM active_complaint_slots WHERE complaint_id = $1', [complaintId]);
      await query('DELETE FROM complaints WHERE complaint_id = $1', [complaintId]);
    } else {
      // Grouped complaint: disassociate this student
      await query('DELETE FROM complaint_reporters WHERE complaint_id = $1 AND student_id = $2', [complaintId, studentId]);
      await query(`
        UPDATE complaints
        SET affected_student_count = CASE WHEN affected_student_count > 1 THEN affected_student_count - 1 ELSE 1 END
        WHERE complaint_id = $1
      `, [complaintId]);

      if (isOwner) {
        const nextRep = await query(
          'SELECT student_id FROM complaint_reporters WHERE complaint_id = $1 LIMIT 1',
          [complaintId]
        );
        if (nextRep.rows.length > 0) {
          await query('UPDATE complaints SET student_id = $1 WHERE complaint_id = $2', [
            nextRep.rows[0].student_id,
            complaintId
          ]);
        }
      }
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        message: 'Complaint deleted successfully.'
      })
    };
  } catch (err) {
    console.error('[complaints-delete] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error during complaint deletion.' })
    };
  }
};
