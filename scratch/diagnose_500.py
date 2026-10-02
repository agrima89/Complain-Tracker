import sys
import os
import requests
import re
import sqlite3

BASE_URL = "http://127.0.0.1:5000"

print("=" * 60)
print("TESTING ALL ROUTES ON LIVE SERVER http://127.0.0.1:5000")
print("=" * 60)

session = requests.Session()

# 1. Public unauthenticated routes
public_routes = [
    ("GET", "/", None),
    ("GET", "/login", None),
    ("GET", "/register", None),
    ("GET", "/admin/login", None),
    ("GET", "/student/dashboard", None),  # Redirects to /login (302)
    ("GET", "/student/submit", None),     # Redirects to /login (302)
    ("GET", "/submit-complaint", None),   # Redirects to /login (302)
    ("GET", "/submit_complaint", None),   # Redirects to /login (302)
    ("GET", "/student/complaints", None), # Redirects to /login (302)
    ("GET", "/my-complaints", None),      # Redirects to /login (302)
    ("GET", "/my_complaints", None),      # Redirects to /login (302)
    ("GET", "/student/complaint/1", None),# Redirects to /login (302)
    ("GET", "/profile", None),            # Redirects to /login (302)
    ("GET", "/admin/dashboard", None),    # Redirects to /admin/login (302)
    ("GET", "/admin/complaint/1", None),  # Redirects to /admin/login (302)
    ("GET", "/admin/api/analytics", None),# Redirects to /admin/login (302)
]

failed = False
for method, path, data in public_routes:
    url = BASE_URL + path
    try:
        r = session.get(url, allow_redirects=False)
        print(f"[{r.status_code}] {method} {path}")
        if r.status_code >= 500:
            print(f"  FAILED: 500 Server Error on {path}")
            print(r.text[:500])
            failed = True
    except Exception as e:
        print(f"[ERR] {method} {path} -> {e}")
        failed = True

# 2. Admin Authentication & Protected Routes
print("\n--- Testing Admin Workflow ---")
admin_sess = requests.Session()
r_admin_get = admin_sess.get(BASE_URL + "/admin/login")
match_admin_csrf = re.search(r'name="csrf_token" value="([^"]+)"', r_admin_get.text)
admin_csrf = match_admin_csrf.group(1) if match_admin_csrf else ""

r_admin_login = admin_sess.post(BASE_URL + "/admin/login", data={
    "csrf_token": admin_csrf,
    "username": "admin",
    "password": "admin123"
}, allow_redirects=False)
print(f"Admin Login POST: {r_admin_login.status_code} -> Location: {r_admin_login.headers.get('Location')}")
if r_admin_login.status_code != 302:
    print("Admin login failed!")
    failed = True

# Test admin routes
admin_pages = [
    "/admin/dashboard",
    "/admin/complaint/1",
    "/admin/api/analytics",
    "/profile"
]
for p in admin_pages:
    r = admin_sess.get(BASE_URL + p, allow_redirects=False)
    print(f"[{r.status_code}] GET {p}")
    if r.status_code >= 500:
        print(f"  FAILED: 500 Server Error on {p}")
        print(r.text[:500])
        failed = True

# Extract dashboard CSRF token for AJAX
r_dash = admin_sess.get(BASE_URL + "/admin/dashboard")
match_dash_csrf = re.search(r'<meta name="csrf-token" content="([^"]+)">', r_dash.text)
dash_csrf = match_dash_csrf.group(1) if match_dash_csrf else admin_csrf

# Test AJAX update status
r_ajax = admin_sess.post(BASE_URL + "/admin/api/update-status", json={
    "complaint_id": 1,
    "status": "In Progress",
    "remarks": "Testing admin status update"
}, headers={
    "X-CSRFToken": dash_csrf,
    "X-Requested-With": "XMLHttpRequest"
})
print(f"[{r_ajax.status_code}] POST /admin/api/update-status: {r_ajax.text[:120]}")
if r_ajax.status_code != 200:
    print("AJAX status update failed!")
    failed = True

# 3. Student Authentication & Protected Routes
print("\n--- Testing Student Workflow ---")
stu_sess = requests.Session()
r_stu_get = stu_sess.get(BASE_URL + "/login")
match_stu_csrf = re.search(r'name="csrf_token" value="([^"]+)"', r_stu_get.text)
stu_csrf = match_stu_csrf.group(1) if match_stu_csrf else ""

r_stu_login = stu_sess.post(BASE_URL + "/login", data={
    "csrf_token": stu_csrf,
    "email": "25LBCS9999@culkomail.in",
    "password": "SecurePass123!"
}, allow_redirects=False)
print(f"Student Login POST: {r_stu_login.status_code} -> Location: {r_stu_login.headers.get('Location')}")
if r_stu_login.status_code != 302:
    print("Student login failed!")
    failed = True

stu_pages = [
    "/student/dashboard",
    "/student/submit",
    "/student/complaints",
    "/my-complaints",
    "/my_complaints",
    "/profile"
]
for p in stu_pages:
    r = stu_sess.get(BASE_URL + p, allow_redirects=False)
    print(f"[{r.status_code}] GET {p}")
    if r.status_code >= 500:
        print(f"  FAILED: 500 Server Error on {p}")
        print(r.text[:500])
        failed = True

if not failed:
    print("\n" + "=" * 60)
    print("ALL ROUTES AND WORKFLOWS PASSED (0 ERRORS, 0 500 RESPONSES)!")
    print("=" * 60)
else:
    print("\nSOME CHECKS FAILED.")
