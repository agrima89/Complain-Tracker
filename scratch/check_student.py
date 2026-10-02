import sqlite3
import os

db_path = r'c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\database.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

email = '25LBCS3099@culkomail.in'
cursor.execute("SELECT * FROM students WHERE LOWER(email) = LOWER(?)", (email,))
student = cursor.fetchone()

if student:
    print(f"STUDENT FOUND: ID={student['student_id']}, Name={student['name']}, Email={student['email']}")
    cursor.execute("SELECT COUNT(*) as cnt FROM complaints WHERE student_id = ?", (student['student_id'],))
    complaints = cursor.fetchone()
    print(f"COMPLAINTS COUNT: {complaints['cnt']}")
else:
    print("STUDENT NOT FOUND")

# Also let's check schema for complaints
cursor.execute("PRAGMA table_info(complaints)")
cols = cursor.fetchall()
# print([dict(c) for c in cols])
