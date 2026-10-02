
def get_grouped_admin_issues():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT c.*, s.name AS student_name, s.email AS student_email 
        FROM complaints c 
        LEFT JOIN students s ON c.student_id = s.student_id
        ORDER BY c.complaint_id ASC
    """).fetchall()
    conn.close()

    groups = []
    
    for row in rows:
        c = dict(row)
        c['ticket_id'] = c.get('ticket_id') or format_ticket_id(c['complaint_id'], c['date'])
        
        is_transport = c.get('category') == 'Transport Complaint'
        
        found_group = False
        for g in groups:
            if g['category'] != c.get('category'):
                continue
                
            if is_transport:
                if g.get('bus_number') != c.get('bus_number') or \
                   g.get('route') != c.get('route') or \
                   g.get('pickup_drop_point') != c.get('pickup_drop_point') or \
                   g.get('transport_complaint_type') != c.get('transport_complaint_type'):
                    continue
            else:
                if g.get('block') != c.get('block') or \
                   g.get('floor_no') != c.get('floor_no') or \
                   g.get('room_no') != c.get('room_no'):
                    continue
            
            if is_similar_issue(c.get('description', ''), g['representative_description'], c.get('room_no', '')):
                g['complaints'].append(c)
                g['complaint_count'] += 1
                g['affected_students'] = len(set([comp['student_id'] for comp in g['complaints']]))
                found_group = True
                break
                
        if not found_group:
            new_group = {
                'group_id': c['complaint_id'],
                'category': c.get('category'),
                'block': c.get('block'),
                'floor_no': c.get('floor_no'),
                'room_no': c.get('room_no'),
                'bus_number': c.get('bus_number'),
                'route': c.get('route'),
                'pickup_drop_point': c.get('pickup_drop_point'),
                'transport_complaint_type': c.get('transport_complaint_type'),
                'representative_description': c.get('description', ''),
                'complaint_count': 1,
                'affected_students': 1,
                'complaints': [c]
            }
            groups.append(new_group)
            
    groups.sort(key=lambda x: max(comp['complaint_id'] for comp in x['complaints']), reverse=True)
    return groups
