import os

DATABASE_PY = r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\database.py"

with open(DATABASE_PY, "r", encoding="utf-8") as f:
    content = f.read()

# Fix statuses
old_status_logic = """    # 3. By Status
    status_rows = conn.execute("SELECT status, COUNT(*) as count FROM complaints GROUP BY status").fetchall()
    by_status = {"Pending": 0, "In Progress": 0, "Resolved": 0}
    for row in status_rows:
        by_status[row["status"]] = row["count"]
    statuses_list = [{"status": s, "count": by_status[s]} for s in ["Pending", "In Progress", "Resolved"]]"""

new_status_logic = """    # 3. By Status
    status_rows = conn.execute("SELECT status, COUNT(*) as count FROM complaints GROUP BY status").fetchall()
    by_status = {"Pending": 0, "In Progress": 0, "Resolved": 0}
    for row in status_rows:
        s = row["status"]
        if s in ("NEW", "FORWARDED"):
            by_status["Pending"] += row["count"]
        elif s in ("IN_PROGRESS", "REOPENED"):
            by_status["In Progress"] += row["count"]
        elif s in ("FINAL_RESOLVED", "RESOLUTION_SUBMITTED", "AWAITING_STUDENT_CONFIRMATION"):
            by_status["Resolved"] += row["count"]
    statuses_list = [{"status": s, "count": by_status[s]} for s in ["Pending", "In Progress", "Resolved"]]"""

content = content.replace(old_status_logic, new_status_logic)

with open(DATABASE_PY, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied patch_db2 successfully.")
