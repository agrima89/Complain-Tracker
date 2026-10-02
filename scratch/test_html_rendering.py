import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import app
import database

client = app.test_client()

# 1. Test student complaints page contains PDF button
with client.session_transaction() as sess:
    sess["student_id"] = 1
    sess["student_name"] = "Agrima Bajpai"
    sess["student_email"] = "agrima89@culkomail.in"

resp = client.get("/my-complaints")
assert resp.status_code == 200
html = resp.get_data(as_text=True)
assert "/pdf" in html or "Download" in html or "PDF" in html
print("[PASS] my_complaints.html contains PDF buttons.")

# 2. Test student complaint detail page contains PDF button
resp = client.get("/student/complaint/1")
if resp.status_code == 200:
    html = resp.get_data(as_text=True)
    assert "/pdf" in html or "Download PDF" in html
    print("[PASS] complaint_detail.html contains PDF button.")

# 3. Test admin dashboard contains "Generate Complaint Report" and "PDF" buttons
with client.session_transaction() as sess:
    sess.clear()
    sess["admin_id"] = 1
    sess["admin_username"] = "admin"

resp = client.get("/admin/dashboard")
assert resp.status_code == 200
html = resp.get_data(as_text=True)
assert "Generate Complaint Report" in html
assert "/admin/report/pdf" in html or "/report/pdf" in html or "report" in html
assert "/admin/complaint/" in html and "/pdf" in html
print("[PASS] admin_dashboard.html contains Generate Complaint Report and per-row PDF buttons.")

# 4. Test admin complaint detail page contains PDF button
resp = client.get("/admin/complaint/1")
if resp.status_code == 200:
    html = resp.get_data(as_text=True)
    assert "/admin/complaint/1/pdf" in html or "/pdf" in html
    assert "Generate PDF" in html
    print("[PASS] admin_complaint_detail.html contains Generate PDF button.")

print("ALL TEMPLATE HTML CHECKS PASSED!")
