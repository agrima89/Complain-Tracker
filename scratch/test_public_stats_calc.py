import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import datetime
import database

def parse_flexible_dt(val):
    if not val:
        return None
    val = str(val).strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%d-%m-%Y %H:%M:%S', '%d/%m/%Y'):
        try:
            return datetime.strptime(val, fmt)
        except (ValueError, TypeError):
            continue
    return None

conn = database.get_db_connection()
total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'").fetchone()[0]
rate = round((resolved / total) * 100.0, 1) if total > 0 else 0.0
print("Total complaints:", total)
print("Resolved complaints:", resolved)
print("Resolution Rate:", rate, "%")

complaint_rows = conn.execute("SELECT complaint_id, date, last_updated FROM complaints").fetchall()
history_rows = conn.execute("SELECT complaint_id, old_status, new_status, admin_name, admin_id, changed_at FROM complaint_status_history ORDER BY history_id ASC").fetchall()
notes_rows = conn.execute("SELECT complaint_id, created_at FROM admin_notes ORDER BY note_id ASC").fetchall()
conn.close()

submission_map = {}
response_map = {}

for h in history_rows:
    cid = h['complaint_id']
    if h['old_status'] is None or h['admin_name'] == 'Student (Submission)':
        if cid not in submission_map:
            submission_map[cid] = h['changed_at']
    else:
        if cid not in response_map:
            response_map[cid] = h['changed_at']

for n in notes_rows:
    cid = n['complaint_id']
    if cid not in response_map:
        response_map[cid] = n['created_at']

durations = []
for c in complaint_rows:
    cid = c['complaint_id']
    sub_str = submission_map.get(cid) or c['date'] or c['last_updated']
    resp_str = response_map.get(cid)
    if sub_str and resp_str:
        sub_dt = parse_flexible_dt(sub_str)
        resp_dt = parse_flexible_dt(resp_str)
        if sub_dt and resp_dt and resp_dt >= sub_dt:
            sec = (resp_dt - sub_dt).total_seconds()
            durations.append(sec)
            print(f"Complaint {cid}: Sub={sub_dt} Resp={resp_dt} Diff={sec}s ({sec/3600:.2f}h)")

if durations:
    avg_sec = sum(durations) / len(durations)
    avg_hours = avg_sec / 3600.0
    print(f"Average response seconds: {avg_sec:.1f}, hours: {avg_hours:.2f}")
else:
    print("No responses yet, average response: --")
