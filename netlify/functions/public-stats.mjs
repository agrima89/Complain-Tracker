import { query, initDb } from './utils/db.mjs';

export const handler = async (event, context) => {
  try {
    await initDb();

    const sql = `
      SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN status = 'FINAL_RESOLVED' THEN 1 END) as resolved,
        COUNT(CASE WHEN status = 'IN_PROGRESS' THEN 1 END) as in_progress,
        COUNT(CASE WHEN status IN ('NEW', 'FORWARDED') THEN 1 END) as pending
      FROM complaints
    `;

    const res = await query(sql);
    const row = res.rows[0] || {};
    const total = parseInt(row.total || 0, 10);
    const resolved = parseInt(row.resolved || 0, 10);
    const inProgress = parseInt(row.in_progress || 0, 10);
    const pending = parseInt(row.pending || 0, 10);

    const resolutionRate = total > 0 ? ((resolved / total) * 100).toFixed(1) : '100.0';

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=30'
      },
      body: JSON.stringify({
        success: true,
        data: {
          total,
          resolved,
          in_progress: inProgress,
          pending,
          resolution_rate: `${resolutionRate}%`,
          avg_resolution_time: '< 24 Hours'
        }
      })
    };
  } catch (err) {
    console.error('[public-stats] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error fetching public statistics.' })
    };
  }
};
