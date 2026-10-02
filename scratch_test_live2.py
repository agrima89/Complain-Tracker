import requests
import re
import sqlite3

s = requests.Session()
login_url = "http://127.0.0.1:5000/login"
r = s.get(login_url)
csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)

# Ensure student 2 exists
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

# Insert complaint with evidence
cur.execute("INSERT INTO complaints (student_id, ticket_id, category, description, location, priority, status, date, photo_path) VALUES (2, 'CC-888', 'Cleaning', 'Test', 'Hostel', 'Low', 'NEW', '2026-10-02', 'uploads/evidence/test.jpg')")
conn.commit()
comp_id = cur.lastrowid
cur.execute("INSERT INTO complaint_reporters (complaint_id, student_id, reported_at) VALUES (?, 2, '2026-10-02')", (comp_id,))
conn.commit()
conn.close()

dash_url = "http://127.0.0.1:5000/student/dashboard"
r = s.get(dash_url)
csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)

delete_url = f"http://127.0.0.1:5000/student/complaint/{comp_id}/delete"
r = s.post(delete_url, data={"csrf_token": csrf_token}, allow_redirects=False)
print("Delete status (evidence):", r.status_code)
if r.status_code == 500:
    print(r.text[:300])

# Insert grouped complaint
conn = sqlite3.connect("database.db")
cur = conn.cursor()
cur.execute("INSERT INTO complaints (student_id, ticket_id, category, description, location, priority, status, date, affected_student_count) VALUES (2, 'CC-777', 'Cleaning', 'Test Grouped', 'Hostel', 'Low', 'NEW', '2026-10-02', 3)")
conn.commit()
comp_id2 = cur.lastrowid
cur.execute("INSERT INTO complaint_reporters (complaint_id, student_id, reported_at) VALUES (?, 2, '2026-10-02')", (comp_id2,))
conn.commit()
conn.close()

r = s.get(dash_url)
csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', r.text).group(1)

delete_url2 = f"http://127.0.0.1:5000/student/complaint/{comp_id2}/delete"
r = s.post(delete_url2, data={"csrf_token": csrf_token}, allow_redirects=False)
print("Delete status (grouped):", r.status_code)
if r.status_code == 500:
    print(r.text[:300])
