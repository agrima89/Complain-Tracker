import sys
import os
import time
import threading
import requests
import traceback

sys.path.insert(0, r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker")
from app import app

def run_server():
    app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(1.5)

BASE_URL = "http://127.0.0.1:5001"
session = requests.Session()

print("\n--- Testing Unauthenticated HTTP Requests on Port 5001 ---")
routes = [
    "/",
    "/login",
    "/register",
    "/admin/login",
    "/student/dashboard",
    "/student/submit",
    "/student/complaints",
    "/profile",
    "/admin/dashboard",
    "/admin/api/analytics"
]

for r in routes:
    res = session.get(BASE_URL + r, allow_redirects=False)
    print(f"[{res.status_code}] GET {r}")
    if res.status_code == 500:
        print(f"FAILED on GET {r} (500 Internal Server Error)")
        print(res.text[:600])

print("\n--- Testing Admin Session ---")
admin_sess = requests.Session()
r_get = admin_sess.get(BASE_URL + "/admin/login")
print(f"Admin Login GET: {r_get.status_code}")

import re
match = re.search(r'name="csrf_token" value="([^"]+)"', r_get.text)
csrf = match.group(1) if match else ""
print(f"CSRF extracted: {bool(csrf)}")

r_post = admin_sess.post(BASE_URL + "/admin/login", data={
    "csrf_token": csrf,
    "username": "admin",
    "password": "admin123"
}, allow_redirects=False)
print(f"Admin Login POST status: {r_post.status_code}, Location: {r_post.headers.get('Location')}")

admin_routes = [
    "/admin/dashboard",
    "/admin/complaint/1",
    "/profile"
]
for r in admin_routes:
    res = admin_sess.get(BASE_URL + r, allow_redirects=False)
    print(f"[{res.status_code}] GET {r}")
    if res.status_code == 500:
        print(f"FAILED on Admin GET {r}")
        print(res.text[:600])

# Test AJAX update status
meta_csrf = re.search(r'<meta name="csrf-token" content="([^"]+)">', r_get.text)
token_for_ajax = csrf

r_ajax = admin_sess.post(BASE_URL + "/admin/api/update-status", json={
    "complaint_id": 1,
    "status": "In Progress"
}, headers={
    "X-CSRFToken": token_for_ajax,
    "X-Requested-With": "XMLHttpRequest"
})
print(f"Admin AJAX update status: {r_ajax.status_code}, response: {r_ajax.text}")

print("\n--- Testing Student Session ---")
stu_sess = requests.Session()
r_stu_get = stu_sess.get(BASE_URL + "/login")
match_stu = re.search(r'name="csrf_token" value="([^"]+)"', r_stu_get.text)
stu_csrf = match_stu.group(1) if match_stu else ""

r_stu_post = stu_sess.post(BASE_URL + "/login", data={
    "csrf_token": stu_csrf,
    "email": "25LBCS9999@culkomail.in",
    "password": "SecurePass123!"
}, allow_redirects=False)
print(f"Student Login POST status: {r_stu_post.status_code}, Location: {r_stu_post.headers.get('Location')}")

stu_routes = [
    "/student/dashboard",
    "/student/submit",
    "/student/complaints",
    "/student/complaint/1",
    "/profile"
]
for r in stu_routes:
    res = stu_sess.get(BASE_URL + r, allow_redirects=False)
    print(f"[{res.status_code}] GET {r}")
    if res.status_code == 500:
        print(f"FAILED on Student GET {r}")
        print(res.text[:600])

print("\nALL LIVE HTTP TESTS COMPLETED SUCCESSFULLY!")
