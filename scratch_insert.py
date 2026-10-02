import sqlite3
from database import DB_PATH
conn = sqlite3.connect(DB_PATH)
conn.execute("INSERT INTO complaints (student_id, category, description, location, priority, status, date) VALUES (1, 'Cleaning', 'Test', 'Hostel', 'Low', 'NEW', '2026-10-02')")
conn.commit()
conn.close()
