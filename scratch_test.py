import database
groups = database.get_grouped_admin_issues()
for g in groups:
    print(f"Group: {g['category']} {g['block']} {g.get('room_no')} - {g['complaint_count']} complaints, {g['affected_students']} students")
    for c in g['complaints']:
        print(f"  Ticket: {c['ticket_id']}, Student: {c['student_name']} (ID: {c['student_id']}), Desc: {c['description']}")
