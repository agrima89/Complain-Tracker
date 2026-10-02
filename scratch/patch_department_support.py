import re
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, "database.py")

with open(DB_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update columns_to_add in migrate_database
old_cols = '''        ("transport_complaint_type", "TEXT DEFAULT ''")
    ]'''

new_cols = '''        ("transport_complaint_type", "TEXT DEFAULT ''"),
        ("department", "TEXT DEFAULT ''")
    ]'''

if old_cols in content:
    content = content.replace(old_cols, new_cols, 1)
    print("1. Updated columns_to_add in migrate_database")

# 2. Add department accounts and backfill to migrate_database
old_migration_end = '''    # 6. Migrate Default Admin Password to Secure Hash if Plaintext
    cursor.execute("SELECT admin_id, username, password FROM admins WHERE username = 'admin'")
    admin_row = cursor.fetchone()
    if admin_row and not admin_row["password"].startswith(("pbkdf2:", "scrypt:", "argon2:")):
        hashed_admin_pass = generate_password_hash(admin_row["password"])
        cursor.execute("UPDATE admins SET password = ? WHERE admin_id = ?", (hashed_admin_pass, admin_row["admin_id"]))
        print("[CampusCare DB] Upgraded default admin password to secure PBKDF2 hash.")

    conn.commit()'''

new_migration_end = '''    # 6. Migrate Default Admin Password to Secure Hash if Plaintext
    cursor.execute("SELECT admin_id, username, password FROM admins WHERE username = 'admin'")
    admin_row = cursor.fetchone()
    if admin_row and not admin_row["password"].startswith(("pbkdf2:", "scrypt:", "argon2:")):
        hashed_admin_pass = generate_password_hash(admin_row["password"])
        cursor.execute("UPDATE admins SET password = ? WHERE admin_id = ?", (hashed_admin_pass, admin_row["admin_id"]))
        print("[CampusCare DB] Upgraded default admin password to secure PBKDF2 hash.")

    # 7. Ensure admins table has role and department columns
    cursor.execute("PRAGMA table_info(admins)")
    admin_cols = {row["name"] for row in cursor.fetchall()}
    if "role" not in admin_cols:
        cursor.execute("ALTER TABLE admins ADD COLUMN role TEXT DEFAULT 'Super Admin'")
    if "department" not in admin_cols:
        cursor.execute("ALTER TABLE admins ADD COLUMN department TEXT DEFAULT ''")

    # 8. Backfill empty complaint departments based on category
    category_dept_map = {
        "Electrical": "Electrical",
        "Cleaning": "Cleaning",
        "Classroom": "Classroom",
        "Hostel": "Hostel",
        "Wi-Fi/Internet": "Wi-Fi/Internet",
        "Library": "Library",
        "Infrastructure": "Infrastructure",
        "Transport Complaint": "Transport",
        "Other": "Other"
    }
    for cat, dept in category_dept_map.items():
        cursor.execute(
            "UPDATE complaints SET department = ? WHERE category = ? AND (department = '' OR department IS NULL)",
            (dept, cat)
        )

    # 9. Seed/Update Department Admin Accounts
    department_accounts = [
        ("admin", "admin123", "Super Admin", ""),
        ("electrical_admin", "electrical123", "HOD", "Electrical"),
        ("electrical", "electrical123", "HOD", "Electrical"),
        ("cleaning_admin", "cleaning123", "HOD", "Cleaning"),
        ("cleaning", "cleaning123", "HOD", "Cleaning"),
        ("classroom_admin", "classroom123", "HOD", "Classroom"),
        ("classroom", "classroom123", "HOD", "Classroom"),
        ("hostel_admin", "hostel123", "HOD", "Hostel"),
        ("hostel", "hostel123", "HOD", "Hostel"),
        ("wifi_admin", "wifi123", "HOD", "Wi-Fi/Internet"),
        ("wifi", "wifi123", "HOD", "Wi-Fi/Internet"),
        ("library_admin", "library123", "HOD", "Library"),
        ("library", "library123", "HOD", "Library"),
        ("infra_admin", "infra123", "HOD", "Infrastructure"),
        ("infra", "infra123", "HOD", "Infrastructure"),
        ("transport_admin", "transport123", "HOD", "Transport"),
        ("transport", "transport123", "HOD", "Transport"),
        ("other_admin", "other123", "HOD", "Other"),
        ("other", "other123", "HOD", "Other"),
    ]
    for uname, pword, urole, udept in department_accounts:
        cursor.execute("SELECT admin_id, password, role, department FROM admins WHERE LOWER(username) = LOWER(?)", (uname,))
        existing_acc = cursor.fetchone()
        if not existing_acc:
            cursor.execute(
                "INSERT INTO admins (username, password, role, department) VALUES (?, ?, ?, ?)",
                (uname, generate_password_hash(pword), urole, udept)
            )
            print(f"[CampusCare DB] Created department admin account: {uname} ({udept})")
        else:
            # Keep role and department synced
            cursor.execute(
                "UPDATE admins SET role = ?, department = ? WHERE admin_id = ?",
                (urole, udept, existing_acc["admin_id"])
            )

    conn.commit()'''

if old_migration_end in content:
    content = content.replace(old_migration_end, new_migration_end, 1)
    print("2. Added department seed & backfill in migrate_database")
else:
    print("WARNING: Could not find old_migration_end")

# 3. Update create_complaint to automatically assign category -> department
old_create_comp = '''    department = ""
    if category == "Transport Complaint":
        department = "Transport"
        if not location:
            location = f"{bus_number} - {route}" if bus_number else "Transport"
    else:'''

new_create_comp = '''    category_dept_map = {
        "Electrical": "Electrical",
        "Cleaning": "Cleaning",
        "Classroom": "Classroom",
        "Hostel": "Hostel",
        "Wi-Fi/Internet": "Wi-Fi/Internet",
        "Library": "Library",
        "Infrastructure": "Infrastructure",
        "Transport Complaint": "Transport",
        "Other": "Other"
    }
    department = category_dept_map.get(category, category)
    if category == "Transport Complaint":
        if not location:
            location = f"{bus_number} - {route}" if bus_number else "Transport"
    else:'''

if old_create_comp in content:
    content = content.replace(old_create_comp, new_create_comp, 1)
    print("3. Updated create_complaint category-to-department auto-assignment")
else:
    print("WARNING: Could not find old_create_comp")

# 4. Update get_analytics_data to accept department=None
old_analytics = '''def get_analytics_data():
    """
    Aggregates statistical insights for the admin dashboard:
    Category breakdown, Priority breakdown, Status distribution, and 6-Month trends.
    """
    conn = get_db_connection()

    # 1. By Category
    cat_rows = conn.execute("SELECT category, COUNT(*) as count FROM complaints GROUP BY category ORDER BY count DESC").fetchall()
    by_category = {row["category"]: row["count"] for row in cat_rows}
    categories_list = [{"category": row["category"], "count": row["count"]} for row in cat_rows]

    # 2. By Priority
    prio_rows = conn.execute("SELECT priority, COUNT(*) as count FROM complaints GROUP BY priority").fetchall()
    by_priority = {"Low": 0, "Medium": 0, "High": 0}
    for row in prio_rows:
        by_priority[row["priority"]] = row["count"]
    priorities_list = [{"priority": p, "count": by_priority[p]} for p in ["High", "Medium", "Low"]]

    # 3. By Status
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
    statuses_list = [{"status": s, "count": by_status[s]} for s in ["Pending", "In Progress", "Resolved"]]

    # 4. Monthly Trend (Past 6 Months)
    monthly_trend = []
    now = datetime.now()
    for i in range(5, -1, -1):
        m_date = now - timedelta(days=i * 30)
        m_str = m_date.strftime("%Y-%m")
        m_label = m_date.strftime("%b %Y")
        m_count = conn.execute("SELECT COUNT(*) FROM complaints WHERE date LIKE ?", (f"{m_str}%",)).fetchone()[0]
        monthly_trend.append({"month": m_label, "count": m_count})'''

new_analytics = '''def get_analytics_data(department=None):
    """
    Aggregates statistical insights for the admin dashboard:
    Category breakdown, Priority breakdown, Status distribution, and 6-Month trends.
    Optionally scoped to a specific department.
    """
    conn = get_db_connection()
    where = "WHERE department = ?" if department else "WHERE 1=1"
    params = (department,) if department else ()

    # 1. By Category
    cat_rows = conn.execute(f"SELECT category, COUNT(*) as count FROM complaints {where} GROUP BY category ORDER BY count DESC", params).fetchall()
    by_category = {row["category"]: row["count"] for row in cat_rows}
    categories_list = [{"category": row["category"], "count": row["count"]} for row in cat_rows]

    # 2. By Priority
    prio_rows = conn.execute(f"SELECT priority, COUNT(*) as count FROM complaints {where} GROUP BY priority", params).fetchall()
    by_priority = {"Low": 0, "Medium": 0, "High": 0}
    for row in prio_rows:
        by_priority[row["priority"]] = row["count"]
    priorities_list = [{"priority": p, "count": by_priority[p]} for p in ["High", "Medium", "Low"]]

    # 3. By Status
    status_rows = conn.execute(f"SELECT status, COUNT(*) as count FROM complaints {where} GROUP BY status", params).fetchall()
    by_status = {"Pending": 0, "In Progress": 0, "Resolved": 0}
    for row in status_rows:
        s = row["status"]
        if s in ("NEW", "FORWARDED"):
            by_status["Pending"] += row["count"]
        elif s in ("IN_PROGRESS", "REOPENED"):
            by_status["In Progress"] += row["count"]
        elif s in ("FINAL_RESOLVED", "RESOLUTION_SUBMITTED", "AWAITING_STUDENT_CONFIRMATION"):
            by_status["Resolved"] += row["count"]
    statuses_list = [{"status": s, "count": by_status[s]} for s in ["Pending", "In Progress", "Resolved"]]

    # 4. Monthly Trend (Past 6 Months)
    monthly_trend = []
    now = datetime.now()
    for i in range(5, -1, -1):
        m_date = now - timedelta(days=i * 30)
        m_str = m_date.strftime("%Y-%m")
        m_label = m_date.strftime("%b %Y")
        m_count = conn.execute(f"SELECT COUNT(*) FROM complaints {where} AND date LIKE ?", params + (f"{m_str}%",)).fetchone()[0]
        monthly_trend.append({"month": m_label, "count": m_count})'''

if old_analytics in content:
    content = content.replace(old_analytics, new_analytics, 1)
    print("4. Updated get_analytics_data with department parameter")
else:
    print("WARNING: Could not find old_analytics")

# 5. Update get_all_complaints_for_report to accept department=None
old_report = '''def get_all_complaints_for_report(status_filter="All", priority_filter="All", search_text=""):
    """
    Fetches all matching complaint records with student details for PDF report generation without pagination limits.
    """
    conn = get_db_connection()
    base_where = "WHERE 1=1"
    params = []

    if status_filter and status_filter != "All":
        base_where += " AND complaints.status = ?"
        params.append(status_filter)

    if priority_filter and priority_filter != "All":
        base_where += " AND complaints.priority = ?"
        params.append(priority_filter)'''

new_report = '''def get_all_complaints_for_report(status_filter="All", priority_filter="All", search_text="", department=None):
    """
    Fetches all matching complaint records with student details for PDF report generation without pagination limits.
    """
    conn = get_db_connection()
    base_where = "WHERE 1=1"
    params = []

    if department:
        base_where += " AND complaints.department = ?"
        params.append(department)

    if status_filter and status_filter != "All":
        base_where += " AND complaints.status = ?"
        params.append(status_filter)

    if priority_filter and priority_filter != "All":
        base_where += " AND complaints.priority = ?"
        params.append(priority_filter)'''

if old_report in content:
    content = content.replace(old_report, new_report, 1)
    print("5. Updated get_all_complaints_for_report with department parameter")
else:
    print("WARNING: Could not find old_report")

# 6. Update get_campus_heatmap_data to accept department=None
old_heatmap = '''def get_campus_heatmap_data():
    """
    Aggregates real-time complaint data mapped to specific campus zones for the interactive problem heatmap.
    Computes intensity ratings (Low, Moderate, High, Critical) based on active volume and safety priority,
    and returns genuine database-driven complaint records for each zone.
    """
    conn = get_db_connection()
    
    # Pre-define canonical campus architectural zones with SVG bounds
    ZONES_CONFIG = {
        "Block A": {"id": "block-a", "name": "Block A", "label": "Academic Block A", "type": "Computer Science & IT Labs", "category_hint": "Computer Science & IT Labs", "x": 50, "y": 80, "w": 150, "h": 105},
        "Block B": {"id": "block-b", "name": "Block B", "label": "Academic Block B", "type": "Electronics & Tech Labs", "category_hint": "Electronics & Tech Labs", "x": 230, "y": 80, "w": 150, "h": 105},
        "Block C": {"id": "block-c", "name": "Block C", "label": "Academic Block C", "type": "Mechanical & Civil Wings", "category_hint": "Mechanical & Civil Wings", "x": 410, "y": 80, "w": 150, "h": 105},
        "Block D": {"id": "block-d", "name": "Block D", "label": "Management Block D", "type": "Business & Media Studios", "category_hint": "Business & Media Studios", "x": 590, "y": 80, "w": 150, "h": 105},
        "Block E": {"id": "block-e", "name": "Block E", "label": "Science Block E", "type": "Biotech & Chemistry", "category_hint": "Biotech & Chemistry", "x": 50, "y": 215, "w": 150, "h": 105},
        "Block F": {"id": "block-f", "name": "Block F", "label": "Innovation Block F", "type": "AI & Research Center", "category_hint": "AI & Research Center", "x": 230, "y": 215, "w": 150, "h": 105},
        "Academic Block": {"id": "academic-complex", "name": "Academic Complex", "label": "Central Academic Complex", "type": "Lecture Theatres & Offices", "category_hint": "Lecture Theatres & Offices", "x": 410, "y": 215, "w": 150, "h": 105},
        "Hostel": {"id": "hostels", "name": "Hostel Complex", "label": "Campus Hostels Complex", "type": "Resident Towers & Mess", "category_hint": "Resident Towers & Mess", "x": 590, "y": 215, "w": 150, "h": 105},
        "Library": {"id": "library", "name": "Central Library", "label": "Central Knowledge Library", "type": "Reading Halls & Archives", "category_hint": "Reading Halls & Archives", "x": 50, "y": 350, "w": 150, "h": 100},
        "Sports": {"id": "sports-arena", "name": "Sports Arena", "label": "Sports Arena & Complex", "type": "Gymnasium & Courts", "category_hint": "Gymnasium & Courts", "x": 230, "y": 350, "w": 150, "h": 100},
        "Campus": {"id": "cafeteria", "name": "Campus & Food Plaza", "label": "Central Campus & Cafeteria", "type": "Food Court & Student Plaza", "category_hint": "Food Court & Student Plaza", "x": 410, "y": 350, "w": 150, "h": 100},
        "Other": {"id": "utility-grounds", "name": "Utility Grounds", "label": "University Utility Grounds", "type": "Infrastructure & Parking", "category_hint": "Infrastructure & Parking", "x": 590, "y": 350, "w": 150, "h": 100}
    }
    
    query = """
        SELECT
            c.complaint_id,
            c.ticket_id,
            c.student_id,
            c.category,
            c.description,
            c.photo_path,
            c.block,
            c.location,
            c.floor_no,
            c.room_no,
            c.corridor_side,
            c.nearby_area,
            c.additional_location,
            c.priority,
            c.status,
            c.date,
            c.last_updated,
            s.name AS student_name,
            s.email AS student_email
        FROM complaints c
        LEFT JOIN students s ON c.student_id = s.student_id
        ORDER BY c.complaint_id DESC
    """
    rows = conn.execute(query).fetchall()'''

new_heatmap = '''def get_campus_heatmap_data(department=None):
    """
    Aggregates real-time complaint data mapped to specific campus zones for the interactive problem heatmap.
    Computes intensity ratings (Low, Moderate, High, Critical) based on active volume and safety priority,
    and returns genuine database-driven complaint records for each zone.
    Optionally scoped to a specific department.
    """
    conn = get_db_connection()
    
    # Pre-define canonical campus architectural zones with SVG bounds
    ZONES_CONFIG = {
        "Block A": {"id": "block-a", "name": "Block A", "label": "Academic Block A", "type": "Computer Science & IT Labs", "category_hint": "Computer Science & IT Labs", "x": 50, "y": 80, "w": 150, "h": 105},
        "Block B": {"id": "block-b", "name": "Block B", "label": "Academic Block B", "type": "Electronics & Tech Labs", "category_hint": "Electronics & Tech Labs", "x": 230, "y": 80, "w": 150, "h": 105},
        "Block C": {"id": "block-c", "name": "Block C", "label": "Academic Block C", "type": "Mechanical & Civil Wings", "category_hint": "Mechanical & Civil Wings", "x": 410, "y": 80, "w": 150, "h": 105},
        "Block D": {"id": "block-d", "name": "Block D", "label": "Management Block D", "type": "Business & Media Studios", "category_hint": "Business & Media Studios", "x": 590, "y": 80, "w": 150, "h": 105},
        "Block E": {"id": "block-e", "name": "Block E", "label": "Science Block E", "type": "Biotech & Chemistry", "category_hint": "Biotech & Chemistry", "x": 50, "y": 215, "w": 150, "h": 105},
        "Block F": {"id": "block-f", "name": "Block F", "label": "Innovation Block F", "type": "AI & Research Center", "category_hint": "AI & Research Center", "x": 230, "y": 215, "w": 150, "h": 105},
        "Academic Block": {"id": "academic-complex", "name": "Academic Complex", "label": "Central Academic Complex", "type": "Lecture Theatres & Offices", "category_hint": "Lecture Theatres & Offices", "x": 410, "y": 215, "w": 150, "h": 105},
        "Hostel": {"id": "hostels", "name": "Hostel Complex", "label": "Campus Hostels Complex", "type": "Resident Towers & Mess", "category_hint": "Resident Towers & Mess", "x": 590, "y": 215, "w": 150, "h": 105},
        "Library": {"id": "library", "name": "Central Library", "label": "Central Knowledge Library", "type": "Reading Halls & Archives", "category_hint": "Reading Halls & Archives", "x": 50, "y": 350, "w": 150, "h": 100},
        "Sports": {"id": "sports-arena", "name": "Sports Arena", "label": "Sports Arena & Complex", "type": "Gymnasium & Courts", "category_hint": "Gymnasium & Courts", "x": 230, "y": 350, "w": 150, "h": 100},
        "Campus": {"id": "cafeteria", "name": "Campus & Food Plaza", "label": "Central Campus & Cafeteria", "type": "Food Court & Student Plaza", "category_hint": "Food Court & Student Plaza", "x": 410, "y": 350, "w": 150, "h": 100},
        "Other": {"id": "utility-grounds", "name": "Utility Grounds", "label": "University Utility Grounds", "type": "Infrastructure & Parking", "category_hint": "Infrastructure & Parking", "x": 590, "y": 350, "w": 150, "h": 100}
    }
    
    where = "WHERE c.department = ?" if department else ""
    params = (department,) if department else ()
    query = f"""
        SELECT
            c.complaint_id,
            c.ticket_id,
            c.student_id,
            c.category,
            c.description,
            c.photo_path,
            c.block,
            c.location,
            c.floor_no,
            c.room_no,
            c.corridor_side,
            c.nearby_area,
            c.additional_location,
            c.priority,
            c.status,
            c.date,
            c.last_updated,
            s.name AS student_name,
            s.email AS student_email
        FROM complaints c
        LEFT JOIN students s ON c.student_id = s.student_id
        {where}
        ORDER BY c.complaint_id DESC
    """
    rows = conn.execute(query, params).fetchall()'''

if old_heatmap in content:
    content = content.replace(old_heatmap, new_heatmap, 1)
    print("6. Updated get_campus_heatmap_data with department parameter")
else:
    print("WARNING: Could not find old_heatmap")

# 7. Update get_campus_pulse_data to accept department=None
old_pulse = '''def get_campus_pulse_data():
    """
    Computes real-time Campus Pulse executive telemetry:
    - Critical unresolved issues
    - Top problem area / hotspot
    - Resolution rate percentage
    - Active complaints volume
    - 7-day complaint activity trend velocity
    """
    conn = get_db_connection()
    
    # 1. Total, Pending, Progress, Resolved
    stats = get_admin_statistics()
    total = stats["total"]
    pending = stats["pending"]
    in_progress = stats["in_progress"]
    resolved = stats["resolved"]
    active = pending + in_progress
    
    # 2. Critical Unresolved Issues (High Priority + Pending/In Progress)
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM complaints 
        WHERE priority = 'High' AND status IN ('NEW', 'FORWARDED', 'IN_PROGRESS', 'REOPENED')
    """)
    critical_issues = cur.fetchone()[0]

    # 3. Top Problem Area (Location/Block with highest active unresolved complaints)
    cur.execute("""
        SELECT 
            COALESCE(NULLIF(block, ''), NULLIF(location, ''), 'Campus') as loc_name,
            COUNT(*) as active_cnt,
            SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as high_cnt
        FROM complaints
        WHERE status IN ('Pending', 'In Progress')
        GROUP BY loc_name
        ORDER BY active_cnt DESC, high_cnt DESC
        LIMIT 1
    """)
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
        top_area_str = "All Zones Normal"

    # 4. Resolution Rate %
    resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0.0

    # 5. Overdue / Escalations (> 48h active)
    cur.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE priority = 'High' AND status != 'FINAL_RESOLVED'
    """)
    escalated_count = cur.fetchone()[0]

    # 6. Past 7-Day Velocity Trend
    now = datetime.now()
    daily_velocity = []
    velocity_7d = []
    for i in range(6, -1, -1):
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
    cur.execute("""
        SELECT AVG(julianday(last_updated) - julianday(date)) 
        FROM complaints 
        WHERE status = 'FINAL_RESOLVED' AND last_updated != '' AND date != ''
    """)'''

new_pulse = '''def get_campus_pulse_data(department=None):
    """
    Computes real-time Campus Pulse executive telemetry:
    - Critical unresolved issues
    - Top problem area / hotspot
    - Resolution rate percentage
    - Active complaints volume
    - 7-day complaint activity trend velocity
    Optionally scoped to a specific department.
    """
    conn = get_db_connection()
    where = "WHERE department = ?" if department else "WHERE 1=1"
    params = (department,) if department else ()
    
    # 1. Total, Pending, Progress, Resolved
    stats = get_admin_statistics(department)
    total = stats["total"]
    pending = stats["pending"]
    in_progress = stats["in_progress"]
    resolved = stats["resolved"]
    active = pending + in_progress
    
    # 2. Critical Unresolved Issues (High Priority + Pending/In Progress)
    cur = conn.cursor()
    cur.execute(f"""
        SELECT COUNT(*) FROM complaints 
        {where} AND priority = 'High' AND status IN ('NEW', 'FORWARDED', 'IN_PROGRESS', 'REOPENED')
    """, params)
    critical_issues = cur.fetchone()[0]

    # 3. Top Problem Area (Location/Block with highest active unresolved complaints)
    cur.execute(f"""
        SELECT 
            COALESCE(NULLIF(block, ''), NULLIF(location, ''), 'Campus') as loc_name,
            COUNT(*) as active_cnt,
            SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as high_cnt
        FROM complaints
        {where} AND status IN ('NEW', 'FORWARDED', 'IN_PROGRESS', 'REOPENED')
        GROUP BY loc_name
        ORDER BY active_cnt DESC, high_cnt DESC
        LIMIT 1
    """, params)
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
        top_area_str = "All Zones Normal"

    # 4. Resolution Rate %
    resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0.0

    # 5. Overdue / Escalations (> 48h active)
    cur.execute(f"""
        SELECT COUNT(*) FROM complaints
        {where} AND priority = 'High' AND status != 'FINAL_RESOLVED'
    """, params)
    escalated_count = cur.fetchone()[0]

    # 6. Past 7-Day Velocity Trend
    now = datetime.now()
    daily_velocity = []
    velocity_7d = []
    for i in range(6, -1, -1):
        day_dt = now - timedelta(days=i)
        day_str = day_dt.strftime("%Y-%m-%d")
        day_label = day_dt.strftime("%a (%d %b)") if i in [0, 6] else day_dt.strftime("%a")
        
        cur.execute(f"SELECT COUNT(*) FROM complaints {where} AND date = ?", params + (day_str,))
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
    cur.execute(f"""
        SELECT AVG(julianday(last_updated) - julianday(date)) 
        FROM complaints 
        {where} AND status = 'FINAL_RESOLVED' AND last_updated != '' AND date != ''
    """, params)'''

if old_pulse in content:
    content = content.replace(old_pulse, new_pulse, 1)
    print("7. Updated get_campus_pulse_data with department parameter")
else:
    print("WARNING: Could not find old_pulse")

with open(DB_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("database.py successfully patched!")
