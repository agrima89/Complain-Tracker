import os
import sys
import sqlite3

# Set up paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import database
import pdf_generator

database.create_database()
conn = database.get_db_connection()

# Fetch an existing complaint or create a test one
complaint = conn.execute("SELECT complaints.*, students.name as student_name, students.email as student_email FROM complaints JOIN students ON complaints.student_id = students.student_id LIMIT 1").fetchone()

if not complaint:
    # Insert a dummy student and complaint
    conn.execute("INSERT OR IGNORE INTO students (student_id, name, email, password) VALUES (999, 'Agrima Bajpai', 'agrima89@culkomail.in', 'test')")
    conn.execute("""
        INSERT OR IGNORE INTO complaints 
        (complaint_id, ticket_id, student_id, category, description, photo_path, block, floor_no, room_no, corridor_side, nearby_area, additional_location, location, priority, status, date, last_updated)
        VALUES (1023, 'CMP-2026-1023', 999, 'Electrical', 'Projector in room 302 not turning on and sparking near switchboard.', '', 'Block B', '3rd Floor', '302', 'North Corridor', 'Near Water Dispenser', 'Please inspect soon', 'Block B, 3rd Floor, Room 302', 'High', 'In Progress', '2026-09-15', '2026-09-15 14:30:00')
    """)
    conn.commit()
    complaint = conn.execute("SELECT complaints.*, students.name as student_name, students.email as student_email FROM complaints JOIN students ON complaints.student_id = students.student_id WHERE complaint_id = 1023").fetchone()

history = database.get_complaint_history(complaint["complaint_id"])

# 1. Test Individual Complaint PDF
out_pdf_name = pdf_generator.get_pdf_filename(complaint["complaint_id"], complaint["student_name"])
out_pdf_path = os.path.join(BASE_DIR, "scratch", out_pdf_name)

print(f"Testing individual PDF generation: {out_pdf_name}")
with open(out_pdf_path, "wb") as f:
    pdf_generator.generate_complaint_pdf(complaint, history, f)

assert os.path.isfile(out_pdf_path), "PDF file was not created!"
size = os.path.getsize(out_pdf_path)
print(f"Generated {out_pdf_name} successfully! Size: {size} bytes.")

# 2. Test Admin Summary Report PDF
stats = database.get_admin_statistics()
analytics = database.get_analytics_data()
all_complaints = database.get_all_complaints_for_report()

summary_pdf_name = pdf_generator.get_summary_pdf_filename()
summary_pdf_path = os.path.join(BASE_DIR, "scratch", summary_pdf_name)

print(f"Testing summary PDF generation: {summary_pdf_name}")
with open(summary_pdf_path, "wb") as f:
    pdf_generator.generate_admin_summary_pdf(
        stats=stats,
        category_stats=analytics["by_category"],
        priority_stats=analytics["by_priority"],
        complaints_list=all_complaints,
        admin_name="Administrator",
        output_stream=f
    )

assert os.path.isfile(summary_pdf_path), "Summary PDF file was not created!"
summary_size = os.path.getsize(summary_pdf_path)
print(f"Generated {summary_pdf_name} successfully! Size: {summary_size} bytes.")

print("ALL PDF ENGINE TESTS PASSED!")
