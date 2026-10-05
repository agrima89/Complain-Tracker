import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';
import { formatTicketId } from './utils/duplicate_logic.mjs';

export const handler = async (event, context) => {
  const session = getSessionFromEvent(event);
  if (!session.authenticated || !session.user.student_id) {
    return {
      statusCode: 401,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unauthorized: Student authentication required.' })
    };
  }

  const studentId = session.user.student_id;
  const params = event.queryStringParameters || {};
  const statusFilter = params.status || 'All';
  const searchQuery = (params.q || '').trim();
  const page = Math.max(1, parseInt(params.page || '1', 10));
  const perPage = Math.min(50, Math.max(1, parseInt(params.per_page || '10', 10)));
  const offset = (page - 1) * perPage;

  try {
    await initDb();

    // 1. Calculate student stats
    const statsSql = `
      SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN status IN ('NEW', 'FORWARDED') THEN 1 END) as pending,
        COUNT(CASE WHEN status IN ('IN_PROGRESS') THEN 1 END) as in_progress,
        COUNT(CASE WHEN status IN ('AWAITING_STUDENT_CONFIRMATION', 'RESOLUTION_SUBMITTED') THEN 1 END) as awaiting,
        COUNT(CASE WHEN status IN ('REOPENED', 'REGENERATED') THEN 1 END) as regenerated,
        COUNT(CASE WHEN status IN ('FINAL_RESOLVED') THEN 1 END) as resolved
      FROM complaints
      WHERE student_id = $1 OR complaint_id IN (SELECT complaint_id FROM complaint_reporters WHERE student_id = $1)
    `;
    const statsRes = await query(statsSql, [studentId]);
    const s = statsRes.rows[0] || {};
    const stats = {
      total: parseInt(s.total || 0, 10),
      pending: parseInt(s.pending || 0, 10),
      in_progress: parseInt(s.in_progress || 0, 10),
      awaiting: parseInt(s.awaiting || 0, 10),
      regenerated: parseInt(s.regenerated || 0, 10),
      resolved: parseInt(s.resolved || 0, 10)
    };

    // 2. Build filtered complaints query
    let whereClauses = [
      `(c.student_id = $1 OR c.complaint_id IN (SELECT complaint_id FROM complaint_reporters WHERE student_id = $1))`
    ];
    let queryParams = [studentId];
    let pIdx = 2;

    if (statusFilter && statusFilter !== 'All') {
      whereClauses.push(`c.status = $${pIdx}`);
      queryParams.push(statusFilter);
      pIdx++;
    }

    if (searchQuery) {
      whereClauses.push(`(
        c.ticket_id ILIKE $${pIdx} OR
        c.category ILIKE $${pIdx} OR
        c.description ILIKE $${pIdx} OR
        c.block ILIKE $${pIdx} OR
        c.room_no ILIKE $${pIdx} OR
        c.location ILIKE $${pIdx}
      )`);
      queryParams.push(`%${searchQuery}%`);
      pIdx++;
    }

    const whereStr = whereClauses.join(' AND ');

    // Total filtered count
    const countRes = await query(`SELECT COUNT(*) as cnt FROM complaints c WHERE ${whereStr}`, queryParams);
    const totalFiltered = parseInt(countRes.rows[0]?.cnt || 0, 10);
    const totalPages = Math.ceil(totalFiltered / perPage) || 1;

    // Fetch page rows
    queryParams.push(perPage, offset);
    const listRes = await query(`
      SELECT c.*
      FROM complaints c
      WHERE ${whereStr}
      ORDER BY c.complaint_id DESC
      LIMIT $${pIdx} OFFSET $${pIdx + 1}
    `, queryParams);

    const complaints = listRes.rows.map(c => ({
      ...c,
      ticket_id: c.ticket_id || formatTicketId(c.complaint_id, c.date)
    }));

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        data: {
          complaints,
          stats,
          pagination: {
            page,
            per_page: perPage,
            total_items: totalFiltered,
            total_pages: totalPages
          }
        }
      })
    };
  } catch (err) {
    console.error('[complaints-list] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error fetching complaints.' })
    };
  }
};
