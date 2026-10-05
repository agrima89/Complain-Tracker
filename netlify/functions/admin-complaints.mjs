import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';
import { formatTicketId, isSimilarIssue } from './utils/duplicate_logic.mjs';

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
  const params = event.queryStringParameters || {};
  const statusFilter = params.status || 'All';
  const priorityFilter = params.priority || 'All';
  const searchQuery = (params.q || '').trim();
  const viewMode = params.view || 'all'; // 'all' or 'grouped'
  const filterEscalated = params.escalated === 'true';

  try {
    await initDb();

    let whereClauses = [];
    let queryParams = [];
    let pIdx = 1;

    // Isolated department filter
    if (adminDept) {
      whereClauses.push(`(LOWER(c.department) = LOWER($${pIdx}) OR LOWER(c.category) = LOWER($${pIdx}))`);
      queryParams.push(adminDept);
      pIdx++;
    }

    if (statusFilter && statusFilter !== 'All') {
      whereClauses.push(`c.status = $${pIdx}`);
      queryParams.push(statusFilter);
      pIdx++;
    }

    if (priorityFilter && priorityFilter !== 'All') {
      whereClauses.push(`c.priority = $${pIdx}`);
      queryParams.push(priorityFilter);
      pIdx++;
    }

    if (filterEscalated) {
      whereClauses.push(`c.priority = 'High' AND c.status != 'FINAL_RESOLVED'`);
    }

    if (searchQuery) {
      whereClauses.push(`(
        c.ticket_id ILIKE $${pIdx} OR
        c.category ILIKE $${pIdx} OR
        c.description ILIKE $${pIdx} OR
        c.block ILIKE $${pIdx} OR
        c.room_no ILIKE $${pIdx} OR
        s.name ILIKE $${pIdx} OR
        s.email ILIKE $${pIdx}
      )`);
      queryParams.push(`%${searchQuery}%`);
      pIdx++;
    }

    const whereStr = whereClauses.length > 0 ? `WHERE ${whereClauses.join(' AND ')}` : '';

    const sql = `
      SELECT c.*, s.name as student_name, s.email as student_email
      FROM complaints c
      LEFT JOIN students s ON c.student_id = s.student_id
      ${whereStr}
      ORDER BY c.complaint_id DESC
    `;

    const res = await query(sql, queryParams);
    const complaints = res.rows.map(c => ({
      ...c,
      ticket_id: c.ticket_id || formatTicketId(c.complaint_id, c.date)
    }));

    if (viewMode === 'grouped') {
      // Grouping logic matching get_grouped_admin_issues
      const groups = [];
      for (const c of complaints) {
        const isTransport = c.category === 'Transport Complaint';
        let foundGroup = false;

        for (const g of groups) {
          if (g.category !== c.category) continue;

          if (isTransport) {
            if (
              g.bus_number !== c.bus_number ||
              g.route !== c.route ||
              g.pickup_drop_point !== c.pickup_drop_point ||
              g.transport_complaint_type !== c.transport_complaint_type
            ) {
              continue;
            }
          } else {
            if (
              g.block !== c.block ||
              g.floor_no !== c.floor_no ||
              g.room_no !== c.room_no
            ) {
              continue;
            }
          }

          if (isSimilarIssue(c.description || '', g.representative_description, c.room_no || '')) {
            const existingStudents = new Set(g.complaints.map(x => x.student_id));
            if (existingStudents.has(c.student_id)) {
              continue;
            }
            g.complaints.push(c);
            g.complaint_count++;
            g.affected_students = existingStudents.size + 1;
            foundGroup = true;
            break;
          }
        }

        if (!foundGroup) {
          groups.push({
            group_id: c.complaint_id,
            category: c.category,
            block: c.block,
            floor_no: c.floor_no,
            room_no: c.room_no,
            location: c.location,
            bus_number: c.bus_number,
            route: c.route,
            pickup_drop_point: c.pickup_drop_point,
            transport_complaint_type: c.transport_complaint_type,
            representative_description: c.description || '',
            complaint_count: 1,
            affected_students: 1,
            complaints: [c],
            evidence_path: c.photo_path,
            status: c.status,
            priority: c.priority,
            date: c.date,
            ticket_id: c.ticket_id
          });
        }
      }

      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          success: true,
          data: {
            groups,
            total_groups: groups.length,
            total_complaints: complaints.length
          }
        })
      };
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        data: {
          complaints,
          total: complaints.length
        }
      })
    };
  } catch (err) {
    console.error('[admin-complaints] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error fetching complaints for admin.' })
    };
  }
};
