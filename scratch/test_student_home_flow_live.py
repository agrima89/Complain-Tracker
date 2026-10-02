import requests
import re
import sys

BASE_URL = "http://127.0.0.1:5000"

print("=" * 60)
print("TESTING COMPLETE STUDENT HOME NAVIGATION FLOW (LIVE SERVER)")
print("=" * 60)

session = requests.Session()

# TEST 1: Open website -> Home works
print("\n[TEST 1] Visiting Home Page as Visitor...")
r1 = session.get(BASE_URL + "/", allow_redirects=False)
assert r1.status_code == 200, f"Expected 200 on Home, got {r1.status_code}"
assert "CampusCare" in r1.text
assert "Student Login" in r1.text
print("  [OK] TEST 1 PASSED: Home page is publicly accessible (200 OK).")

# TEST 2: Student Login -> Student Dashboard
print("\n[TEST 2] Logging in as Student...")
r_login_get = session.get(BASE_URL + "/login")
match_csrf = re.search(r'name="csrf_token" value="([^"]+)"', r_login_get.text)
csrf_token = match_csrf.group(1) if match_csrf else ""

r2 = session.post(BASE_URL + "/login", data={
    "csrf_token": csrf_token,
    "email": "25LBCS3099@culkomail.in",
    "password": "Test@1234"
}, allow_redirects=False)
assert r2.status_code == 302, f"Expected 302 redirect after login, got {r2.status_code}"
assert r2.headers.get("Location") == "/student/dashboard"

r_dash = session.get(BASE_URL + "/student/dashboard")
assert r_dash.status_code == 200
assert "Mayank Awasthi" in r_dash.text
print("  [OK] TEST 2 PASSED: Student logged in and reached Student Dashboard.")

# TEST 3: Student Dashboard -> Click Home
print("\n[TEST 3] From Student Dashboard, navigating to Home (/)...")
r3 = session.get(BASE_URL + "/", allow_redirects=False)
assert r3.status_code == 200, f"Expected 200 OK on Home for logged-in student, but got {r3.status_code} (Redirect: {r3.headers.get('Location')})"
assert "Dashboard" in r3.text
assert "My Complaints" in r3.text
assert "Mayank Awasthi" in r3.text
print("  [OK] TEST 3 PASSED: Logged-in student successfully opened Home page without being redirected or logged out.")

# TEST 4: From Home -> Click Dashboard
print("\n[TEST 4] From Home page, navigating back to Student Dashboard...")
r4 = session.get(BASE_URL + "/student/dashboard", allow_redirects=False)
assert r4.status_code == 200, f"Expected 200 OK on Student Dashboard, but got {r4.status_code} (Location: {r4.headers.get('Location')})"
assert "Mayank Awasthi" in r4.text
print("  [OK] TEST 4 PASSED: Student returned to Student Dashboard seamlessly without re-login.")

# TEST 5: From Home -> Submit Complaint
print("\n[TEST 5] From Home page, navigating to Submit Complaint...")
r5 = session.get(BASE_URL + "/student/submit", allow_redirects=False)
assert r5.status_code == 200, f"Expected 200 OK on Submit Complaint, but got {r5.status_code}"
assert "Report a Campus Issue" in r5.text
print("  [OK] TEST 5 PASSED: Student accessed Submit Complaint while remaining logged in.")

# TEST 6: From Home -> Logout
print("\n[TEST 6] Explicitly logging out...")
r6 = session.get(BASE_URL + "/logout", allow_redirects=False)
assert r6.status_code == 302, f"Expected 302 on logout, got {r6.status_code}"
assert r6.headers.get("Location") == "/"
print("  [OK] TEST 6 PASSED: Student explicitly logged out.")

# TEST 7: After Logout -> Home works, private pages require login
print("\n[TEST 7] Verifying access control after logout...")
r7_home = session.get(BASE_URL + "/", allow_redirects=False)
assert r7_home.status_code == 200
assert "Student Login" in r7_home.text

r7_priv = session.get(BASE_URL + "/student/dashboard", allow_redirects=False)
assert r7_priv.status_code == 302
assert "/login" in r7_priv.headers.get("Location")
print("  [OK] TEST 7 PASSED: Home page remains public, while private student pages are securely protected.")

print("\n" + "=" * 60)
print("ALL 7 NAVIGATION & SESSION TESTS PASSED WITH 100% SUCCESS!")
print("=" * 60)
