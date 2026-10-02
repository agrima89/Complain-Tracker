import sys
import re

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('def get_all_complaints_admin_paginated(')
end_idx = content.find('def get_complaint_by_id(', start_idx)

new_func = '''def get_all_complaints_admin_paginated(
    status_filter="All",
    priority_filter="All",
    search_text="",
    escalated_only=False,
    page=1,
    per_page=10,
    department=None
):
    conn = get_db_connection()
    base_where = "WHERE 1=1"
    params = []

    if department:
        base_where += " AND complaints.department = ?"
        params.append(department)

    if status_filter and status_filter != "All":
        base_where += " AND complaints.status = ?"
        params.append(status_filter)

    if priority_filter and priority_filter != "All":
        base_where += " AND complaints.priority = ?"
        params.append(priority_filter)

    if search_text and search_text.strip():
        s = f"%{search_text.strip()}%"
        base_where += """
            AND (
                complaints.ticket_id LIKE ?
                OR students.name LIKE ?
                OR students.email LIKE ?
                OR complaints.category LIKE ?
                OR complaints.description LIKE ?
                OR complaints.location LIKE ?
                OR complaints.block LIKE ?
                OR complaints.room_no LIKE ?
                OR complaints.nearby_area LIKE ?
                OR CAST(complaints.complaint_id AS TEXT) LIKE ?
            )
        """
        params.extend([s, s, s, s, s, s, s, s, s, s])

    if escalated_only:
        threshold_date = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d")
        threshold_dt = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
        base_where += " AND complaints.priority = 'High' AND complaints.status != 'FINAL_RESOLVED'"
        base_where += " AND (complaints.date < ? OR (complaints.last_updated != '' AND complaints.last_updated < ?))"
        params.extend([threshold_date, threshold_dt])

    count_sql = f"""
        SELECT COUNT(*)
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        {base_where}
    """
    total_count = conn.execute(count_sql, params).fetchone()[0]

    page = max(1, int(page))
    per_page = max(1, min(int(per_page), 50))
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    query_sql = f"""
        SELECT
            complaints.*,
            students.name AS student_name,
            students.email AS student_email
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        {base_where}
        ORDER BY complaints.complaint_id DESC
        LIMIT ? OFFSET ?
    """
    query_params = list(params) + [per_page, offset]
    complaints_raw = conn.execute(query_sql, query_params).fetchall()
    conn.close()

    return {
        "items": [dict(r) for r in complaints_raw],
        "total": total_count,
        "total_items": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    }

def get_complaint_collections():
    conn = get_db_connection()
    query_sql = """
        SELECT
            complaints.*,
            students.name AS student_name,
            students.email AS student_email
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        ORDER BY complaints.complaint_id DESC
    """
    complaints_raw = conn.execute(query_sql).fetchall()
    conn.close()

    collections = []
    
    priority_rank = {"High": 3, "Medium": 2, "Low": 1, "": 0}
    
    for row in complaints_raw:
        c = dict(row)
        c['ticket_id'] = c.get('ticket_id') or format_ticket_id(c['complaint_id'], c['date'])
        
        is_transport = c.get('category') == 'Transport Complaint'
        
        found_col = False
        for col in collections:
            if col['category'] != c.get('category'):
                continue
                
            if is_transport:
                if col.get('bus_number') != c.get('bus_number') or \
                   col.get('route') != c.get('route') or \
                   col.get('pickup_drop_point') != c.get('pickup_drop_point'):
                    continue
            else:
                if col.get('block') != c.get('block') or \
                   col.get('floor_no') != c.get('floor_no') or \
                   col.get('room_no') != c.get('room_no'):
                    continue
            
            if is_similar_issue(c.get('description', ''), col['representative_description'], c.get('room_no', '')):
                col['complaints'].append(c)
                col['report_count'] += 1
                
                # Status
                if c['status'] in ('NEW', 'FORWARDED', 'REOPENED'):
                    col['status_counts']['NEW'] += 1
                elif c['status'] in ('IN_PROGRESS', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION'):
                    col['status_counts']['IN_PROGRESS'] += 1
                elif c['status'] == 'FINAL_RESOLVED':
                    col['status_counts']['RESOLVED'] += 1
                    
                # Priority
                c_rank = priority_rank.get(c.get('priority', 'Low'), 0)
                col_rank = priority_rank.get(col.get('priority', 'Low'), 0)
                if c_rank > col_rank:
                    col['priority'] = c.get('priority', 'High')
                
                # Unique students
                existing_students = set([comp['student_id'] for comp in col['complaints']])
                col['student_count'] = len(existing_students)
                found_col = True
                break
                
        if not found_col:
            col = {
                'collection_id': f"COL-{c['complaint_id']:04d}",
                'issue': c.get('description', ''),
                'representative_description': c.get('description', ''),
                'category': c.get('category', ''),
                'location': f"{c.get('block', '')} • {c.get('floor_no', '')} • {c.get('room_no', '')}" if not is_transport else f"Bus {c.get('bus_number', '')} • Route {c.get('route', '')}",
                'block': c.get('block', ''),
                'floor_no': c.get('floor_no', ''),
                'room_no': c.get('room_no', ''),
                'bus_number': c.get('bus_number', ''),
                'route': c.get('route', ''),
                'pickup_drop_point': c.get('pickup_drop_point', ''),
                'priority': c.get('priority', 'Low'),
                'student_count': 1,
                'report_count': 1,
                'complaints': [c],
                'status_counts': {'NEW': 0, 'IN_PROGRESS': 0, 'RESOLVED': 0}
            }
            if c['status'] in ('NEW', 'FORWARDED', 'REOPENED'):
                col['status_counts']['NEW'] = 1
            elif c['status'] in ('IN_PROGRESS', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION'):
                col['status_counts']['IN_PROGRESS'] = 1
            elif c['status'] == 'FINAL_RESOLVED':
                col['status_counts']['RESOLVED'] = 1
                
            collections.append(col)
            
    summary = {
        'total_issues': len(collections),
        'affected_students': 0,
        'open_issues': 0,
        'in_progress': 0,
        'resolved': 0
    }
    
    for col in collections:
        summary['affected_students'] += col['student_count']
        
        if col['status_counts']['NEW'] == col['report_count']:
            col['status'] = 'NEW'
            summary['open_issues'] += 1
        elif col['status_counts']['RESOLVED'] == col['report_count']:
            col['status'] = 'RESOLVED'
            summary['resolved'] += 1
        else:
            col['status'] = 'IN_PROGRESS'
            summary['in_progress'] += 1
            
    return collections, summary

'''

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_func + content[end_idx:]
    with open('database.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Database updated!")
else:
    print("Could not find replacement indices.")
