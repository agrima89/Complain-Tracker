import sys

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = 'def get_related_complaints(complaint_id):'
start_idx = content.find(start_marker)

if start_idx == -1:
    print("Could not find get_related_complaints")
    sys.exit(1)

new_func = '''def get_related_complaints(complaint_id):
    conn = get_db_connection()
    
    # Get target complaint
    target_comp = conn.execute(
        """
        SELECT complaints.*
        FROM complaints 
        WHERE complaint_id = ?
        """, 
        (complaint_id,)
    ).fetchone()
    
    if not target_comp:
        conn.close()
        return None
        
    target = dict(target_comp)
    is_transport = target.get('category') == 'Transport Complaint'
    
    # Get all reporters for this complaint
    reporters = conn.execute(
        """
        SELECT complaint_reporters.*, students.name AS student_name, students.email AS student_email
        FROM complaint_reporters
        JOIN students ON complaint_reporters.student_id = students.student_id
        WHERE complaint_id = ?
        ORDER BY reported_at DESC
        """, (complaint_id,)
    ).fetchall()
    
    conn.close()
    
    related = []
    unique_students = set()
    
    # In the new merged paradigm, every reporter row is effectively a "complaint submission" mapped to this master ticket
    # To keep the UI compatible with the modal (which expects a ticket_id and student_name for each item),
    # we yield pseudo-records representing each reporter's submission, sharing the master ticket_id.
    
    for row in reporters:
        r = dict(row)
        c = {
            'complaint_id': complaint_id,
            'ticket_id': target.get('ticket_id') or format_ticket_id(complaint_id, target.get('date')),
            'student_name': r.get('student_name'),
            'student_id': r.get('student_id')
        }
        related.append(c)
        unique_students.add(r['student_id'])
            
    return {
        'related_complaints': related,
        'report_count': len(related),
        'affected_student_count': len(unique_students),
        'category': target.get('category', ''),
        'location': f"{target.get('block', '')} • {target.get('floor_no', '')} • {target.get('room_no', '')}" if not is_transport else f"Bus {target.get('bus_number', '')} • Route {target.get('route', '')}",
        'issue': target.get('description', '')
    }
'''

content = content[:start_idx] + new_func

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched get_related_complaints in database.py")
