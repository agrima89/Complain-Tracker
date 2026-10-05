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

  try {
    await initDb();

    if (event.httpMethod === 'POST') {
      const body = JSON.parse(event.body || '{}');
      const eventType = body.event_type || 'SYSTEM_INFO';
      const userEmail = body.user_email || session.user.admin_username || '';
      const complaintId = body.complaint_id || '';
      const department = body.department || session.user.admin_department || '';
      const severity = body.severity || 'LOW';
      const details = body.details || '';
      const nowTimestamp = new Date().toISOString().replace('T', ' ').slice(0, 19);

      await query(`
        INSERT INTO soc_audit_logs (event_type, user_email, complaint_id, department, severity, timestamp, details)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
      `, [eventType, userEmail, String(complaintId), department, severity, nowTimestamp, details]);

      return {
        statusCode: 201,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: true, message: 'Event logged.' })
      };
    }

    // GET: Return logs and analytics
    const logsRes = await query(`
      SELECT * FROM soc_audit_logs
      ORDER BY log_id DESC
      LIMIT 100
    `);

    const statsRes = await query(`
      SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN severity = 'HIGH' THEN 1 END) as high_severity,
        COUNT(CASE WHEN event_type = 'FAILED_LOGIN' THEN 1 END) as failed_logins,
        COUNT(CASE WHEN event_type = 'UNAUTHORIZED_ACCESS' THEN 1 END) as unauthorized
      FROM soc_audit_logs
    `);

    const s = statsRes.rows[0] || {};

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        data: {
          logs: logsRes.rows,
          total: parseInt(s.total || 0, 10),
          high_severity: parseInt(s.high_severity || 0, 10),
          failed_logins: parseInt(s.failed_logins || 0, 10),
          unauthorized: parseInt(s.unauthorized || 0, 10)
        }
      })
    };
  } catch (err) {
    console.error('[soc-logs] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error handling SOC logs.' })
    };
  }
};
