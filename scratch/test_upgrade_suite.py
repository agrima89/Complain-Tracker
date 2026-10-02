import os
import sys
import unittest
import sqlite3
import re
from datetime import datetime, timedelta

# Ensure root directory is on Python path
sys.path.insert(0, r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker")

import database
from app import app

class TestUpgradeSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.create_database()
        cls.client = app.test_client()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = True

        # Clean test accounts if any exist
        with database.get_db_connection() as conn:
            conn.execute("DELETE FROM students WHERE email IN ('25LBCS9999@culkomail.in', '25LBCS8888@culkomail.in')")
            conn.commit()

    def test_01_password_hashing_and_migration(self):
        """Test PBKDF2 password hashing and legacy plain-text auto-migration."""
        test_email = "25LBCS9999@culkomail.in"
        test_pass = "SecurePass123!"

        # Register new student
        success, student_id = database.register_new_student(
            name="Hash Student",
            email=test_email,
            password=test_pass
        )
        self.assertTrue(success, f"Registration failed: {student_id}")

        # Verify hashed format in DB
        with database.get_db_connection() as conn:
            user = conn.execute("SELECT password FROM students WHERE email = ?", (test_email,)).fetchone()
            self.assertIsNotNone(user)
            self.assertTrue(user["password"].startswith(("pbkdf2:sha256:", "scrypt:")))

        # Verify authentication
        auth_user, err = database.authenticate_student(test_email, test_pass)
        self.assertIsNotNone(auth_user)
        self.assertEqual(auth_user["email"], test_email)

        # Test legacy plain-text auto-migration
        legacy_email = "25LBCS8888@culkomail.in"
        with database.get_db_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO students (name, email, password) VALUES (?, ?, ?)",
                ("Legacy User", legacy_email, "plainpassword")
            )
            conn.commit()

        # Check that it's initially plain text
        with database.get_db_connection() as conn:
            leg_row = conn.execute("SELECT password FROM students WHERE email = ?", (legacy_email,)).fetchone()
            self.assertEqual(leg_row["password"], "plainpassword")

        # Authenticate legacy user -> should trigger auto-migration
        migrated_user, err = database.authenticate_student(legacy_email, "plainpassword")
        self.assertIsNotNone(migrated_user)

        # Check DB row is now hashed
        with database.get_db_connection() as conn:
            migrated_row = conn.execute("SELECT password FROM students WHERE email = ?", (legacy_email,)).fetchone()
            self.assertTrue(migrated_row["password"].startswith(("pbkdf2:sha256:", "scrypt:")))

        print("[OK] Test 1: Password hashing & auto-migration passed.")

    def test_02_csrf_protection(self):
        """Verify CSRF token rejection on missing token and acceptance on valid token."""
        # 1. AJAX/JSON POST without CSRF token should be rejected (400 Bad Request)
        res_no_csrf = self.client.post("/admin/api/update-status", json={
            "complaint_id": 1,
            "status": "In Progress"
        }, headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(res_no_csrf.status_code, 400)
        data = res_no_csrf.get_json()
        self.assertFalse(data.get("success", True))

        # 2. Form POST without CSRF redirects back safely with flash message (302)
        res_form_no_csrf = self.client.post("/login", data={
            "email": "25LBCS9999@culkomail.in",
            "password": "SecurePass123!"
        })
        self.assertEqual(res_form_no_csrf.status_code, 302)

        # 3. Get login page, extract CSRF token, and submit
        res_get = self.client.get("/login")
        self.assertEqual(res_get.status_code, 200)
        match = re.search(r'name="csrf_token" value="([^"]+)"', res_get.get_data(as_text=True))
        self.assertIsNotNone(match, "CSRF token hidden input not found in login page")
        csrf_token = match.group(1)

        res_with_csrf = self.client.post("/login", data={
            "csrf_token": csrf_token,
            "email": "25LBCS9999@culkomail.in",
            "password": "SecurePass123!"
        }, follow_redirects=False)
        self.assertEqual(res_with_csrf.status_code, 302) # Redirect to student dashboard

        print("[OK] Test 2: CSRF Protection enforcement passed.")

    def test_03_ticket_id_and_status_audit_trail(self):
        """Verify ticket ID generation, status history audit trail, and admin remarks."""
        # Insert test complaint
        complaint_id, ticket_id = database.create_complaint(
            student_id=1,
            category="Electrical",
            description="Flickering lights in Room 302",
            photo_path="static/uploads/evidence.jpg",
            priority="High",
            block="Block A",
            floor_no="3rd Floor",
            room_no="302",
            corridor_side="East",
            nearby_area="Opposite Lab",
            additional_location="Next to water cooler"
        )
        self.assertIsNotNone(complaint_id)
        self.assertTrue(ticket_id.startswith("CMP-"))

        complaint = database.get_complaint_by_id(complaint_id)
        self.assertIsNotNone(complaint)
        self.assertEqual(complaint["ticket_id"], ticket_id)
        self.assertEqual(complaint["status"], "NEW")

        # Update status to In Progress with remarks
        database.update_complaint_status(
            complaint_id=complaint_id,
            new_status="IN_PROGRESS",
            admin_id=1,
            admin_name="Admin Officer",
            remarks="Dispatched technician to inspect Room 302"
        )

        history = database.get_complaint_history(complaint_id)
        self.assertTrue(len(history) >= 1)
        latest_history = history[-1]
        self.assertEqual(latest_history["new_status"], "IN_PROGRESS")
        self.assertEqual(latest_history["changed_by"], "Admin Officer")
        self.assertIn("Dispatched technician", latest_history["remarks"])

        # Add internal admin note
        n_success, n_id = database.add_admin_note(
            complaint_id=complaint_id,
            admin_id=1,
            admin_name="Lead Admin",
            note="Spoke with electrician, replacement ballast required."
        )
        self.assertTrue(n_success)

        notes = database.get_admin_notes(complaint_id)
        self.assertTrue(len(notes) >= 1)
        self.assertEqual(notes[0]["admin_name"], "Lead Admin")
        self.assertIn("replacement ballast required", notes[0]["note"])

        print("[OK] Test 3: Ticket ID, status audit trail & admin notes passed.")

    def test_04_analytics_and_escalation(self):
        """Verify analytics telemetry aggregation and escalation detection."""
        analytics = database.get_analytics_data()
        self.assertIn("categories", analytics)
        self.assertIn("priorities", analytics)
        self.assertIn("monthly_trends", analytics)
        self.assertIn("total_complaints", analytics)
        self.assertIn("resolved_percentage", analytics)

        # Test escalation logic
        # 1. Fresh High priority complaint (not escalated)
        fresh_complaint = {
            "status": "NEW",
            "priority": "High",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.assertFalse(database.check_is_escalated(fresh_complaint, hours_threshold=48))

        # 2. Overdue High priority complaint (3 days old -> escalated)
        overdue_complaint = {
            "status": "In Progress",
            "priority": "High",
            "date": (datetime.now() - timedelta(hours=72)).strftime("%Y-%m-%d %H:%M:%S")
        }
        self.assertTrue(database.check_is_escalated(overdue_complaint, hours_threshold=48))

        # 3. Overdue Low priority complaint (not escalated since priority is not High)
        low_overdue = {
            "status": "NEW",
            "priority": "Low",
            "date": (datetime.now() - timedelta(hours=72)).strftime("%Y-%m-%d %H:%M:%S")
        }
        self.assertFalse(database.check_is_escalated(low_overdue, hours_threshold=48))

        print("[OK] Test 4: Analytics telemetry & escalation detection passed.")

    def test_05_pagination_and_file_validation(self):
        """Verify server-side pagination and secure file upload validation."""
        # Test pagination
        p_data = database.get_all_complaints_admin_paginated(page=1, per_page=5)
        self.assertIn("items", p_data)
        self.assertIn("total_pages", p_data)
        self.assertIn("total_items", p_data)
        self.assertIn("page", p_data)
        self.assertEqual(p_data["page"], 1)

        # Test secure file extension helper
        self.assertTrue(database.allowed_file("evidence.jpg"))
        self.assertTrue(database.allowed_file("document.pdf"))
        self.assertTrue(database.allowed_file("snapshot.PNG"))
        self.assertTrue(database.allowed_file("image.webp"))
        self.assertFalse(database.allowed_file("malicious.exe"))
        self.assertFalse(database.allowed_file("script.py"))
        self.assertFalse(database.allowed_file("payload.php"))

        print("[OK] Test 5: Server-side pagination & secure file validation passed.")

if __name__ == "__main__":
    unittest.main()
