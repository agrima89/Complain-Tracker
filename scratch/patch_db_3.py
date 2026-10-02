import json

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_get_public_stats = """def get_public_statistics():
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'FINAL_RESOLVED'").fetchone()[0]
    students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'IN_PROGRESS'").fetchone()[0]
    awaiting = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'AWAITING_STUDENT_CONFIRMATION'").fetchone()[0]
    open_comp = conn.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('NEW', 'FORWARDED', 'REGENERATED')").fetchone()[0]
    regenerated = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'REGENERATED'").fetchone()[0]
    
    # Department activity
    dept_rows = conn.execute("SELECT department, COUNT(*) as c FROM complaints GROUP BY department").fetchall()
    department_activity = {row['department'] or 'Unassigned': row['c'] for row in dept_rows}

    conn.close()

    resolution_rate = int((resolved / total * 100)) if total > 0 else 0

    return {
        "total_complaints": total,
        "resolved_complaints": resolved,
        "active_students": students,
        "resolution_rate": resolution_rate,
        "in_progress": in_progress,
        "awaiting": awaiting,
        "open_complaints": open_comp,
        "regenerated": regenerated,
        "department_activity": department_activity
    }"""
    
# Replace the old one which I added recently
import re
content = re.sub(r'def get_public_statistics\(\):.*?return \{.*?\}', new_get_public_stats, content, flags=re.DOTALL)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated get_public_statistics")
