import os

DATABASE_PY = r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\database.py"

with open(DATABASE_PY, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the broken block from create_database()
broken_block = """    # Real DB calculation for avg resolution days
    cur.execute(\"\"\"
        SELECT AVG(julianday(last_updated) - julianday(date)) 
        FROM complaints 
        WHERE status = 'FINAL_RESOLVED' AND last_updated != '' AND date != ''
    \"\"\")
    avg_turnaround = cur.fetchone()[0]
    avg_resolution_days = round(float(avg_turnaround), 1) if avg_turnaround is not None else "N/A"
    
    conn.close()"""

content = content.replace(broken_block, "    conn.close()")

# Now, apply it correctly to get_campus_pulse_data
# We want to replace the `conn.close()` inside get_campus_pulse_data
old_end_of_pulse = """    for i in range(6, -1, -1):
        day_dt = now - timedelta(days=i)
        day_str = day_dt.strftime("%Y-%m-%d")
        day_label = day_dt.strftime("%a (%d %b)") if i in [0, 6] else day_dt.strftime("%a")
        
        cur.execute("SELECT COUNT(*) FROM complaints WHERE date = ?", (day_str,))
        filed_count = cur.fetchone()[0]
        
        daily_velocity.append({
            "day": day_label,
            "date": day_str,
            "filed": filed_count
        })
        velocity_7d.append({
            "day_name": day_label,
            "day": day_label,
            "date": day_str,
            "count": filed_count,
            "filed": filed_count
        })

    conn.close()"""

new_end_of_pulse = """    for i in range(6, -1, -1):
        day_dt = now - timedelta(days=i)
        day_str = day_dt.strftime("%Y-%m-%d")
        day_label = day_dt.strftime("%a (%d %b)") if i in [0, 6] else day_dt.strftime("%a")
        
        cur.execute("SELECT COUNT(*) FROM complaints WHERE date = ?", (day_str,))
        filed_count = cur.fetchone()[0]
        
        daily_velocity.append({
            "day": day_label,
            "date": day_str,
            "filed": filed_count
        })
        velocity_7d.append({
            "day_name": day_label,
            "day": day_label,
            "date": day_str,
            "count": filed_count,
            "filed": filed_count
        })

    # Real DB calculation for avg resolution days
    cur.execute(\"\"\"
        SELECT AVG(julianday(last_updated) - julianday(date)) 
        FROM complaints 
        WHERE status = 'FINAL_RESOLVED' AND last_updated != '' AND date != ''
    \"\"\")
    avg_turnaround = cur.fetchone()[0]
    avg_resolution_days = round(float(avg_turnaround), 1) if avg_turnaround is not None else "N/A"

    conn.close()"""

content = content.replace(old_end_of_pulse, new_end_of_pulse)

with open(DATABASE_PY, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied fix for patch_db1 successfully.")
