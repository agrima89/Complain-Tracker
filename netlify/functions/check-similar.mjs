import { query, initDb } from './utils/db.mjs';
import { computeSimilarityScore } from './utils/smart_complaint.mjs';
import { formatTicketId } from './utils/duplicate_logic.mjs';

export const handler = async (event, context) => {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Method Not Allowed' })
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

    const description = (body.description || '').trim();
    const category = (body.category || '').trim();
    const block = (body.block || '').trim();

    if (!description || description.length < 8) {
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ found: false, matches: [], count: 0 })
      };
    }

    // Query active unresolved complaints
    const activeRes = await query(`
      SELECT complaint_id, ticket_id, category, description, block, location, priority, status, date
      FROM complaints
      WHERE status IN ('NEW', 'PENDING', 'IN_PROGRESS', 'REOPENED', 'FORWARDED')
      ORDER BY complaint_id DESC
      LIMIT 100
    `);

    const matches = [];
    const threshold = 0.28;

    for (const cand of activeRes.rows) {
      const score = computeSimilarityScore(
        description,
        cand.description || '',
        category,
        cand.category,
        block,
        cand.block
      );

      if (score >= threshold) {
        matches.push({
          complaint_id: cand.complaint_id,
          ticket_id: cand.ticket_id || formatTicketId(cand.complaint_id, cand.date),
          category: cand.category,
          location: cand.block || cand.location,
          priority: cand.priority,
          status: cand.status,
          date: cand.date,
          similarity_score: score,
          similarity_pct: Math.round(score * 100)
        });
      }
    }

    matches.sort((a, b) => b.similarity_score - a.similarity_score);
    const topMatches = matches.slice(0, 4);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        found: topMatches.length > 0,
        count: topMatches.length,
        matches: topMatches
      })
    };
  } catch (err) {
    console.error('[check-similar] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Error checking for similar complaints.' })
    };
  }
};
