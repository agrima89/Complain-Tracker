import sys
import os
import unittest
import re

sys.path.insert(0, r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker")

import database
from app import app

class TestHomeNavigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.create_database()
        cls.client = app.test_client()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

        # Ensure test student exists
        with database.get_db_connection() as conn:
            conn.execute("DELETE FROM students WHERE LOWER(email) = LOWER(?)", ("25LBCS3099@culkomail.in",))
            conn.commit()
        database.register_new_student("Mayank Awasthi", "25LBCS3099@culkomail.in", "Test@1234")

    def test_01_public_home_accessible(self):
        """TEST 1: Open website -> Home works (200 OK)."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("CampusCare", html)
        self.assertIn("Student Login", html)
        print("[OK] TEST 1: Public Home page opens successfully for unauthenticated visitor.")

    def test_02_student_login_and_dashboard(self):
        """TEST 2: Student Login -> Student Dashboard."""
        res_login = self.client.post("/login", data={
            "email": "25LBCS3099@culkomail.in",
            "password": "Test@1234"
        }, follow_redirects=False)
        self.assertEqual(res_login.status_code, 302)
        self.assertEqual(res_login.headers.get("Location"), "/student/dashboard")

        res_dash = self.client.get("/student/dashboard")
        self.assertEqual(res_dash.status_code, 200)
        html_dash = res_dash.get_data(as_text=True)
        self.assertIn("Welcome back, Mayank Awasthi", html_dash)
        print("[OK] TEST 2: Student logs in and lands on Student Dashboard.")

    def test_03_student_dashboard_to_home_preserves_session(self):
        """TEST 3 & 4: Student Dashboard -> Home -> Student Dashboard without logging out."""
        # 1. Login student
        self.client.post("/login", data={
            "email": "25LBCS3099@culkomail.in",
            "password": "Test@1234"
        }, follow_redirects=True)

        # 2. Student clicks "Home" -> Navigates to "/"
        res_home = self.client.get("/", follow_redirects=False)
        self.assertEqual(res_home.status_code, 200, "Home page MUST return 200, not redirect!")
        html_home = res_home.get_data(as_text=True)
        # Should show student navigation links on Home page
        self.assertIn("Dashboard", html_home)
        self.assertIn("My Complaints", html_home)
        self.assertIn("Mayank Awasthi", html_home)
        print("[OK] TEST 3: Logged-in student navigated to Home page (200 OK) without being redirected or logged out.")

        # 3. From Home, student clicks "Dashboard" -> Navigates to "/student/dashboard"
        res_dash = self.client.get("/student/dashboard", follow_redirects=False)
        self.assertEqual(res_dash.status_code, 200, "Student Dashboard should open directly without re-login!")
        html_dash = res_dash.get_data(as_text=True)
        self.assertIn("Welcome back, Mayank Awasthi", html_dash)
        print("[OK] TEST 4: Student returned to Student Dashboard seamlessly without re-login.")

    def test_05_home_to_submit_complaint(self):
        """TEST 5: Home -> Submit Complaint while remaining logged in."""
        # Student logged in
        self.client.post("/login", data={
            "email": "25LBCS3099@culkomail.in",
            "password": "Test@1234"
        }, follow_redirects=True)

        # Access submit complaint from Home
        res_submit = self.client.get("/student/submit", follow_redirects=False)
        self.assertEqual(res_submit.status_code, 200)
        html_submit = res_submit.get_data(as_text=True)
        self.assertIn("Report a Campus Issue", html_submit)
        print("[OK] TEST 5: Student accessed Submit Complaint page while still logged in.")

    def test_06_and_07_logout_flow(self):
        """TEST 6 & 7: Logout flow and access control verification."""
        # 1. Login
        self.client.post("/login", data={
            "email": "25LBCS3099@culkomail.in",
            "password": "Test@1234"
        }, follow_redirects=True)

        # 2. Click Logout
        res_logout = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(res_logout.status_code, 302)
        self.assertEqual(res_logout.headers.get("Location"), "/")

        # 3. Visit Home after logout
        res_home = self.client.get("/")
        self.assertEqual(res_home.status_code, 200)
        html_home = res_home.get_data(as_text=True)
        self.assertIn("Student Login", html_home)

        # 4. Attempt to access private dashboard after logout -> redirects to login
        res_priv = self.client.get("/student/dashboard", follow_redirects=False)
        self.assertEqual(res_priv.status_code, 302)
        self.assertIn("/login", res_priv.headers.get("Location"))
        print("[OK] TEST 6 & 7: Explicit logout cleanly clears session and protects private routes.")

    def test_08_admin_home_navigation(self):
        """TEST 8: Admin login -> Home -> Admin Dashboard without losing session."""
        # Admin login
        res_admin_login = self.client.post("/admin/login", data={
            "username": "admin",
            "password": "admin123"
        }, follow_redirects=False)
        self.assertEqual(res_admin_login.status_code, 302)

        # Admin visits Home
        res_home = self.client.get("/", follow_redirects=False)
        self.assertEqual(res_home.status_code, 200)
        html_home = res_home.get_data(as_text=True)
        self.assertIn("Management Dashboard", html_home)

        # Admin returns to Dashboard
        res_admin_dash = self.client.get("/admin/dashboard", follow_redirects=False)
        self.assertEqual(res_admin_dash.status_code, 200)
        print("[OK] TEST 8: Admin navigates Home <-> Admin Dashboard smoothly.")

if __name__ == "__main__":
    unittest.main()
