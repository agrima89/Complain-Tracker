import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from app import app
import database

class TestDepartmentIsolation(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

    def test_department_accounts_exist_and_authenticate(self):
        departments = [
            ("electrical_admin", "electrical123", "Electrical"),
            ("electrical", "electrical123", "Electrical"),
            ("cleaning_admin", "cleaning123", "Cleaning"),
            ("cleaning", "cleaning123", "Cleaning"),
            ("hostel_admin", "hostel123", "Hostel"),
            ("wifi_admin", "wifi123", "Wi-Fi/Internet"),
            ("library_admin", "library123", "Library"),
            ("infra_admin", "infra123", "Infrastructure"),
            ("transport_admin", "transport123", "Transport"),
            ("other_admin", "other123", "Other"),
            ("admin", "admin123", "")
        ]
        for uname, pwd, expected_dept in departments:
            admin = database.authenticate_admin(uname, pwd)
            self.assertIsNotNone(admin, f"Failed to authenticate {uname}")
            self.assertEqual(admin["department"], expected_dept, f"Mismatched department for {uname}")

    def _create_test_pair(self):
        conn = database.get_db_connection()
        s = conn.execute("SELECT student_id FROM students LIMIT 1").fetchone()
        student_id = s[0] if s else 1
        conn.close()

        cid_elec, _ = database.create_complaint(
            student_id=student_id,
            category="Electrical",
            description="Test electrical wiring issue in lab",
            block="Block B"
        )
        cid_clean, _ = database.create_complaint(
            student_id=student_id,
            category="Cleaning",
            description="Test corridor needs immediate cleaning",
            block="Block A"
        )
        return cid_elec, cid_clean

    def test_complaint_auto_assignment(self):
        cid_elec, cid_clean = self._create_test_pair()
        comp_elec = database.get_complaint_by_id(cid_elec)
        self.assertEqual(comp_elec["department"], "Electrical")
        comp_clean = database.get_complaint_by_id(cid_clean)
        self.assertEqual(comp_clean["department"], "Cleaning")

    def test_dashboard_isolation(self):
        # 1. Login as electrical_admin
        with self.client.session_transaction() as sess:
            admin = database.authenticate_admin("electrical_admin", "electrical123")
            sess["admin_id"] = admin["admin_id"]
            sess["admin_username"] = admin["username"]
            sess["admin_role"] = admin["role"]
            sess["admin_department"] = admin["department"]

        res = self.client.get("/admin/dashboard")
        self.assertEqual(res.status_code, 200)
        content = res.get_data(as_text=True)
        self.assertIn("ELECTRICAL DEPARTMENT COMMAND CENTER", content)

        # 2. Check complaints pagination scoped to electrical
        items = database.get_all_complaints_admin_paginated(department="Electrical")["items"]
        for it in items:
            self.assertEqual(it["department"], "Electrical")

        # 3. Check cleaning admin sees only cleaning complaints
        with self.client.session_transaction() as sess:
            clean_admin = database.authenticate_admin("cleaning_admin", "cleaning123")
            sess["admin_id"] = clean_admin["admin_id"]
            sess["admin_username"] = clean_admin["username"]
            sess["admin_role"] = clean_admin["role"]
            sess["admin_department"] = clean_admin["department"]

        res_clean = self.client.get("/admin/dashboard")
        self.assertEqual(res_clean.status_code, 200)
        clean_content = res_clean.get_data(as_text=True)
        self.assertIn("CLEANING DEPARTMENT COMMAND CENTER", clean_content)

        clean_items = database.get_all_complaints_admin_paginated(department="Cleaning")["items"]
        for it in clean_items:
            self.assertEqual(it["department"], "Cleaning")

    def test_unauthorized_complaint_access_blocked(self):
        cid_elec, cid_clean = self._create_test_pair()

        # Login as electrical_admin
        with self.client.session_transaction() as sess:
            admin = database.authenticate_admin("electrical_admin", "electrical123")
            sess["admin_id"] = admin["admin_id"]
            sess["admin_username"] = admin["username"]
            sess["admin_role"] = admin["role"]
            sess["admin_department"] = admin["department"]

        # Attempt to access cleaning complaint detail
        res = self.client.get(f"/admin/complaint/{cid_clean}", follow_redirects=True)
        self.assertIn("Access Denied", res.get_data(as_text=True))

        # Attempt to access cleaning complaint PDF
        res_pdf = self.client.get(f"/admin/complaint/{cid_clean}/pdf", follow_redirects=True)
        self.assertIn("Access Denied", res_pdf.get_data(as_text=True))

        # Attempt to update status of cleaning complaint
        res_upd = self.client.post("/admin/api/update-status", json={
            "complaint_id": cid_clean,
            "status": "IN_PROGRESS"
        })
        self.assertEqual(res_upd.status_code, 403)
        self.assertIn("Access Denied", res_upd.get_json()["message"])

        # But can access electrical complaint detail
        res_ok = self.client.get(f"/admin/complaint/{cid_elec}")
        self.assertEqual(res_ok.status_code, 200)

    def test_super_admin_has_global_access(self):
        conn = database.get_db_connection()
        s = conn.execute("SELECT student_id FROM students LIMIT 1").fetchone()
        student_id = s[0] if s else 1
        conn.close()

        cid_elec, _ = database.create_complaint(student_id=student_id, category="Electrical", description="Super Admin Elec test", block="Block A")
        cid_clean, _ = database.create_complaint(student_id=student_id, category="Cleaning", description="Super Admin Clean test", block="Block B")

        # Login as Super Admin
        with self.client.session_transaction() as sess:
            admin = database.authenticate_admin("admin", "admin123")
            sess["admin_id"] = admin["admin_id"]
            sess["admin_username"] = admin["username"]
            sess["admin_role"] = admin["role"]
            sess["admin_department"] = admin["department"]

        # Super Admin sees global dashboard
        res = self.client.get("/admin/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn("ADMINISTRATIVE COMMAND CENTER", res.get_data(as_text=True))

        # Super Admin can view electrical complaint
        res_elec = self.client.get(f"/admin/complaint/{cid_elec}")
        self.assertEqual(res_elec.status_code, 200)

        # Super Admin can view cleaning complaint
        res_clean = self.client.get(f"/admin/complaint/{cid_clean}")
        self.assertEqual(res_clean.status_code, 200)

        # Super Admin summary report generates successfully
        res_rep = self.client.get("/admin/report/pdf")
        self.assertEqual(res_rep.status_code, 200)
        self.assertEqual(res_rep.mimetype, "application/pdf")

if __name__ == "__main__":
    unittest.main()
