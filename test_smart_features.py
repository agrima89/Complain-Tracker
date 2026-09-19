import os
import sys
import unittest
import json

# Ensure parent directory is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import database
import smart_complaint
import pdf_generator
from app import app


class TestSmartFeaturesAndIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.create_database()
        cls.client = app.test_client()

    def test_01_smart_detection_wifi(self):
        text = "WiFi router in Block B 3rd floor computer lab is completely dead and disconnected. Needs urgent fix for lab exam."
        result = smart_complaint.analyze_complaint(text)
        self.assertTrue(result["success"])
        self.assertEqual(result["category"], "Wi-Fi/Internet")
        self.assertEqual(result["priority"], "High")
        self.assertEqual(result["location"], "Block B")
        self.assertIn("reason", result)
        print("Test 01 Passed: WiFi detection ->", result["category"], result["priority"], result["location"])

    def test_02_smart_detection_hostel_mess(self):
        text = "Hostel mess food dinner quality is extremely poor and water purifier filter in dining hall is leaking."
        result = smart_complaint.analyze_complaint(text)
        self.assertTrue(result["success"])
        self.assertIn(result["category"], ["Hostel", "Cleaning"])
        self.assertIn("Hostel", result["location"])
        print("Test 02 Passed: Hostel/Mess detection ->", result["category"], result["location"])

    def test_03_smart_detection_electricity(self):
        text = "Fan sparking and electrical switchboard burnt in Block A room 102 dangerous short circuit."
        result = smart_complaint.analyze_complaint(text)
        self.assertTrue(result["success"])
        self.assertEqual(result["category"], "Electrical")
        self.assertEqual(result["priority"], "High")
        self.assertEqual(result["location"], "Block A")
        print("Test 03 Passed: Electrical safety detection ->", result["category"], result["priority"])

    def test_04_find_similar_complaints(self):
        unresolved = database.get_unresolved_complaints_for_similarity()
        self.assertIsInstance(unresolved, list)

        res = smart_complaint.find_similar_complaints(
            description="Internet connection is broken in Block B lab",
            category="Wi-Fi/Internet",
            block="Block B"
        )
        self.assertIn("has_similar", res)
        self.assertIn("similar_complaints", res)
        print(f"Test 04 Passed: Similar search returned {len(res['similar_complaints'])} items (has_similar: {res['has_similar']})")

    def test_05_campus_heatmap_data(self):
        zones = database.get_campus_heatmap_data()
        self.assertIsInstance(zones, list)
        self.assertGreaterEqual(len(zones), 12)
        for zone in zones:
            self.assertIn("id", zone)
            self.assertIn("name", zone)
            self.assertIn("intensity", zone)
            self.assertIn("total_complaints", zone)
            self.assertIn("unresolved_count", zone)
            self.assertIn("high_priority_count", zone)
        print(f"Test 05 Passed: Heatmap data generated for {len(zones)} campus zones")

    def test_06_campus_pulse_data(self):
        pulse = database.get_campus_pulse_data()
        self.assertIn("critical_issues", pulse)
        self.assertIn("top_problem_area", pulse)
        self.assertIn("resolution_rate", pulse)
        self.assertIn("active_complaints", pulse)
        self.assertIn("velocity_7d", pulse)
        self.assertIn("status_breakdown", pulse)
        self.assertEqual(len(pulse["velocity_7d"]), 7)
        print(f"Test 06 Passed: Pulse data verified -> Resolution: {pulse['resolution_rate']}%, Active: {pulse['active_complaints']}, Top: {pulse['top_problem_area']}")

    def test_07_api_smart_detect_endpoint(self):
        resp = self.client.post(
            "/api/smart-detect",
            data=json.dumps({"text": "Projector not working in Block B seminar hall"}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["location"], "Block B")
        print("Test 07 Passed: /api/smart-detect endpoint returned 200 OK")

    def test_08_api_check_similar_endpoint(self):
        resp = self.client.post(
            "/api/check-similar",
            data=json.dumps({
                "description": "WiFi router issues in Block B",
                "category": "Wi-Fi/Internet",
                "block": "Block B"
            }),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("has_similar", data)
        print("Test 08 Passed: /api/check-similar endpoint returned 200 OK")

    def test_09_admin_dashboard_render(self):
        with self.client.session_transaction() as sess:
            sess["admin_id"] = 1
            sess["admin_username"] = "admin"

        resp = self.client.get("/admin/dashboard")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Campus Pulse & Health Telemetry", html)
        self.assertIn("Campus Problem Heatmap & Zone Telemetry", html)
        self.assertIn("campusHeatmapSvg", html)
        self.assertIn("zoneInspectorDrawer", html)
        print("Test 09 Passed: Admin dashboard rendered with Pulse and Heatmap components")

    def test_10_pdf_generator_preservation(self):
        complaints = database.get_all_complaints_admin()
        if complaints:
            c = complaints[0]
            history = database.get_complaint_history(c["complaint_id"])
            pdf_buf = pdf_generator.generate_complaint_pdf(c, history)
            self.assertIsNotNone(pdf_buf)
            self.assertGreater(len(pdf_buf.getvalue()), 1000)
            print(f"Test 10 Passed: Complaint PDF generated ({len(pdf_buf.getvalue())} bytes)")


if __name__ == "__main__":
    unittest.main()
