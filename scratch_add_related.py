import sys

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

helper_code = '''
def get_related_complaints(complaint_id):
    conn = get_db_connection()
    
    # Get target complaint
    target_comp = conn.execute(
        """
        SELECT complaints.*, students.name AS student_name, students.email AS student_email
        FROM complaints 
        JOIN students ON complaints.student_id = students.student_id
        WHERE complaint_id = ?
        """, 
        (complaint_id,)
    ).fetchone()
    
    if not target_comp:
        conn.close()
        return None
        
    target = dict(target_comp)
    is_transport = target.get('category') == 'Transport Complaint'
    
    # Base query for same category
    query_sql = """
        SELECT complaints.*, students.name AS student_name, students.email AS student_email
        FROM complaints 
        JOIN students ON complaints.student_id = students.student_id
        WHERE complaints.category = ?
        ORDER BY complaints.complaint_id DESC
    """
    all_comps = conn.execute(query_sql, (target.get('category'),)).fetchall()
    conn.close()
    
    related = []
    unique_students = set()
    
    for row in all_comps:
        c = dict(row)
        
        # Location matching
        if is_transport:
            if c.get('bus_number') != target.get('bus_number') or \\
               c.get('route') != target.get('route') or \\
               c.get('pickup_drop_point') != target.get('pickup_drop_point'):
                continue
        else:
            if c.get('block') != target.get('block') or \\
               c.get('floor_no') != target.get('floor_no') or \\
               c.get('room_no') != target.get('room_no'):
                continue
                
        # Issue similarity matching
        if is_similar_issue(c.get('description', ''), target.get('description', ''), target.get('room_no', '')):
            c['ticket_id'] = c.get('ticket_id') or format_ticket_id(c['complaint_id'], c['date'])
            related.append(c)
            unique_students.add(c['student_id'])
            
    return {
        'related_complaints': related,
        'report_count': len(related),
        'affected_student_count': len(unique_students),
        'category': target.get('category', ''),
        'location': f"{target.get('block', '')} • {target.get('floor_no', '')} • {target.get('room_no', '')}" if not is_transport else f"Bus {target.get('bus_number', '')} • Route {target.get('route', '')}",
        'issue': target.get('description', '')
    }
'''

if 'def get_related_complaints' not in content:
    content += '\n' + helper_code
    with open('database.py', 'w', encoding='utf-8') as f:
        f.write(content)
