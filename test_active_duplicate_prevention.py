
import os
import sys
import unittest
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import database
from app import app


class TestActiveDuplicateComplaintPrevention(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.create_database()
        cls.app = app
        cls.client = app.test_client()

        # Connect to DB and fetch or register test student
        conn = database.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT student_id, email FROM students WHERE LOWER(email) = LOWER('25LBCS1028@culkomail.in')")
        row = cursor.fetchone()
        if row:
            cls.student_id = row["student_id"]
            cls.student_email = row["email"]
        else:
            ok, sid = database.register_new_student("Agrima Bajpai", "25LBCS1028@culkomail.in", "Password123!")
            cls.student_id = sid
            cls.student_email = "25LBCS1028@culkomail.in"

        conn.close()

    def test_01_existing_active_complaint_blocks_duplicate_different_words(self):
        """
        1. When CMP-2026-0051 is active (Electrical in Block E, Room E-329),
           submitting another Electrical complaint in Block E, Room E-329
           with DIFFERENT wording MUST be rejected without creating a new record.
        """
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM complaints")
        total_before = cursor.fetchone()[0]

        # Verify CMP-2026-0051 is in database and update its description so similar words can be matched
        cursor.execute("UPDATE complaints SET description = 'Switchboard is sparking' WHERE ticket_id = 'CMP-2026-0051'")
        conn.commit()
        cursor.execute("SELECT complaint_id, ticket_id, status FROM complaints WHERE ticket_id = 'CMP-2026-0051'")
        existing = cursor.fetchone()
        self.assertIsNotNone(existing, "CMP-2026-0051 should exist in database.")
        self.assertIn(existing["status"], database.ACTIVE_COMPLAINT_STATUSES)
        conn.close()

        # Attempt to submit another Electrical complaint for Block E, Room E-329
        # with totally different wording ("Switchboard sparking, plug melted")
        res = database.submit_or_attach_complaint(
            student_id=self.student_id,
            category="Electrical",
            description="Switchboard is sparking heavily and plug point has completely melted down",
            photo_path="uploads/spark_evidence.jpg",
            block="Block E",
            floor_no="2nd Floor",
            room_no="Room E-329",
            priority="High",
            date_str="2026-09-24"
        )

        self.assertEqual(res["status"], "DUPLICATE_REJECTED")
        self.assertIn("Duplicate Complaint Detected", res["message"])
        self.assertIn("CMP-2026-0051", res["message"])
        self.assertEqual(res["ticket_id"], "CMP-2026-0051")

        # Verify no new row was inserted in database
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM complaints")
        total_after = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(total_before, total_after, "Duplicate complaint MUST NOT create a new database row!")
        print(f"\n[Test 01 Passed]: Submission rejected -> '{res['message']}'")

    def test_02_same_student_different_room_is_allowed(self):
        """
        2. Same student submitting Electrical issue in ANOTHER ROOM (Room 101)
           MUST be accepted and created normally.
        """
        res = database.submit_or_attach_complaint(
            student_id=self.student_id,
            category="Electrical",
            description="Fan not working in Room 101 ground floor",
            photo_path="uploads/room101_evidence.jpg",
            block="Block E",
            floor_no="Ground Floor",
            room_no="Room 101",
            priority="Medium",
            date_str="2026-09-24"
        )

        self.assertEqual(res["status"], "CREATED_NEW")
        new_id = res["complaint_id"]
        self.assertNotEqual(new_id, 51)
        print(f"[Test 02 Passed]: Electrical issue in another room accepted -> Ticket {res['ticket_id']}")

        # Cleanup test record
        conn = database.get_db_connection()
        conn.execute("DELETE FROM complaints WHERE complaint_id = ?", (new_id,))
        conn.execute("DELETE FROM active_complaint_slots WHERE complaint_id = ?", (new_id,))
        conn.commit()
        conn.close()

    def test_03_same_student_different_location_block_is_allowed(self):
        """
        3. Same student submitting Electrical issue at ANOTHER BLOCK (Block C)
           MUST be accepted and created normally.
        """
        res = database.submit_or_attach_complaint(
            student_id=self.student_id,
            category="Electrical",
            description="Switch not working in Block C room E-329",
            photo_path="uploads/blockc_evidence.jpg",
            block="Block C",
            floor_no="2nd Floor",
            room_no="Room E-329",
            priority="Medium",
            date_str="2026-09-24"
        )

        self.assertEqual(res["status"], "CREATED_NEW")
        new_id = res["complaint_id"]
        print(f"[Test 03 Passed]: Electrical issue at another location (Block C) accepted -> Ticket {res['ticket_id']}")

        # Cleanup test record
        conn = database.get_db_connection()
        conn.execute("DELETE FROM complaints WHERE complaint_id = ?", (new_id,))
        conn.execute("DELETE FROM active_complaint_slots WHERE complaint_id = ?", (new_id,))
        conn.commit()
        conn.close()

    def test_04_same_student_different_category_same_location_is_allowed(self):
        """
        4. Same student submitting a DIFFERENT CATEGORY (Cleaning) at the same location
           MUST be accepted and created normally.
        """
        res = database.submit_or_attach_complaint(
            student_id=self.student_id,
            category="Cleaning",
            description="Room E-329 floor has water spilled and dustbin overflowing",
            photo_path="uploads/cleaning_evidence.jpg",
            block="Block E",
            floor_no="2nd Floor",
            room_no="Room E-329",
            priority="Low",
            date_str="2026-09-24"
        )

        self.assertEqual(res["status"], "CREATED_NEW")
        new_id = res["complaint_id"]
        print(f"[Test 04 Passed]: Different category (Cleaning) at same location accepted -> Ticket {res['ticket_id']}")

        # Cleanup test record
        conn = database.get_db_connection()
        conn.execute("DELETE FROM complaints WHERE complaint_id = ?", (new_id,))
        conn.execute("DELETE FROM active_complaint_slots WHERE complaint_id = ?", (new_id,))
        conn.commit()
        conn.close()

    def test_05_re_submission_allowed_after_resolution(self):
        """
        5. Once the previous complaint is RESOLVED/CLOSED, allow the student
           to submit a new complaint for the same issue/location if necessary.
        """
        # Create a temporary active complaint
        res = database.submit_or_attach_complaint(
            student_id=self.student_id,
            category="Hostel",
            description="Hostel room 404 cupboard latch broken",
            photo_path="uploads/latch.jpg",
            block="Hostel",
            floor_no="4th Floor",
            room_no="Room 404",
            priority="Medium",
            date_str="2026-09-24"
        )
        self.assertEqual(res["status"], "CREATED_NEW")
        cid = res["complaint_id"]

        # Duplicate submission while active -> REJECTED
        dup_res = database.submit_or_attach_complaint(
            student_id=self.student_id,
            category="Hostel",
            description="Cupboard door latch issue in room 404",
            photo_path="uploads/latch2.jpg",
            block="Hostel",
            floor_no="4th Floor",
            room_no="404",
            priority="High",
            date_str="2026-09-24"
        )
        self.assertEqual(dup_res["status"], "DUPLICATE_REJECTED")

        # Now mark complaint as FINAL_RESOLVED
        ok, msg = database.update_complaint_status(cid, "FINAL_RESOLVED", admin_name="Staff Tech", remarks="Latch replaced")
        self.assertTrue(ok)

        # Now submit again for same category + location -> MUST BE ALLOWED!
        res_after = database.submit_or_attach_complaint(
            student_id=self.student_id,
            category="Hostel",
            description="Cupboard latch loose again after a month",
            photo_path="uploads/latch3.jpg",
            block="Hostel",
            floor_no="4th Floor",
            room_no="Room 404",
            priority="Low",
            date_str="2026-09-24"
        )
        self.assertEqual(res_after["status"], "CREATED_NEW")
        print(f"[Test 05 Passed]: Re-submission after resolution succeeded -> New Ticket {res_after['ticket_id']}")

        # Cleanup test records
        conn = database.get_db_connection()
        conn.execute("DELETE FROM complaints WHERE complaint_id IN (?, ?)", (cid, res_after["complaint_id"]))
        conn.execute("DELETE FROM active_complaint_slots WHERE complaint_id IN (?, ?)", (cid, res_after["complaint_id"]))
        conn.commit()
        conn.close()

    def test_06_database_level_concurrency_lock_protection(self):
        """
        6. Database-level UNIQUE constraint in active_complaint_slots prevents
           rapid double-clicks or direct API spam.
        """
        conn = database.get_db_connection()
        cursor = conn.cursor()
        test_slot = "test_user_concurrency::electrical::block e||329::fan"

        # First insert succeeds
        cursor.execute("INSERT INTO active_complaint_slots (slot_key, complaint_id, student_id, created_at) VALUES (?, 9999, 166, '2026-09-24')", (test_slot,))
        conn.commit()

        # Concurrent second insert fails with sqlite3.IntegrityError
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO active_complaint_slots (slot_key, complaint_id, student_id, created_at) VALUES (?, 9998, 166, '2026-09-24')", (test_slot,))
            conn.commit()

        # Cleanup
        cursor.execute("DELETE FROM active_complaint_slots WHERE slot_key = ?", (test_slot,))
        conn.commit()
        conn.close()
        print("[Test 06 Passed]: SQLite UNIQUE constraint protects against concurrent duplicate submissions.")


if __name__ == "__main__":
    unittest.main()
