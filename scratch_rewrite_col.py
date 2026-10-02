import sys

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = 'def get_complaint_collections():'
end_marker = 'def get_complaint_by_id(complaint_id):'
start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print('Failed to find markers')
    sys.exit(1)

new_func = '''def get_complaint_collections():
    conn = get_db_connection()
    # Fetch all master complaints
    query_sql = """
        SELECT
            complaints.*,
            students.name AS student_name,
            students.email AS student_email
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        WHERE complaints.is_primary = 1 OR complaints.group_id IS NULL
        ORDER BY complaints.complaint_id DESC
    """
    complaints_raw = conn.execute(query_sql).fetchall()
    
    collections = []
    
    summary = {
        'total_issues': 0,
        'affected_students': 0,
        'open_issues': 0,
        'in_progress': 0,
        'resolved': 0
    }
    
    for row in complaints_raw:
        c = dict(row)
        c['ticket_id'] = c.get('ticket_id') or format_ticket_id(c['complaint_id'], c['date'])
        
        # In the new paradigm, each collection is just a 1-to-1 mapping with a master complaint.
        reporters = conn.execute(
            "SELECT student_id, student_email, reported_at FROM complaint_reporters WHERE complaint_id = ?",
            (c['complaint_id'],)
        ).fetchall()
        
        is_transport = c.get('category') == 'Transport Complaint'
        location_str = f"{c.get('block', '')} • {c.get('floor_no', '')} • {c.get('room_no', '')}" if not is_transport else f"Bus {c.get('bus_number', '')} • Route {c.get('route', '')}"
        
        status_counts = {'NEW': 0, 'IN_PROGRESS': 0, 'RESOLVED': 0}
        s = c['status']
        # The user requested mapping:
        # NEW, FORWARDED, RESOLUTION_SUBMITTED, AWAITING_STUDENT_CONFIRMATION -> Pending (NEW)
        # IN_PROGRESS, REOPENED -> In Progress
        # FINAL_RESOLVED -> Resolved
        if s in ('NEW', 'FORWARDED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION'):
            status_counts['NEW'] = 1
            summary['open_issues'] += 1
        elif s in ('IN_PROGRESS', 'REOPENED'):
            status_counts['IN_PROGRESS'] = 1
            summary['in_progress'] += 1
        elif s == 'FINAL_RESOLVED':
            status_counts['RESOLVED'] = 1
            summary['resolved'] += 1
            
        student_count = c.get('affected_student_count', 1)
        summary['affected_students'] += student_count
        summary['total_issues'] += 1
        
        # Build pseudo-complaints for the UI modal so it can display the list of reporters
        pseudo_complaints = []
        for r in reporters:
            pc = dict(c) # copy master
            pc['student_id'] = r['student_id']
            pc['student_email'] = r['student_email']
            # Try to get the student's name
            student_row = conn.execute("SELECT name FROM students WHERE student_id = ?", (r['student_id'],)).fetchone()
            if student_row:
                pc['student_name'] = student_row['name']
            pseudo_complaints.append(pc)
            
        if not pseudo_complaints:
            pseudo_complaints = [c] # Failsafe
            
        col = {
            'collection_id': f"COL-{c['complaint_id']:04d}",
            'issue': c.get('description', ''),
            'representative_description': c.get('description', ''),
            'category': c.get('category', ''),
            'location': location_str,
            'block': c.get('block', ''),
            'floor_no': c.get('floor_no', ''),
            'room_no': c.get('room_no', ''),
            'bus_number': c.get('bus_number', ''),
            'route': c.get('route', ''),
            'pickup_drop_point': c.get('pickup_drop_point', ''),
            'priority': c.get('priority', 'Low'),
            'student_count': student_count,
            'report_count': student_count,
            'complaints': pseudo_complaints,
            'status_counts': status_counts,
            'status': c['status'] # Important: direct master status!
        }
        collections.append(col)
        
    conn.close()
    return collections, summary
'''

content = content[:start_idx] + new_func + '\n' + content[end_idx:]

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched get_complaint_collections!')
