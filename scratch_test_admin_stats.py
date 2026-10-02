import database

# Ensure students exist
conn = database.get_db_connection()
students = ['Student_A', 'Student_B']
for s in students:
    try:
        conn.execute("INSERT INTO students (student_id, name, email, password, gender, hostel, room_no, course, admission_year, registered_at) VALUES (?, ?, ?, 'pass', 'M', 'H1', '101', 'BTech', '2023', '2023-01-01')", (s, f"{s} Name", f"{s}@test.com"))
    except:
        pass
conn.commit()
conn.close()

print('Inserting Complaint 1 (Student A)...')
database.submit_or_attach_complaint('Student_A', 'Electrical', 'fan is not working', block='Block E', floor_no='3rd Floor', room_no='323', corridor_side='RHS')

print('Inserting Complaint 2 (Student B) for the same issue...')
database.submit_or_attach_complaint('Student_B', 'Electrical', 'Fan is not working', block='Block E', floor_no='3rd Floor', room_no='323', corridor_side='RHS')

print('\nCalculating stats...')
stats = database.get_admin_statistics()
print(f'Actual complaint records found: {stats["total"]}')
print(f'Unique grievances: {stats["unique_complaints"]}')
print(f'Student Reports: {stats["total_reports"]}')
print(f'Unique students (affected): {stats["students_affected"]}')
print('Status counts:')
print(f'  NEW/PENDING: {stats["pending"]}')
print(f'  IN_PROGRESS: {stats["in_progress"]}')
print(f'  RESOLVED: {stats["resolved"]}')

# Print the actual database records just for proof
conn = database.get_db_connection()
conn.row_factory = __import__('sqlite3').Row
complaints = conn.execute('SELECT ticket_id, is_primary FROM complaints').fetchall()
print('\nComplaint records in DB:')
for c in complaints:
    print(f'Ticket: {c["ticket_id"]}, Primary: {c["is_primary"]}')
conn.close()
