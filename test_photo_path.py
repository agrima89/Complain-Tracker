import database
from datetime import date
import sqlite3

# Submit a test complaint with a fake photo path
res = database.submit_or_attach_complaint(
    student_id=1,
    category="Test Category",
    description="This is a test description for photo path",
    photo_path="uploads/complaints/test_photo.jpg",
    block="Block A",
    priority="Medium",
    date_str=str(date.today())
)
print("Result:", res)

# Check DB
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("SELECT complaint_id, photo_path, description FROM complaints ORDER BY complaint_id DESC LIMIT 1")
print("DB Record:", cursor.fetchone())
conn.close()
