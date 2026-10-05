import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';
import { formatTicketId } from './utils/duplicate_logic.mjs';

const ZONES_CONFIG = {
  "Block A": { id: "block-a", name: "Block A", label: "Academic Block A", type: "Computer Science & IT Labs", x: 50, y: 80, w: 150, h: 105 },
  "Block B": { id: "block-b", name: "Block B", label: "Academic Block B", type: "Electronics & Tech Labs", x: 230, y: 80, w: 150, h: 105 },
  "Block C": { id: "block-c", name: "Block C", label: "Academic Block C", type: "Mechanical & Civil Wings", x: 410, y: 80, w: 150, h: 105 },
  "Block D": { id: "block-d", name: "Block D", label: "Management Block D", type: "Business & Media Studios", x: 590, y: 80, w: 150, h: 105 },
  "Block E": { id: "block-e", name: "Block E", label: "Science Block E", type: "Biotech & Chemistry", x: 50, y: 215, w: 150, h: 105 },
  "Block F": { id: "block-f", name: "Block F", label: "Innovation Block F", type: "AI & Research Center", x: 230, y: 215, w: 150, h: 105 },
  "Academic Block": { id: "academic-complex", name: "Academic Complex", label: "Central Academic Complex", type: "Lecture Theatres & Offices", x: 410, y: 215, w: 150, h: 105 },
  "Hostel": { id: "hostels", name: "Hostel Complex", label: "Campus Hostels Complex", type: "Resident Towers & Mess", x: 590, y: 215, w: 150, h: 105 },
  "Library": { id: "library", name: "Central Library", label: "Central Knowledge Library", type: "Reading Halls & Archives", x: 50, y: 350, w: 150, h: 100 },
  "Sports": { id: "sports-arena", name: "Sports Arena", label: "Sports Arena & Complex", type: "Gymnasium & Courts", x: 230, y: 350, w: 150, h: 100 },
  "Campus": { id: "cafeteria", name: "Campus & Food Plaza", label: "Central Campus & Cafeteria", type: "Food Court & Student Plaza", x: 410, y: 350, w: 150, h: 100 },
  "Other": { id: "utility-grounds", name: "Utility Grounds", label: "University Utility Grounds", type: "Infrastructure & Parking", x: 590, y: 350, w: 150, h: 100 }
};

export const handler = async (event, context) => {
  const session = getSessionFromEvent(event);
  if (!session.authenticated || session.user.role !== 'admin') {
    return {
      statusCode: 401,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unauthorized: Admin access required.' })
    };
  }

  const adminDept = session.user.admin_department || '';
  const zoneId = event.queryStringParameters?.zone_id;

  try {
    await initDb();

    let deptFilter = '';
    let params = [];
    if (adminDept) {
      deptFilter = 'WHERE LOWER(c.department) = LOWER($1) OR LOWER(c.category) = LOWER($1)';
      params = [adminDept];
    }

    const res = await query(`
      SELECT c.*, s.name as student_name, s.email as student_email
      FROM complaints c
      LEFT JOIN students s ON c.student_id = s.student_id
      ${deptFilter}
      ORDER BY c.complaint_id DESC
    `, params);

    const rows = res.rows;

    const zoneBuckets = {};
    for (const [k, v] of Object.entries(ZONES_CONFIG)) {
      zoneBuckets[k] = {
        ...v,
        complaints: [],
        total: 0,
        unresolved: 0,
        high: 0,
        medium: 0,
        low: 0,
        intensity: 'Low'
      };
    }

    for (const r of rows) {
      const blockKey = r.block && r.block in zoneBuckets ? r.block : 'Other';
      const z = zoneBuckets[blockKey];
      z.complaints.push({
        ...r,
        ticket_id: r.ticket_id || formatTicketId(r.complaint_id, r.date)
      });
      z.total++;
      if (r.status !== 'FINAL_RESOLVED') {
        z.unresolved++;
      }
      if (r.priority === 'High') z.high++;
      else if (r.priority === 'Medium') z.medium++;
      else z.low++;
    }

    for (const z of Object.values(zoneBuckets)) {
      if (z.high >= 3 || z.unresolved >= 8) z.intensity = 'Critical';
      else if (z.high >= 1 || z.unresolved >= 4) z.intensity = 'High';
      else if (z.unresolved >= 1) z.intensity = 'Moderate';
      else z.intensity = 'Low';
    }

    if (zoneId) {
      const match = Object.values(zoneBuckets).find(z => z.id === zoneId);
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: true, data: match || null })
      };
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        data: {
          zones: Object.values(zoneBuckets)
        }
      })
    };
  } catch (err) {
    console.error('[admin-zone] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error fetching campus heatmap data.' })
    };
  }
};
