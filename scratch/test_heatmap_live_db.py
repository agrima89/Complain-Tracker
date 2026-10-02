import os
import sys
import unittest
import json

# Setup workspace path
sys.path.insert(0, os.path.abspath("."))
import database
import app as flask_app

class TestCampusHeatmapLiveDatabase(unittest.TestCase):
    def setUp(self):
        self.app = flask_app.app.test_client()
        self.app.testing = True

    def test_01_live_database_zone_counts(self):
        """Verify that every zone in heatmap_data matches the actual database query counts."""
        zones = database.get_campus_heatmap_data()
        self.assertEqual(len(zones), 12, "Should return 12 canonical campus zones")

        conn = database.get_db_connection()
        total_db_complaints = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
        conn.close()

        sum_zone_totals = sum(z["total_complaints"] for z in zones)
        sum_zone_unresolved = sum(z["unresolved_count"] for z in zones)
        sum_zone_resolved = sum(z["resolved_count"] for z in zones)

        self.assertEqual(sum_zone_totals, total_db_complaints, f"Sum of zone complaints ({sum_zone_totals}) must match DB count ({total_db_complaints})")
        self.assertEqual(sum_zone_totals, sum_zone_unresolved + sum_zone_resolved, "Total must equal unresolved + resolved")

        for z in zones:
            self.assertIn("id", z)
            self.assertIn("name", z)
            self.assertIn("total_complaints", z)
            self.assertIn("unresolved_count", z)
            self.assertIn("top_category", z)
            self.assertIn("intensity", z)
            self.assertIn("complaints", z)
            self.assertEqual(len(z["complaints"]), z["total_complaints"])

            if z["total_complaints"] == 0:
                self.assertEqual(z["unresolved_count"], 0)
                self.assertEqual(z["top_category"], "None Recorded")
                self.assertEqual(z["intensity"], "Low")
                self.assertEqual(len(z["complaints"]), 0)
            else:
                self.assertNotEqual(z["top_category"], "None Recorded")
                # Check first complaint properties
                c0 = z["complaints"][0]
                self.assertIn("ticket_id", c0)
                self.assertIn("student_name", c0)
                self.assertIn("category", c0)
                self.assertIn("description", c0)
                self.assertIn("location", c0)
                self.assertIn("priority", c0)
                self.assertIn("status", c0)
                self.assertIn("date", c0)

        print(f"[TEST 1 PASS] Heatmap Zone Telemetry matches DB: Total {sum_zone_totals} complaints across 12 zones.")

    def test_02_api_endpoints_with_admin_auth(self):
        """Verify /api/admin/zone-telemetry, /api/admin/heatmap, and /api/admin/zone/<id>."""
        with self.app.session_transaction() as sess:
            sess["admin_id"] = 1
            sess["admin_username"] = "admin"

        # Test /api/admin/zone-telemetry
        resp1 = self.app.get("/api/admin/zone-telemetry")
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.get_json()
        self.assertTrue(data1["success"])
        self.assertEqual(len(data1["zones"]), 12)

        # Test /api/admin/heatmap
        resp2 = self.app.get("/api/admin/heatmap")
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.get_json()
        self.assertEqual(data1["zones"], data2["zones"])

        # Test /api/admin/zone/block-b
        resp3 = self.app.get("/api/admin/zone/block-b")
        self.assertEqual(resp3.status_code, 200)
        data3 = resp3.get_json()
        self.assertTrue(data3["success"])
        self.assertEqual(data3["zone"]["name"], "Block B")
        self.assertIn("complaints", data3["zone"])

        print("[TEST 2 PASS] API Endpoints (/api/admin/zone-telemetry & /api/admin/zone/<id>) return valid JSON.")

    def test_03_admin_dashboard_render(self):
        """Verify Admin Dashboard HTML renders with live heatmap data and complaint cards."""
        with self.app.session_transaction() as sess:
            sess["admin_id"] = 1
            sess["admin_username"] = "admin"

        resp = self.app.get("/admin/dashboard")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)

        self.assertIn("Campus Problem Heatmap & Zone Telemetry", html)
        self.assertIn("campusHeatmapSvg", html)
        self.assertIn("zoneInspectorDrawer", html)
        self.assertIn("zoneComplaintsContainer", html)
        self.assertIn("id=\"heatmapData\"", html)

        print("[TEST 3 PASS] Admin Dashboard renders live SVG heatmap and Zone Telemetry Inspector.")

    def test_04_lifecycle_zone_count_and_status_transition(self):
        """Test submitting a complaint to Block D (initially 0 complaints) and updating status."""
        conn = database.get_db_connection()
        student = conn.execute("SELECT student_id FROM students LIMIT 1").fetchone()
        student_id = student["student_id"] if student else 1
        conn.close()

        # Check initial Block D count
        zones_before = {z["name"]: z for z in database.get_campus_heatmap_data()}
        d_before_total = zones_before["Block D"]["total_complaints"]
        d_before_unresolved = zones_before["Block D"]["unresolved_count"]

        # 1. Submit complaint in Block D
        cid, ticket_id = database.create_complaint(
            student_id=student_id,
            category="Electrical",
            description="Projector lamp flickering in Media Studio Room D-104",
            block="Block D",
            room_no="D-104",
            floor_no="1st Floor",
            corridor_side="RHS",
            priority="High"
        )

        try:
            zones_after_sub = {z["name"]: z for z in database.get_campus_heatmap_data()}
            d_after_sub = zones_after_sub["Block D"]

            self.assertEqual(d_after_sub["total_complaints"], d_before_total + 1)
            self.assertEqual(d_after_sub["unresolved_count"], d_before_unresolved + 1)
            self.assertEqual(d_after_sub["top_category"], "Electrical")
            self.assertEqual(d_after_sub["high_priority_count"], zones_before["Block D"]["high_priority_count"] + 1)

            # Check that the complaint appears in Block D's complaints list
            matching = [c for c in d_after_sub["complaints"] if c["complaint_id"] == cid]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0]["ticket_id"], ticket_id)
            self.assertEqual(matching[0]["priority"], "High")
            self.assertEqual(matching[0]["status"], "Pending")

            # 2. Change status to Resolved
            database.update_complaint_status(
                complaint_id=cid,
                new_status="Resolved",
                admin_id=1,
                admin_name="Facility Head",
                remarks="Projector lamp replaced."
            )

            zones_after_res = {z["name"]: z for z in database.get_campus_heatmap_data()}
            d_after_res = zones_after_res["Block D"]

            self.assertEqual(d_after_res["total_complaints"], d_before_total + 1)
            self.assertEqual(d_after_res["unresolved_count"], d_before_unresolved)
            self.assertEqual(d_after_res["resolved_count"], zones_before["Block D"]["resolved_count"] + 1)

            res_matching = [c for c in d_after_res["complaints"] if c["complaint_id"] == cid]
            self.assertEqual(res_matching[0]["status"], "Resolved")

            print(f"[TEST 4 PASS] Lifecycle transition passed: Block D total={d_after_res['total_complaints']}, unresolved={d_after_res['unresolved_count']}, resolved={d_after_res['resolved_count']}.")

        finally:
            # Clean up test complaint
            conn = database.get_db_connection()
            conn.execute("DELETE FROM complaint_status_history WHERE complaint_id=?", (cid,))
            conn.execute("DELETE FROM admin_notes WHERE complaint_id=?", (cid,))
            conn.execute("DELETE FROM complaints WHERE complaint_id=?", (cid,))
            conn.commit()
            conn.close()

if __name__ == "__main__":
    unittest.main()
