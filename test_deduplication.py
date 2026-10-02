import os
import sys
import unittest
import sqlite3

# Ensure workspace root is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import database
from app import app


class TestDuplicateComplaintGrouping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.create_database()
        cls.app = app
        cls.client = app.test_client()

        # Create or fetch 3 dedicated test students with valid @culkomail.in emails
        conn = database.get_db_connection()
        cursor = conn.cursor()

        def get_or_create_student(name, email):
            cursor.execute("SELECT student_id FROM students WHERE LOWER(email) = LOWER(?)", (email,))
            row = cursor.fetchone()
            if row:
                return row["student_id"]
            ok, sid = database.register_new_student(name=name, email=email, password="Password123!")
            if ok:
                return sid
            cursor.execute("SELECT student_id FROM students WHERE LOWER(email) = LOWER(?)", (email,))
            return cursor.fetchone()["student_id"]

        cls.student_a_id = get_or_create_student("Student Alpha", "studenta123@culkomail.in")
        cls.student_b_id = get_or_create_student("Student Beta", "studentb123@culkomail.in")
        cls.student_c_id = get_or_create_student("Student Gamma", "studentc123@culkomail.in")

        # Clean any prior test complaints and slots for test students and test room 999
        cursor.execute("DELETE FROM complaint_reporters WHERE student_id IN (?, ?, ?)", (cls.student_a_id, cls.student_b_id, cls.student_c_id))
        cursor.execute("DELETE FROM active_complaint_slots WHERE student_id IN (?, ?, ?) OR slot_key LIKE '%999%'", (cls.student_a_id, cls.student_b_id, cls.student_c_id))
        cursor.execute("DELETE FROM complaints WHERE student_id IN (?, ?, ?) OR room_no LIKE '%999%'", (cls.student_a_id, cls.student_b_id, cls.student_c_id))
        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM complaint_reporters WHERE student_id IN (?, ?, ?)", (cls.student_a_id, cls.student_b_id, cls.student_c_id))
        cursor.execute("DELETE FROM active_complaint_slots WHERE student_id IN (?, ?, ?) OR slot_key LIKE '%999%'", (cls.student_a_id, cls.student_b_id, cls.student_c_id))
        cursor.execute("DELETE FROM complaints WHERE student_id IN (?, ?, ?) OR room_no LIKE '%999%'", (cls.student_a_id, cls.student_b_id, cls.student_c_id))
        cursor.execute("DELETE FROM complaint_status_history WHERE complaint_id NOT IN (SELECT complaint_id FROM complaints)")
        conn.commit()
        conn.close()

    def test_01_student_a_submits_issue_x(self):
        """1. Student A submits Issue X -> new master complaint created"""
        res = database.submit_or_attach_complaint(
            student_id=self.student_a_id,
            category="Electrical",
            description="Ceiling fan is not working properly in the room",
            photo_path="uploads/test_evidence.jpg",
            block="Block E",
            floor_no="2nd Floor",
            room_no="Room 999",
            corridor_side="Left",
            priority="Medium",
            date_str="2026-03-24"
        )

        self.assertEqual(res["status"], "CREATED_NEW")
        self.assertIn("complaint_id", res)
        TestDuplicateComplaintGrouping.master_complaint_id = res["complaint_id"]

        complaint = database.get_complaint_by_id(self.master_complaint_id)
        self.assertIsNotNone(complaint)
        self.assertEqual(complaint["affected_student_count"], 1)
        self.assertTrue(bool(complaint["complaint_fingerprint"]))

        print(f"\n[Test 01 Passed]: Master complaint {self.master_complaint_id} created with count 1.")

    def test_02_student_a_submits_same_issue_x_again(self):
        """2. Student A submits Issue X again -> rejected duplicate with message, no new DB record"""
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM complaints")
        total_before = cursor.fetchone()[0]
        conn.close()

        res = database.submit_or_attach_complaint(
            student_id=self.student_a_id,
            category="Electrical",
            description="ceiling fan not working",  # slight variation in grammar/casing
            photo_path="uploads/test_evidence2.jpg",
            block="Block E",
            floor_no="2nd Floor",
            room_no="999",  # slight variation in room notation
            priority="High",
            date_str="2026-03-24"
        )

        self.assertEqual(res["status"], "DUPLICATE_REJECTED")
        self.assertIn("already reported this issue", res["message"])
        self.assertEqual(res["complaint_id"], self.master_complaint_id)

        # Verify no new row inserted in complaints table
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM complaints")
        total_after = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(total_before, total_after, "Duplicate submission must NOT insert a new complaint record!")
        print(f"[Test 02 Passed]: Duplicate submission blocked for Student A with message: '{res['message']}'")

    def test_03_student_b_submits_issue_x(self):
        """3. Student B submits Issue X -> accepted, linked to master complaint, count becomes 2"""
        res = database.submit_or_attach_complaint(
            student_id=self.student_b_id,
            category="Electrical",
            description="The ceiling fan is not working at all",
            photo_path="uploads/test_evidence_b.jpg",
            block="Block E",
            floor_no="2nd Floor",
            room_no="Room 999",
            priority="Medium",
            date_str="2026-03-24"
        )

        self.assertEqual(res["status"], "ATTACHED_TO_MASTER")
        self.assertEqual(res["complaint_id"], self.master_complaint_id)
        self.assertEqual(res["affected_student_count"], 2)
        self.assertIn("linked to existing grievance ticket", res["message"])

        complaint = database.get_complaint_by_id(self.master_complaint_id)
        self.assertEqual(complaint["affected_student_count"], 2)
        print(f"[Test 03 Passed]: Student B linked to master {self.master_complaint_id}, count is now 2.")

    def test_04_student_c_submits_issue_x(self):
        """4. Student C submits Issue X -> accepted, linked to master complaint, count becomes 3"""
        res = database.submit_or_attach_complaint(
            student_id=self.student_c_id,
            category="Electrical",
            description="room 999 ceiling fan is not working",
            photo_path="uploads/test_evidence_c.jpg",
            block="Block E",
            floor_no="2nd Floor",
            room_no="999",
            priority="High",
            date_str="2026-03-24"
        )

        self.assertEqual(res["status"], "ATTACHED_TO_MASTER")
        self.assertEqual(res["complaint_id"], self.master_complaint_id)
        self.assertEqual(res["affected_student_count"], 3)

        complaint = database.get_complaint_by_id(self.master_complaint_id)
        self.assertEqual(complaint["affected_student_count"], 3)
        print(f"[Test 04 Passed]: Student C linked to master {self.master_complaint_id}, count is now 3.")

    def test_05_admin_dashboard_shows_one_complaint_with_3_affected(self):
        """5. Admin dashboard shows 1 complaint with 3 students affected"""
        res = database.get_all_complaints_admin_paginated(
            page=1,
            per_page=100
        )
        complaints = res["items"]

        matching = [c for c in complaints if c["complaint_id"] == self.master_complaint_id]
        self.assertEqual(len(matching), 1, "Admin list must show exactly 1 master complaint row!")
        self.assertEqual(matching[0]["affected_student_count"], 3)
        print(f"[Test 05 Passed]: Admin list shows 1 row with affected_student_count = {matching[0]['affected_student_count']}.")

    def test_06_admin_detail_view_lists_all_3_students(self):
        """6. Admin detail view lists all 3 reporting students with details and timestamps"""
        reporters = database.get_complaint_reporters(self.master_complaint_id)
        self.assertEqual(len(reporters), 3)

        reported_student_ids = [r["student_id"] for r in reporters]
        self.assertIn(self.student_a_id, reported_student_ids)
        self.assertIn(self.student_b_id, reported_student_ids)
        self.assertIn(self.student_c_id, reported_student_ids)

        for r in reporters:
            self.assertIsNotNone(r["reported_at"])
            self.assertTrue(bool(r["student_email"]))

        print(f"[Test 06 Passed]: Admin detail view retrieves all 3 reporters: {[r['student_email'] for r in reporters]}")

    def test_07_students_a_b_c_each_see_master_complaint_once(self):
        """7. Students A, B, and C each see master complaint once in their complaint list"""
        for sid, name in [
            (self.student_a_id, "Student A"),
            (self.student_b_id, "Student B"),
            (self.student_c_id, "Student C")
        ]:
            res = database.get_student_complaints_paginated(student_id=sid, page=1, per_page=50)
            complaints = res["items"]
            matching = [c for c in complaints if c["complaint_id"] == self.master_complaint_id]
            self.assertEqual(len(matching), 1, f"{name} must see the master complaint exactly once!")
            self.assertEqual(matching[0]["affected_student_count"], 3)

        print("[Test 07 Passed]: Students A, B, and C each see the master complaint exactly once.")

    def test_08_student_a_submits_different_issue(self):
        """8. Student A submits different issue at same location -> new complaint created"""
        res = database.submit_or_attach_complaint(
            student_id=self.student_a_id,
            category="Infrastructure",
            description="Window glass frame is completely broken and rattling",
            photo_path="uploads/test_infra.jpg",
            block="Block E",
            floor_no="2nd Floor",
            room_no="Room 999",
            priority="Medium",
            date_str="2026-03-24"
        )

        self.assertEqual(res["status"], "CREATED_NEW")
        new_cid = res["complaint_id"]
        self.assertNotEqual(new_cid, self.master_complaint_id)
        print(f"[Test 08 Passed]: Different issue created new complaint {new_cid}.")

    def test_09_student_a_submits_same_issue_at_different_location(self):
        """9. Student A submits same issue at different location -> new complaint created"""
        res = database.submit_or_attach_complaint(
            student_id=self.student_a_id,
            category="Electrical",
            description="Ceiling fan is not working properly in the room",
            photo_path="uploads/test_fan_blockc.jpg",
            block="Block C",  # Different block
            floor_no="1st Floor",
            room_no="Room 101",
            priority="Medium",
            date_str="2026-03-24"
        )

        self.assertEqual(res["status"], "CREATED_NEW")
        new_loc_cid = res["complaint_id"]
        self.assertNotEqual(new_loc_cid, self.master_complaint_id)
        print(f"[Test 09 Passed]: Same issue at different location created new complaint {new_loc_cid}.")

    def test_10_refresh_resubmit_browser_simulation(self):
        """10. Refresh/re-submit on browser does not create duplicate"""
        # Simulate Student B trying to submit again via submit_or_attach_complaint
        res = database.submit_or_attach_complaint(
            student_id=self.student_b_id,
            category="Electrical",
            description="The ceiling fan is not working at all",
            photo_path="uploads/test_evidence_b.jpg",
            block="Block E",
            floor_no="2nd Floor",
            room_no="Room 999",
            priority="Medium",
            date_str="2026-03-24"
        )

        self.assertEqual(res["status"], "DUPLICATE_REJECTED")
        self.assertEqual(res["complaint_id"], self.master_complaint_id)
        print("[Test 10 Passed]: Backend idempotency prevents duplicate on refresh/re-submit.")

    def test_11_db_constraint_prevents_duplicate_in_complaint_reporters(self):
        """11. Database constraint prevents duplicate (complaint_id, student_id) in complaint_reporters"""
        conn = database.get_db_connection()
        cursor = conn.cursor()
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at) VALUES (?, ?, ?, ?)",
                (self.master_complaint_id, self.student_a_id, "studenta123@culkomail.in", "2026-03-24 12:00:00")
            )
            conn.commit()
        conn.close()
        print("[Test 11 Passed]: SQLite UNIQUE(complaint_id, student_id) constraint verified.")

    def test_12_admin_statistics_update_correctly(self):
        """12. Admin statistics update correctly: unique grievances vs total student reports"""
        stats = database.get_admin_statistics()
        self.assertIn("total", stats)
        self.assertIn("total_reports", stats)
        self.assertIn("students_affected", stats)
        self.assertGreaterEqual(stats["total_reports"], stats["total"])
        self.assertGreaterEqual(stats["students_affected"], stats["total"])
        print(f"[Test 12 Passed]: Admin stats -> Unique Complaints: {stats['total']}, Total Reports: {stats['total_reports']}, Affected: {stats['students_affected']}")

    def test_13_existing_complaints_not_corrupted(self):
        """13. Existing complaints in the system are not corrupted"""
        all_complaints = database.get_all_complaints()
        self.assertGreater(len(all_complaints), 0)
        for c in all_complaints:
            self.assertIsNotNone(c["complaint_id"])
            self.assertIsNotNone(c["category"])
            self.assertIsNotNone(c["description"])
            self.assertIsNotNone(c["complaint_fingerprint"])
            self.assertGreaterEqual(c["affected_student_count"], 1)

        print(f"[Test 13 Passed]: All {len(all_complaints)} existing complaints have valid fingerprints and reporter counts.")


if __name__ == "__main__":
    unittest.main()
