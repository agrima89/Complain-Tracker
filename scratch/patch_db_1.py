import re

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update VALID_STATUSES
content = content.replace('VALID_STATUSES = ["Pending", "In Progress", "Resolved"]',
                          'VALID_STATUSES = ["NEW", "FORWARDED", "IN_PROGRESS", "RESOLVED_BY_DEPARTMENT", "AWAITING_STUDENT_CONFIRMATION", "REGENERATED", "FINAL_RESOLVED"]')

# 2. Add log_soc_event function right after check_is_escalated (just a place to put it)
soc_func = """
def log_soc_event(event_type, user_email, complaint_id, department, severity="LOW", details=""):
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO soc_audit_logs (event_type, user_email, complaint_id, department, severity, timestamp, details) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (event_type, user_email, str(complaint_id) if complaint_id else "", department, severity, now, details)
    )
    conn.commit()
    conn.close()
"""
if 'def log_soc_event' not in content:
    content += "\n" + soc_func

# 3. Add complaint workflow functions
workflow_funcs = """
def forward_complaint(complaint_id, department, admin_name, admin_id, reason):
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE complaints SET department = ?, forwarded_to = ?, forwarded_by = ?, forwarded_at = ?, status = 'FORWARDED', last_updated = ? WHERE complaint_id = ?",
        (department, department, admin_name, now, now, complaint_id)
    )
    conn.execute(
        "INSERT INTO complaint_status_history (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at) VALUES (?, ?, ?, (SELECT status FROM complaints WHERE complaint_id = ?), 'FORWARDED', ?, ?)",
        (complaint_id, admin_id, admin_name, complaint_id, f"Forwarded to {department}. Reason: {reason}", now)
    )
    conn.commit()
    conn.close()
    return True, "Complaint forwarded successfully."

def mark_resolved_by_department(complaint_id, admin_name, admin_id, remarks):
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE complaints SET resolved_by_department = 1, department_resolution_time = ?, status = 'AWAITING_STUDENT_CONFIRMATION', last_updated = ? WHERE complaint_id = ?",
        (now, now, complaint_id)
    )
    conn.execute(
        "INSERT INTO complaint_status_history (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at) VALUES (?, ?, ?, (SELECT status FROM complaints WHERE complaint_id = ?), 'AWAITING_STUDENT_CONFIRMATION', ?, ?)",
        (complaint_id, admin_id, admin_name, complaint_id, f"Resolved by department. Remarks: {remarks}", now)
    )
    conn.commit()
    conn.close()
    return True, "Complaint marked as resolved by department."

def confirm_resolution(complaint_id, student_id):
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Verify student
    comp = conn.execute("SELECT student_id FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
    if not comp or comp['student_id'] != student_id:
        conn.close()
        return False, "Unauthorized"

    conn.execute(
        "UPDATE complaints SET student_confirmation = 'confirmed', student_confirmation_time = ?, final_resolution_time = ?, status = 'FINAL_RESOLVED', last_updated = ? WHERE complaint_id = ?",
        (now, now, now, complaint_id)
    )
    conn.execute(
        "INSERT INTO complaint_status_history (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at) VALUES (?, NULL, 'Student', 'AWAITING_STUDENT_CONFIRMATION', 'FINAL_RESOLVED', 'Student confirmed resolution.', ?)",
        (complaint_id, now)
    )
    conn.commit()
    conn.close()
    return True, "Resolution confirmed."

def regenerate_complaint(complaint_id, student_id, reason, new_photo):
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    comp = conn.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
    if not comp or comp['student_id'] != student_id:
        conn.close()
        return False, "Unauthorized"

    new_count = (comp['regeneration_count'] or 0) + 1
    new_ticket_id = f"{comp['ticket_id']}-R{new_count}"

    conn.execute(
        "UPDATE complaints SET status = 'REGENERATED', regenerated_by_student = 1, regeneration_count = ?, regeneration_reason = ?, previous_resolution_details = ?, photo_path = ?, ticket_id = ?, last_updated = ? WHERE complaint_id = ?",
        (new_count, reason, f"Previously resolved by department at {comp['department_resolution_time']}", new_photo or comp['photo_path'], new_ticket_id, now, complaint_id)
    )
    
    conn.execute(
        "INSERT INTO complaint_status_history (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at) VALUES (?, NULL, 'Student', 'AWAITING_STUDENT_CONFIRMATION', 'REGENERATED', ?, ?)",
        (complaint_id, f"Student regenerated complaint. Reason: {reason}", now)
    )
    conn.commit()
    conn.close()
    return True, "Complaint regenerated."
"""
if 'def forward_complaint' not in content:
    content += "\n" + workflow_funcs

# Write back
with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Appended new functions and constants.")
