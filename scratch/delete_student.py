import sqlite3
import os

db_path = 'database.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get student IDs
    cursor.execute("SELECT student_id, name, email FROM students WHERE name LIKE '%agrima bajpai%';")
    students = cursor.fetchall()
    
    for student in students:
        s_id = student[0]
        print(f"Deleting student {student[1]} ({student[2]}) ID: {s_id}")
        
        # We'll just delete from students for now
        cursor.execute("DELETE FROM students WHERE student_id = ?;", (s_id,))
    
    conn.commit()
    conn.close()
    print("Done")
else:
    print("No DB")
