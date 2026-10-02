import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import database
import json

conn = database.get_db_connection()
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print('Tables in DB:', tables)

# Inspect complaints and students
cursor.execute("""
    SELECT c.complaint_id, c.ticket_id, c.student_id, c.category, c.status, c.date,
           s.name as student_name, s.email as student_email
    FROM complaints c
    LEFT JOIN students s ON c.student_id = s.student_id
""")
complaints = [dict(r) for r in cursor.fetchall()]
print(f'Total complaints: {len(complaints)}')
for comp in complaints:
    print(comp)

# Also check students table
cursor.execute("SELECT student_id, name, email FROM students")
students = [dict(r) for r in cursor.fetchall()]
print(f'\nTotal students: {len(students)}')
for st in students:
    print(st)

# Also check complaint_reporters table
if 'complaint_reporters' in tables:
    cursor.execute("SELECT * FROM complaint_reporters")
    reporters = [dict(r) for r in cursor.fetchall()]
    print(f'\nTotal reporters: {len(reporters)}')
    for rep in reporters:
        print(rep)

conn.close()
