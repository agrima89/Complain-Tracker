import sys
with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('def get_admin_statistics(department=None):')
end = content.find('def get_transport_statistics():', start)
if start == -1 or end == -1:
    print('Could not find get_admin_statistics')
    sys.exit(1)

new_func = '''def get_admin_statistics(department=None):
    conn = get_db_connection()
    where = "WHERE (is_primary = 1 OR group_id IS NULL)"
    if department:
        where += " AND department = ?"
        params = (department,)
    else:
        params = ()

    # 1. Unique Grievances (Total Master Complaints)
    total = conn.execute(f"SELECT COUNT(*) FROM complaints {where}", params).fetchone()[0]

    # 2 & 3. Student Reports and Students Affected
    # Only count reporters that belong to a valid active master complaint
    # (to prevent double counting if an old/merged record still has reporters)
    if department:
        total_reports = conn.execute(f"""
            SELECT COUNT(*) FROM complaint_reporters cr
            JOIN complaints c ON cr.complaint_id = c.complaint_id
            {where}
        """, params).fetchone()[0]
        students_affected = conn.execute(f"""
            SELECT COUNT(DISTINCT cr.student_id) FROM complaint_reporters cr
            JOIN complaints c ON cr.complaint_id = c.complaint_id
            {where}
        """, params).fetchone()[0]
    else:
        total_reports = conn.execute(f"""
            SELECT COUNT(*) FROM complaint_reporters cr
            JOIN complaints c ON cr.complaint_id = c.complaint_id
            {where}
        """, params).fetchone()[0]
        students_affected = conn.execute(f"""
            SELECT COUNT(DISTINCT cr.student_id) FROM complaint_reporters cr
            JOIN complaints c ON cr.complaint_id = c.complaint_id
            {where}
        """, params).fetchone()[0]

    # Ensure reports/affected are at least equal to master complaints count
    total_reports = max(total_reports, total)
    students_affected = max(students_affected, total)
    
    # 4. Pending Action
    # The application uses NEW, FORWARDED, RESOLUTION_SUBMITTED, AWAITING_STUDENT_CONFIRMATION for Pending Action
    # Let's count them according to the rules defined previously.
    where_pending = f"{where} AND status IN ('NEW', 'FORWARDED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION')"
    pending = conn.execute(f"SELECT COUNT(*) FROM complaints {where_pending}", params).fetchone()[0]
    
    where_in_progress = f"{where} AND status IN ('IN_PROGRESS', 'REOPENED')"
    in_progress = conn.execute(f"SELECT COUNT(*) FROM complaints {where_in_progress}", params).fetchone()[0]
    
    where_resolved = f"{where} AND status = 'FINAL_RESOLVED'"
    resolved = conn.execute(f"SELECT COUNT(*) FROM complaints {where_resolved}", params).fetchone()[0]

    # Count escalated items (High Priority + status != 'FINAL_RESOLVED' older than 48 hours)
    from datetime import datetime, timedelta
    threshold_dt = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
    threshold_date = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d")

    where_escalated = f"{where} AND priority = 'High' AND status != 'FINAL_RESOLVED' AND (date < ? OR (last_updated != '' AND last_updated < ?))"
    params_escalated = params + (threshold_date, threshold_dt)
    escalated = conn.execute(f"SELECT COUNT(*) FROM complaints {where_escalated}", params_escalated).fetchone()[0]

    conn.close()
    return {
        "total": total,
        "unique_complaints": total,
        "total_reports": total_reports,
        "students_affected": students_affected,
        "pending": pending,
        "new": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "final_resolved": resolved,
        "escalated": escalated
    }

'''

content = content[:start] + new_func + content[end:]
with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched get_admin_statistics successfully!')
