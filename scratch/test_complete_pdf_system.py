import os
import sys
import io

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import app
import database
import pdf_generator

def test_pdf_routes():
    database.create_database()
    conn = database.get_db_connection()

    # 1. Ensure test student exists
    student_email = "agrima89@culkomail.in"
    student = conn.execute("SELECT * FROM students WHERE LOWER(email) = LOWER(?)", (student_email,)).fetchone()
    if not student:
        success, student_id = database.register_new_student("Agrima Bajpai", student_email, "student123")
    else:
        student_id = student["student_id"]

    # 2. Ensure test complaints exist
    # Complaint 1: In Progress with remarks
    c1_id, t1 = database.create_complaint(
        student_id=student_id,
        category="Electrical",
        description="Air conditioning unit in Lab 402 is vibrating violently and emitting smoke.",
        photo_path="",
        block="Block B",
        floor_no="4th Floor",
        room_no="Lab 402",
        corridor_side="East Wing",
        nearby_area="Next to Server Room",
        priority="High",
        date_str="2026-09-15"
    )
    database.update_complaint_status(c1_id, "In Progress", admin_id=1, admin_name="Campus Engineer", remarks="Technician dispatched to replace compressor unit.")

    # Complaint 2: Pending (no resolution remarks)
    c2_id, t2 = database.create_complaint(
        student_id=student_id,
        category="Cleaning",
        description="Water spill in hallway near library stairs needs urgent mopping.",
        photo_path="",
        block="Library",
        floor_no="1st Floor",
        room_no="",
        corridor_side="Main Staircase",
        nearby_area="Opposite Book Return Desk",
        priority="Medium",
        date_str="2026-09-15"
    )

    client = app.test_client()

    print("\n--- TEST 1: Unauthenticated Student Access ---")
    resp = client.get(f"/student/complaint/{c1_id}/pdf")
    assert resp.status_code == 302, f"Expected redirect, got {resp.status_code}"
    print("[PASS] Unauthenticated request redirected properly to login.")

    print("\n--- TEST 2: Authenticated Student PDF Download ---")
    with client.session_transaction() as sess:
        sess["student_id"] = student_id
        sess["student_name"] = "Agrima Bajpai"
        sess["student_email"] = student_email

    resp = client.get(f"/student/complaint/{c1_id}/pdf")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.content_type == "application/pdf", f"Expected application/pdf, got {resp.content_type}"
    disp = resp.headers.get("Content-Disposition", "")
    print(f"Content-Disposition: {disp}")
    assert f"Complaint_{c1_id}_Agrima_Bajpai.pdf" in disp or f"Complaint_{c1_id}" in disp
    assert resp.data.startswith(b"%PDF-"), "Invalid PDF data!"
    print(f"[PASS] Student PDF generated successfully! Bytes: {len(resp.data)}")

    print("\n--- TEST 3: Authenticated Student Pending Complaint PDF ---")
    resp = client.get(f"/student/complaint/{c2_id}/pdf")
    assert resp.status_code == 200
    assert resp.data.startswith(b"%PDF-")
    print(f"[PASS] Pending complaint PDF generated successfully! Bytes: {len(resp.data)}")

    print("\n--- TEST 4: Student Permission Check (Accessing Another Student's Complaint) ---")
    with client.session_transaction() as sess:
        sess["student_id"] = 88888  # Different student

    resp = client.get(f"/student/complaint/{c1_id}/pdf")
    assert resp.status_code == 302, "Student should not be able to access another student's complaint"
    print("[PASS] Unauthorized student properly blocked from downloading other complaints.")

    print("\n--- TEST 5: Admin Individual Complaint PDF Download ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess["admin_id"] = 1
        sess["admin_username"] = "admin"

    resp = client.get(f"/admin/complaint/{c1_id}/pdf")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.content_type == "application/pdf"
    assert resp.data.startswith(b"%PDF-")
    print(f"[PASS] Admin individual PDF downloaded successfully! Bytes: {len(resp.data)}")

    print("\n--- TEST 6: Admin Summary Report PDF Download ---")
    resp = client.get("/admin/report/pdf")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.content_type == "application/pdf"
    disp = resp.headers.get("Content-Disposition", "")
    print(f"Summary Report Content-Disposition: {disp}")
    assert "Complaint_Summary_Report" in disp
    assert resp.data.startswith(b"%PDF-")
    print(f"[PASS] Admin Summary Analytics Report PDF generated successfully! Bytes: {len(resp.data)}")

    print("\n--- TEST 7: Admin Filtered Summary Report PDF Download ---")
    resp = client.get("/admin/report/pdf?status=In+Progress&priority=High")
    assert resp.status_code == 200
    assert resp.data.startswith(b"%PDF-")
    print(f"[PASS] Admin Filtered Summary Report PDF generated successfully! Bytes: {len(resp.data)}")

    print("\n=======================================================")
    print("  ALL PDF MANAGEMENT SYSTEM TESTS COMPLETED & PASSED! ")
    print("=======================================================")

if __name__ == "__main__":
    test_pdf_routes()
