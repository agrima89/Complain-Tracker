import os
import re

DATABASE_PY = r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\database.py"

with open(DATABASE_PY, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Critical Unresolved Issues in get_campus_pulse_data
content = content.replace(
    "WHERE priority = 'High' AND status IN ('Pending', 'In Progress')",
    "WHERE priority = 'High' AND status IN ('NEW', 'FORWARDED', 'IN_PROGRESS', 'REOPENED')"
)

# 2. Update Top Problem Area in get_campus_pulse_data
content = content.replace(
    """        WHERE status IN ('Pending', 'In Progress')
        GROUP BY loc_name
        ORDER BY active_cnt DESC, high_cnt DESC
        LIMIT 1
    \"\"\")
    top_area_row = cur.fetchone()
    if top_area_row:
        problem_area = {
            "name": top_area_row["loc_name"],
            "active_count": top_area_row["active_cnt"],
            "high_priority_count": top_area_row["high_cnt"]
        }
        top_area_str = f"{problem_area['name']} ({problem_area['active_count']} complaints)"
    else:
        problem_area = {
            "name": "None (All Clear)",
            "active_count": 0,
            "high_priority_count": 0
        }
        top_area_str = "All Zones Normal\"\"\"""",
    """        WHERE status IN ('NEW', 'FORWARDED', 'IN_PROGRESS', 'REOPENED')
        GROUP BY loc_name
        ORDER BY active_cnt DESC, high_cnt DESC
        LIMIT 1
    \"\"\")
    top_area_row = cur.fetchone()
    if top_area_row and top_area_row["active_cnt"] > 0:
        problem_area = {
            "name": top_area_row["loc_name"],
            "active_count": top_area_row["active_cnt"],
            "high_priority_count": top_area_row["high_cnt"]
        }
        top_area_str = f"{problem_area['name']} ({problem_area['active_count']} complaints)"
    else:
        problem_area = {
            "name": "No complaints recorded",
            "active_count": 0,
            "high_priority_count": 0
        }
        top_area_str = "No complaints recorded" """
)

# 3. Update Escalations
content = content.replace(
    "WHERE priority = 'High' AND status != 'Resolved'",
    "WHERE priority = 'High' AND status != 'FINAL_RESOLVED'"
)

# 4. Average turnaround logic
avg_turnaround_code = """
    # Real DB calculation for avg resolution days
    cur.execute(\"\"\"
        SELECT AVG(julianday(last_updated) - julianday(date)) 
        FROM complaints 
        WHERE status = 'FINAL_RESOLVED' AND last_updated != '' AND date != ''
    \"\"\")
    avg_turnaround = cur.fetchone()[0]
    avg_resolution_days = round(float(avg_turnaround), 1) if avg_turnaround is not None else "N/A"
    
    conn.close()"""

content = content.replace("    conn.close()", avg_turnaround_code, 1)

# 5. Fix return dictionary of get_campus_pulse_data
content = content.replace(
    """        "escalated_count": escalated_count,
        "avg_resolution_days": 2.4,
        "status_breakdown": {
            "Pending": pending,
            "In Progress": in_progress,
            "Resolved": resolved
        },""",
    """        "escalated_count": escalated_count,
        "avg_resolution_days": avg_resolution_days,
        "status_breakdown": {
            "Pending": pending,
            "In Progress": in_progress,
            "Resolved": resolved
        },"""
)

with open(DATABASE_PY, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied patch_db1 successfully.")
