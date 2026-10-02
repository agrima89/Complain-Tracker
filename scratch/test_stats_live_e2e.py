import os
import sys
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta

# Import workspace modules
sys.path.insert(0, os.path.abspath("."))
import database
import app as flask_app

class TestLiveStatistics(unittest.TestCase):
    def setUp(self):
        self.app = flask_app.app.test_client()
        self.app.testing = True

    def test_01_current_database_live_stats(self):
        """Verify that get_public_statistics() matches real database queries exactly."""
        conn = database.get_db_connection()
        db_total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
        db_resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'").fetchone()[0]
        conn.close()

        stats = database.get_public_statistics()
        self.assertEqual(stats["total_complaints"], db_total)
        self.assertEqual(stats["resolved_complaints"], db_resolved)

        if db_total > 0:
            expected_rate = round((db_resolved / db_total) * 100.0, 1)
            self.assertEqual(stats["resolution_rate"], expected_rate)
            self.assertEqual(stats["resolution_rate_display"], f"{expected_rate:.1f}%")
        else:
            self.assertEqual(stats["resolution_rate"], 0.0)
            self.assertEqual(stats["resolution_rate_display"], "0.0%")

        print(f"[TEST 1 PASS] Live DB Stats: Total={stats['total_complaints']}, Resolved={stats['resolved_complaints']}, Rate={stats['resolution_rate_display']}, AvgResp={stats['average_response_display']}")

    def test_02_api_endpoint(self):
        """Verify /api/public-stats and /api/stats return live JSON data."""
        resp1 = self.app.get("/api/public-stats")
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.get_json()
        self.assertTrue(data1["success"])
        self.assertIn("total_complaints", data1["stats"])
        self.assertIn("resolved_complaints", data1["stats"])
        self.assertIn("resolution_rate", data1["stats"])
        self.assertIn("average_response_display", data1["stats"])

        resp2 = self.app.get("/api/stats")
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.get_json()
        self.assertEqual(data1["stats"], data2["stats"])

        print("[TEST 2 PASS] API Endpoints /api/public-stats & /api/stats return correct live JSON payload.")

    def test_03_landing_page_render(self):
        """Verify landing.html and login.html render with live stats without fake fallback data."""
        stats = database.get_public_statistics()
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)

        self.assertNotIn('data-target="2481"', html)
        self.assertNotIn('data-target="2316"', html)
        self.assertNotIn('data-target="93.4"', html)
        self.assertIn('id="statComplaintsSubmitted"', html)
        self.assertIn('id="statIssuesResolved"', html)
        self.assertIn('id="statResolutionRate"', html)
        self.assertIn('id="statAverageResponse"', html)
        self.assertIn(str(stats["total_complaints"]), html)
        self.assertIn(str(stats["resolved_complaints"]), html)

        print("[TEST 3 PASS] Landing page HTML renders live dynamic attributes and values.")

    def test_04_empty_database_behavior(self):
        """Verify that on an empty database, zero division is prevented and neutral values are returned."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_db_path = tmp.name

        orig_db_path = database.DB_PATH
        try:
            database.DB_PATH = tmp_db_path
            database.create_database()

            stats = database.get_public_statistics()
            self.assertEqual(stats["total_complaints"], 0)
            self.assertEqual(stats["resolved_complaints"], 0)
            self.assertEqual(stats["resolution_rate"], 0.0)
            self.assertEqual(stats["resolution_rate_display"], "0.0%")
            self.assertIsNone(stats["average_response_hours"])
            self.assertEqual(stats["average_response_display"], "--")

            print("[TEST 4 PASS] Empty DB Behavior: 0 complaints -> 0.0% rate, '--' avg response.")
        finally:
            database.DB_PATH = orig_db_path
            if os.path.exists(tmp_db_path):
                try:
                    os.remove(tmp_db_path)
                except Exception:
                    pass

    def test_05_lifecycle_and_response_time_calculation(self):
        """Verify dynamic calculation as complaints are created, responded to, and resolved."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_db_path = tmp.name

        orig_db_path = database.DB_PATH
        try:
            database.DB_PATH = tmp_db_path
            database.create_database()

            # 1. Register a student
            database.register_new_student("Test User", "teststudent1@culkomail.in", "Password123")
            conn = database.get_db_connection()
            student = conn.execute("SELECT student_id FROM students WHERE email='teststudent1@culkomail.in'").fetchone()
            student_id = student["student_id"]
            conn.close()

            # 2. Submit complaint #1 at T - 4 hours
            sub_time_1 = (datetime.now() - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")
            cid1, ticket1 = database.create_complaint(
                student_id=student_id,
                category="Electrical",
                description="Power outlet in Room 302 not working",
                block="Block A",
                date_str=sub_time_1[:10]
            )
            # Update history / submission timestamp
            conn = database.get_db_connection()
            conn.execute("UPDATE complaints SET date=?, last_updated=? WHERE complaint_id=?", (sub_time_1, sub_time_1, cid1))
            conn.execute("UPDATE complaint_status_history SET changed_at=? WHERE complaint_id=?", (sub_time_1, cid1))
            conn.commit()
            conn.close()

            stats1 = database.get_public_statistics()
            self.assertEqual(stats1["total_complaints"], 1)
            self.assertEqual(stats1["resolved_complaints"], 0)
            self.assertEqual(stats1["resolution_rate"], 0.0)
            self.assertEqual(stats1["average_response_display"], "--")

            # 3. Admin responds at T - 2 hours (2 hours response time)
            resp_time_1 = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
            database.update_complaint_status(
                complaint_id=cid1,
                new_status="In Progress",
                admin_name="Facility Head",
                admin_id=1,
                remarks="Technician dispatched to inspect room."
            )
            conn = database.get_db_connection()
            conn.execute("UPDATE complaints SET first_responded_at=? WHERE complaint_id=?", (resp_time_1, cid1))
            conn.execute("UPDATE complaint_status_history SET changed_at=? WHERE complaint_id=? AND new_status='In Progress'", (resp_time_1, cid1))
            conn.commit()
            conn.close()

            stats2 = database.get_public_statistics()
            self.assertEqual(stats2["total_complaints"], 1)
            self.assertEqual(stats2["resolved_complaints"], 0)
            self.assertEqual(stats2["average_response_hours"], 2.0)
            self.assertEqual(stats2["average_response_display"], "2h")

            # 4. Admin marks complaint as Resolved
            database.update_complaint_status(
                complaint_id=cid1,
                new_status="Resolved",
                admin_name="Facility Head",
                admin_id=1,
                remarks="Outlet replaced and tested."
            )

            stats3 = database.get_public_statistics()
            self.assertEqual(stats3["total_complaints"], 1)
            self.assertEqual(stats3["resolved_complaints"], 1)
            self.assertEqual(stats3["resolution_rate"], 100.0)
            self.assertEqual(stats3["resolution_rate_display"], "100.0%")
            self.assertEqual(stats3["average_response_hours"], 2.0)
            self.assertEqual(stats3["average_response_display"], "2h")

            print("[TEST 5 PASS] Lifecycle test passed: Total=1, Resolved=1, Rate=100.0%, AvgResp=2h.")
        finally:
            database.DB_PATH = orig_db_path
            if os.path.exists(tmp_db_path):
                try:
                    os.remove(tmp_db_path)
                except Exception:
                    pass

if __name__ == "__main__":
    unittest.main()
