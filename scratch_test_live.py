import requests
import re
import sqlite3

s = requests.Session()
login_url = "http://127.0.0.1:5000/login"
r = s.get(login_url)
csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)

# Ensure student 2 exists, password is password
conn = sqlite3.connect("database.db")
cur = conn.cursor()
cur.execute("INSERT OR IGNORE INTO students (student_id, name, email, password) VALUES (2, 'Test2', 'test2@culkomail.in', 'password')")
conn.commit()

login_data = {
    "email": "test2@culkomail.in",
    "password": "password",
    "csrf_token": csrf_token
}
r = s.post(login_url, data=login_data)
print("Login status:", r.status_code)

cur.execute("INSERT INTO complaints (student_id, ticket_id, category, description, location, priority, status, date) VALUES (2, 'CC-999', 'Cleaning', 'Test', 'Hostel', 'Low', 'NEW', '2026-10-02')")
conn.commit()
comp_id = cur.lastrowid
cur.execute("INSERT INTO complaint_reporters (complaint_id, student_id, reported_at) VALUES (?, 2, '2026-10-02')", (comp_id,))
conn.commit()
conn.close()

dash_url = "http://127.0.0.1:5000/student/dashboard"
r = s.get(dash_url)
csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)

delete_url = f"http://127.0.0.1:5000/student/complaint/{comp_id}/delete"
print("Deleting URL:", delete_url)
r = s.post(delete_url, data={"csrf_token": csrf_token})
print("Delete status:", r.status_code)
print("Response text:", r.text[:300])

