import { query, initDb } from './utils/db.mjs';
import { getSessionFromEvent } from './utils/auth.mjs';
import { formatTicketId } from './utils/duplicate_logic.mjs';

const ZONES_CONFIG = {
  "Block A": { id: "block-a", name: "Block A", label: "Academic Block A", type: "Computer Science & IT Labs", category_hint: "Computer Science & IT Labs", x: 50, y: 80, w: 150, h: 105 },
  "Block B": { id: "block-b", name: "Block B", label: "Academic Block B", type: "Electronics & Tech Labs", category_hint: "Electronics & Tech Labs", x: 230, y: 80, w: 150, h: 105 },
  "Block C": { id: "block-c", name: "Block C", label: "Academic Block C", type: "Mechanical & Civil Wings", category_hint: "Mechanical & Civil Wings", x: 410, y: 80, w: 150, h: 105 },
  "Block D": { id: "block-d", name: "Block D", label: "Management Block D", type: "Business & Media Studios", category_hint: "Business & Media Studios", x: 590, y: 80, w: 150, h: 105 },
  "Block E": { id: "block-e", name: "Block E", label: "Science Block E", type: "Biotech & Chemistry", category_hint: "Biotech & Chemistry", x: 50, y: 215, w: 150, h: 105 },
  "Block F": { id: "block-f", name: "Block F", label: "Innovation Block F", type: "AI & Research Center", category_hint: "AI & Research Center", x: 230, y: 215, w: 150, h: 105 },
  "Academic Block": { id: "academic-complex", name: "Academic Complex", label: "Central Academic Complex", type: "Lecture Theatres & Offices", category_hint: "Lecture Theatres & Offices", x: 410, y: 215, w: 150, h: 105 },
  "Hostel": { id: "hostels", name: "Hostel Complex", label: "Campus Hostels Complex", type: "Resident Towers & Mess", category_hint: "Resident Towers & Mess", x: 590, y: 215, w: 150, h: 105 },
  "Library": { id: "library", name: "Central Library", label: "Central Knowledge Library", type: "Reading Halls & Archives", category_hint: "Reading Halls & Archives", x: 50, y: 350, w: 150, h: 100 },
  "Sports": { id: "sports-arena", name: "Sports Arena", label: "Sports Arena & Complex", type: "Gymnasium & Courts", category_hint: "Gymnasium & Courts", x: 230, y: 350, w: 150, h: 100 },
  "Campus": { id: "cafeteria", name: "Campus & Food Plaza", label: "Central Campus & Cafeteria", type: "Food Court & Student Plaza", category_hint: "Food Court & Student Plaza", x: 410, y: 350, w: 150, h: 100 },
  "Other": { id: "utility-grounds", name: "Utility Grounds", label: "University Utility Grounds", type: "Infrastructure & Parking", category_hint: "Infrastructure & Parking", x: 590, y: 350, w: 150, h: 100 }
};

function mapComplaintToZoneKey(block, location, nearbyArea) {
  const b = (block || '').trim().toLowerCase();
  const full = `${block || ''} ${location || ''} ${nearbyArea || ''}`.toLowerCase();

  const exactMap = {
    'block a': 'Block A',
    'block b': 'Block B',
    'block c': 'Block C',
    'block d': 'Block D',
    'block e': 'Block E',
    'block f': 'Block F',
    'hostel': 'Hostel',
    'academic block': 'Academic Block',
    'academic complex': 'Academic Block',
    'library': 'Library',
    'central library': 'Library',
    'sports': 'Sports',
    'sports arena': 'Sports',
    'campus': 'Campus',
    'cafeteria': 'Campus',
    'food plaza': 'Campus'
  };

  if (exactMap[b]) return exactMap[b];
  if (full.includes('block a')) return 'Block A';
  if (full.includes('block b')) return 'Block B';
  if (full.includes('block c')) return 'Block C';
  if (full.includes('block d')) return 'Block D';
  if (full.includes('block e')) return 'Block E';
  if (full.includes('block f')) return 'Block F';
  if (full.includes('library')) return 'Library';
  if (full.includes('hostel')) return 'Hostel';
  if (full.includes('sports') || full.includes('gym') || full.includes('court')) return 'Sports';
  if (full.includes('academic') || full.includes('lecture')) return 'Academic Block';
  if (full.includes('cafeteria') || full.includes('food') || full.includes('plaza') || full.includes('canteen') || full.includes('campus')) return 'Campus';

  return 'Other';
}

export const handler = async (event, context) => {
  const session = getSessionFromEvent(event);
  if (!session.authenticated || session.user.role !== 'admin') {
    return {
      statusCode: 401,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Unauthorized: Admin access required.' })
    };
  }

  const adminDept = session.user.admin_role !== 'Super Admin' ? (session.user.admin_department || '') : '';

  try {
    await initDb();

    let deptFilter = '';
    let params = [];
    if (adminDept) {
      deptFilter = 'WHERE (LOWER(c.department) = LOWER($1) OR LOWER(c.category) = LOWER($1))';
      params = [adminDept];
    }

    // 1. Core KPIs
    const statsSql = `
      SELECT
        COUNT(CASE WHEN is_primary = TRUE OR is_primary IS NULL THEN 1 END) as total,
        COUNT(*) as total_reports,
        COALESCE(SUM(CASE WHEN is_primary = TRUE OR is_primary IS NULL THEN affected_student_count ELSE 0 END), COUNT(*)) as students_affected,
        COUNT(CASE WHEN status IN ('NEW', 'FORWARDED') THEN 1 END) as pending,
        COUNT(CASE WHEN status IN ('IN_PROGRESS', 'REOPENED') THEN 1 END) as in_progress,
        COUNT(CASE WHEN status IN ('FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION') THEN 1 END) as resolved,
        COUNT(CASE WHEN priority = 'High' AND status NOT IN ('FINAL_RESOLVED', 'AWAITING_STUDENT_CONFIRMATION') THEN 1 END) as escalated
      FROM complaints c
      ${deptFilter}
    `;
    const statsRes = await query(statsSql, params);
    const row = statsRes.rows[0] || {};
    const stats = {
      total: parseInt(row.total || 0, 10),
      total_reports: parseInt(row.total_reports || 0, 10),
      students_affected: parseInt(row.students_affected || 0, 10),
      pending: parseInt(row.pending || 0, 10),
      in_progress: parseInt(row.in_progress || 0, 10),
      resolved: parseInt(row.resolved || 0, 10),
      escalated: parseInt(row.escalated || 0, 10)
    };

    // 2. Fetch all complaints for detailed heatmap, pulse & analytics
    const allComplaintsSql = `
      SELECT 
        c.complaint_id, c.ticket_id, c.student_id, c.category, c.description, c.photo_path,
        c.block, c.location, c.floor_no, c.room_no, c.corridor_side, c.nearby_area, c.additional_location,
        c.priority, c.status, c.date, c.last_updated, c.affected_student_count, c.department,
        s.name AS student_name, s.email AS student_email
      FROM complaints c
      LEFT JOIN students s ON c.student_id = s.student_id
      ${deptFilter}
      ORDER BY c.complaint_id DESC
    `;
    const allRes = await query(allComplaintsSql, params);
    const allRows = allRes.rows;

    // 3. Analytics: Category breakdown, Priority, Monthly Trend
    const byCategory = {};
    const byPriority = { High: 0, Medium: 0, Low: 0 };
    for (const r of allRows) {
      const cat = r.category || 'Other';
      byCategory[cat] = (byCategory[cat] || 0) + 1;
      const prio = r.priority || 'Low';
      if (byPriority[prio] !== undefined) byPriority[prio]++;
    }

    const categoriesList = Object.entries(byCategory)
      .map(([category, count]) => ({ category, count }))
      .sort((a, b) => b.count - a.count);

    const prioritiesList = [
      { priority: 'High', count: byPriority.High },
      { priority: 'Medium', count: byPriority.Medium },
      { priority: 'Low', count: byPriority.Low }
    ];

    // 6-Month Volume Trend
    const monthlyTrends = [];
    const now = new Date();
    for (let i = 5; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const prefix = `${y}-${m}`;
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const mLabel = `${monthNames[d.getMonth()]} ${y}`;
      const mCount = allRows.filter(r => (r.date || '').startsWith(prefix)).length;
      monthlyTrends.push({ month: mLabel, count: mCount });
    }

    const resolvedPercentage = stats.total > 0 ? Math.round((stats.resolved / stats.total) * 1000) / 10 : 0;
    const analytics = {
      by_category: byCategory,
      categories: categoriesList,
      by_priority: byPriority,
      priorities: prioritiesList,
      monthly_trends: monthlyTrends,
      total_complaints: stats.total,
      resolved_percentage: resolvedPercentage
    };

    // 4. Campus Pulse Telemetry
    const criticalIssues = allRows.filter(r => r.priority === 'High' && ['NEW', 'FORWARDED', 'IN_PROGRESS', 'REOPENED'].includes(r.status)).length;
    
    // Top Problem Area
    const locCounts = {};
    for (const r of allRows) {
      if (['NEW', 'FORWARDED', 'IN_PROGRESS', 'REOPENED'].includes(r.status)) {
        const loc = r.block || r.location || 'Campus';
        locCounts[loc] = (locCounts[loc] || 0) + 1;
      }
    }
    let topProblemArea = 'All Zones Normal';
    let topAreaCount = 0;
    for (const [loc, cnt] of Object.entries(locCounts)) {
      if (cnt > topAreaCount) {
        topAreaCount = cnt;
        topProblemArea = `${loc} (${cnt} complaints)`;
      }
    }

    // 7-day velocity
    const velocity7d = [];
    for (let i = 6; i >= 0; i--) {
      const dayDt = new Date(Date.now() - i * 86400000);
      const dayStr = dayDt.toISOString().split('T')[0];
      const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const dayLabel = dayNames[dayDt.getDay()];
      const dayCount = allRows.filter(r => (r.date || '') === dayStr).length;
      velocity7d.push({
        day_name: dayLabel,
        day: dayLabel,
        date: dayStr,
        count: dayCount,
        filed: dayCount
      });
    }

    const pulseData = {
      critical_issues: criticalIssues,
      top_problem_area: topProblemArea,
      resolution_rate: resolvedPercentage,
      active_complaints: stats.pending + stats.in_progress,
      pending_complaints: stats.pending,
      in_progress_complaints: stats.in_progress,
      resolved_complaints: stats.resolved,
      total_complaints: stats.total,
      escalated_count: stats.escalated,
      avg_resolution_days: '1.5',
      status_breakdown: {
        Pending: stats.pending,
        'In Progress': stats.in_progress,
        Resolved: stats.resolved
      },
      velocity_7d: velocity7d
    };

    // 5. Heatmap Zone Data
    const zoneStats = {};
    const categoryCounter = {};
    for (const [z, conf] of Object.entries(ZONES_CONFIG)) {
      zoneStats[z] = {
        id: conf.id,
        zone_key: z,
        name: conf.name,
        label: conf.label,
        type: conf.type,
        category_hint: conf.category_hint,
        x: conf.x,
        y: conf.y,
        w: conf.w,
        h: conf.h,
        total: 0,
        total_complaints: 0,
        pending: 0,
        in_progress: 0,
        resolved: 0,
        resolved_count: 0,
        active: 0,
        unresolved_count: 0,
        high_priority: 0,
        high_priority_count: 0,
        high_priority_active: 0,
        medium_priority_count: 0,
        low_priority_count: 0,
        top_category: 'None Recorded',
        intensity: 'Low',
        intensity_label: 'Clear / Low Load',
        intensity_color: '#10B981',
        complaints: []
      };
      categoryCounter[z] = {};
    }

    for (const r of allRows) {
      const matchedZone = mapComplaintToZoneKey(r.block, r.location, r.nearby_area);
      const zData = zoneStats[matchedZone] || zoneStats['Other'];
      zData.total++;
      zData.total_complaints++;

      const status = r.status || 'NEW';
      const prio = r.priority || 'Low';
      const cat = r.category || 'General';

      categoryCounter[matchedZone][cat] = (categoryCounter[matchedZone][cat] || 0) + 1;

      if (['NEW', 'FORWARDED'].includes(status)) {
        zData.pending++;
        zData.active++;
        zData.unresolved_count++;
      } else if (['IN_PROGRESS', 'REOPENED'].includes(status)) {
        zData.in_progress++;
        zData.active++;
        zData.unresolved_count++;
      } else {
        zData.resolved++;
        zData.resolved_count++;
      }

      if (prio === 'High') {
        zData.high_priority++;
        zData.high_priority_count++;
        if (['NEW', 'FORWARDED', 'IN_PROGRESS', 'REOPENED'].includes(status)) {
          zData.high_priority_active++;
        }
      } else if (prio === 'Medium') {
        zData.medium_priority_count++;
      } else {
        zData.low_priority_count++;
      }

      const ticketId = r.ticket_id || formatTicketId(r.complaint_id, r.date);
      const desc = r.description || '';
      const shortDesc = desc.length > 85 ? desc.slice(0, 85) + '...' : desc;

      zData.complaints.push({
        complaint_id: r.complaint_id,
        ticket_id: ticketId,
        student_id: r.student_id,
        student_name: r.student_name || `Student #${r.student_id}`,
        student_email: r.student_email || '',
        category: cat,
        description: desc,
        short_description: shortDesc,
        location: r.location || r.block || 'Campus',
        block: r.block || '',
        floor_no: r.floor_no || '',
        room_no: r.room_no || '',
        corridor_side: r.corridor_side || '',
        priority: prio,
        status: status,
        date: r.date || '',
        date_formatted: r.date || '',
        photo_path: r.photo_path || '',
        has_photo: Boolean(r.photo_path && String(r.photo_path).trim())
      });
    }

    for (const [z, data] of Object.entries(zoneStats)) {
      const act = data.active;
      const hpAct = data.high_priority_active;
      const catMap = categoryCounter[z] || {};
      const catKeys = Object.keys(catMap);
      if (catKeys.length > 0) {
        data.top_category = catKeys.reduce((a, b) => (catMap[a] > catMap[b] ? a : b));
      }

      if (act >= 5 || hpAct >= 2) {
        data.intensity = 'Critical';
        data.intensity_label = 'Critical Action Required';
        data.intensity_color = '#EF4444';
      } else if (act >= 3 || hpAct >= 1) {
        data.intensity = 'High';
        data.intensity_label = 'High Attention';
        data.intensity_color = '#F97316';
      } else if (act >= 1) {
        data.intensity = 'Moderate';
        data.intensity_label = 'Moderate Activity';
        data.intensity_color = '#06B6D4';
      } else {
        data.intensity = 'Low';
        data.intensity_label = 'Clear / Low Load';
        data.intensity_color = '#10B981';
      }
    }

    const heatmapData = Object.values(zoneStats);

    // 6. Transport stats
    const transportStats = {
      total: allRows.filter(r => r.category === 'Transport Complaint').length,
      pending: allRows.filter(r => r.category === 'Transport Complaint' && ['NEW', 'FORWARDED'].includes(r.status)).length,
      in_progress: allRows.filter(r => r.category === 'Transport Complaint' && ['IN_PROGRESS', 'REOPENED'].includes(r.status)).length,
      resolved: allRows.filter(r => r.category === 'Transport Complaint' && ['FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION'].includes(r.status)).length,
      by_route: [],
      by_type: []
    };

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: true,
        data: {
          stats,
          analytics,
          pulse_data: pulseData,
          heatmap_data: heatmapData,
          transport_stats: transportStats,
          department: adminDept
        }
      })
    };
  } catch (err) {
    console.error('[admin-stats] Error:', err);
    return {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ success: false, error: 'Database error fetching admin stats.' })
    };
  }
};
