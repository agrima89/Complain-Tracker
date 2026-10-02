import json

with open('scratch/funcs.json', 'r', encoding='utf-8') as f:
    funcs = json.load(f)

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. authenticate_admin
new_auth_admin = """def authenticate_admin(username, password):
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
    conn.close()
    if admin and verify_and_migrate_password(admin["password"], password):
        return dict(admin)
    return None"""
content = content.replace(funcs['authenticate_admin'], new_auth_admin)

# 2. get_admin_statistics
new_get_admin_stats = """def get_admin_statistics(department=None):
    conn = get_db_connection()
    where = "WHERE department = ?" if department else "WHERE 1=1"
    params = (department,) if department else ()

    total = conn.execute(f"SELECT COUNT(*) FROM complaints {where}", params).fetchone()[0]
    
    where_pending = f"{where} AND status = 'NEW'"
    pending = conn.execute(f"SELECT COUNT(*) FROM complaints {where_pending}", params).fetchone()[0]
    
    where_forwarded = f"{where} AND status = 'FORWARDED'"
    forwarded = conn.execute(f"SELECT COUNT(*) FROM complaints {where_forwarded}", params).fetchone()[0]
    
    where_in_progress = f"{where} AND status = 'IN_PROGRESS'"
    in_progress = conn.execute(f"SELECT COUNT(*) FROM complaints {where_in_progress}", params).fetchone()[0]
    
    where_resolved = f"{where} AND status = 'RESOLVED_BY_DEPARTMENT'"
    resolved = conn.execute(f"SELECT COUNT(*) FROM complaints {where_resolved}", params).fetchone()[0]
    
    where_awaiting = f"{where} AND status = 'AWAITING_STUDENT_CONFIRMATION'"
    awaiting = conn.execute(f"SELECT COUNT(*) FROM complaints {where_awaiting}", params).fetchone()[0]
    
    where_regenerated = f"{where} AND status = 'REGENERATED'"
    regenerated = conn.execute(f"SELECT COUNT(*) FROM complaints {where_regenerated}", params).fetchone()[0]
    
    where_final = f"{where} AND status = 'FINAL_RESOLVED'"
    final_resolved = conn.execute(f"SELECT COUNT(*) FROM complaints {where_final}", params).fetchone()[0]

    # Count escalated items (High Priority + status != 'FINAL_RESOLVED' older than 48 hours)
    threshold_dt = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
    threshold_date = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d")

    where_escalated = f"{where} AND priority = 'High' AND status != 'FINAL_RESOLVED' AND (date < ? OR (last_updated != '' AND last_updated < ?))"
    params_escalated = params + (threshold_date, threshold_dt)
    escalated = conn.execute(f"SELECT COUNT(*) FROM complaints {where_escalated}", params_escalated).fetchone()[0]

    conn.close()
    return {
        "total": total,
        "pending": pending,
        "new": pending,
        "forwarded": forwarded,
        "in_progress": in_progress,
        "resolved_by_department": resolved,
        "awaiting_student_confirmation": awaiting,
        "regenerated": regenerated,
        "resolved": final_resolved,
        "final_resolved": final_resolved,
        "escalated": escalated
    }"""
content = content.replace(funcs['get_admin_statistics'], new_get_admin_stats)

# 3. get_student_statistics
new_get_student_stats = """def get_student_statistics(student_id):
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ?", (student_id,)).fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status IN ('NEW', 'FORWARDED')", (student_id,)).fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'IN_PROGRESS'", (student_id,)).fetchone()[0]
    awaiting = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'AWAITING_STUDENT_CONFIRMATION'", (student_id,)).fetchone()[0]
    regenerated = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'REGENERATED'", (student_id,)).fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'FINAL_RESOLVED'", (student_id,)).fetchone()[0]
    conn.close()
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "awaiting": awaiting,
        "regenerated": regenerated,
        "resolved": resolved
    }"""
content = content.replace(funcs['get_student_statistics'], new_get_student_stats)

# 4. get_public_statistics
new_get_public_stats = """def get_public_statistics():
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'FINAL_RESOLVED'").fetchone()[0]
    students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'IN_PROGRESS'").fetchone()[0]
    awaiting = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'AWAITING_STUDENT_CONFIRMATION'").fetchone()[0]
    conn.close()

    resolution_rate = int((resolved / total * 100)) if total > 0 else 0

    return {
        "total_complaints": total,
        "resolved_complaints": resolved,
        "active_students": students,
        "resolution_rate": resolution_rate,
        "in_progress": in_progress,
        "awaiting": awaiting
    }"""
content = content.replace(funcs['get_public_statistics'], new_get_public_stats)

# 5. create_complaint
new_create_complaint = """def create_complaint(
    student_id,
    category,
    description,
    photo_path="",
    block="",
    floor_no="",
    room_no="",
    corridor_side="",
    nearby_area="",
    additional_location="",
    priority="Low",
    date_str=None,
    location=None,
    transport_type="",
    bus_number="",
    route="",
    pickup_drop_point="",
    transport_complaint_type=""
):
    \"\"\"
    Inserts a new complaint record with ticket ID, formatted location, and records initial status history.
    \"\"\"
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    department = ""
    if category == "Transport Complaint":
        department = "Transport"
        if not location:
            location = f"{bus_number} - {route}" if bus_number else "Transport"
    else:
        if not location:
            loc_parts = []
            if block:
                loc_parts.append(block)
            if floor_no:
                loc_parts.append(f"Floor {floor_no}")
            if room_no:
                loc_parts.append(f"Room {room_no}")
            if corridor_side:
                loc_parts.append(f"Side: {corridor_side}")
            if nearby_area:
                loc_parts.append(f"Near: {nearby_area}")
            location = ", ".join(loc_parts) if loc_parts else (block or "Campus")

    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(\"\"\"
        INSERT INTO complaints
        (student_id, ticket_id, category, description, photo_path, block, floor_no, room_no,
         corridor_side, nearby_area, additional_location, location, priority, status, date, last_updated,
         transport_type, bus_number, route, pickup_drop_point, transport_complaint_type, department)
        VALUES (?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?, ?, ?, ?, ?, ?, ?)
    \"\"\", (
        student_id,
        category,
        description,
        photo_path or "",
        block or "",
        floor_no or "",
        room_no or "",
        corridor_side or "",
        nearby_area or "",
        additional_location or "",
        location,
        priority,
        date_str,
        now_timestamp,
        transport_type or "",
        bus_number or "",
        route or "",
        pickup_drop_point or "",
        transport_complaint_type or "",
        department
    ))
    complaint_id = cursor.lastrowid
    ticket_id = format_ticket_id(complaint_id, date_str)

    # Save generated ticket_id
    cursor.execute("UPDATE complaints SET ticket_id = ? WHERE complaint_id = ?", (ticket_id, complaint_id))

    # Record initial audit trail entry
    cursor.execute(\"\"\"
        INSERT INTO complaint_status_history
        (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at)
        VALUES (?, NULL, 'Student (Submission)', NULL, 'NEW', 'Grievance ticket created and lodged for administration review.', ?)
    \"\"\", (complaint_id, now_timestamp))

    conn.commit()
    conn.close()
    return complaint_id, ticket_id"""
content = content.replace(funcs['create_complaint'], new_create_complaint)

# 6. update_complaint_status
new_update_status = """def update_complaint_status(complaint_id, new_status, admin_id=None, admin_name="Administrator", remarks=""):
    \"\"\"
    Updates a complaint's status, updates last_updated, and creates a history audit trail entry.
    \"\"\"
    if new_status not in VALID_STATUSES:
        return False, "Invalid status value."

    conn = get_db_connection()
    existing = conn.execute("SELECT status, ticket_id FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
    if not existing:
        conn.close()
        return False, "Complaint record not found."

    old_status = existing["status"]
    if old_status == new_status:
        conn.close()
        return True, f"Status is already {new_status}."

    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute(\"\"\"
        UPDATE complaints
        SET status = ?,
            last_updated = ?,
            first_responded_at = CASE WHEN (first_responded_at = '' OR first_responded_at IS NULL) THEN ? ELSE first_responded_at END
        WHERE complaint_id = ?
    \"\"\", (new_status, now_timestamp, now_timestamp, complaint_id))

    # Record status change audit history
    cursor.execute(\"\"\"
        INSERT INTO complaint_status_history
        (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    \"\"\", (
        complaint_id,
        admin_id,
        admin_name or "Administrator",
        old_status,
        new_status,
        remarks or f"Status transitioned from '{old_status}' to '{new_status}'",
        now_timestamp
    ))

    conn.commit()
    conn.close()
    return True, f"Complaint status updated to {new_status}." """
content = content.replace(funcs['update_complaint_status'], new_update_status)

# 7. get_all_complaints_admin_paginated
new_get_admin_paginated = """def get_all_complaints_admin_paginated(
    status_filter="All",
    priority_filter="All",
    search_text="",
    escalated_only=False,
    page=1,
    per_page=10,
    department=None
):
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
        params.append(priority_filter)

    if search_text and search_text.strip():
        s = f"%{search_text.strip()}%"
        base_where += \"\"\"
            AND (
                complaints.ticket_id LIKE ?
                OR students.name LIKE ?
                OR students.email LIKE ?
                OR complaints.category LIKE ?
                OR complaints.description LIKE ?
                OR complaints.location LIKE ?
                OR complaints.block LIKE ?
                OR complaints.room_no LIKE ?
                OR complaints.nearby_area LIKE ?
                OR CAST(complaints.complaint_id AS TEXT) LIKE ?
            )
        \"\"\"
        params.extend([s, s, s, s, s, s, s, s, s, s])

    if escalated_only:
        threshold_date = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d")
        threshold_dt = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
        base_where += " AND complaints.priority = 'High' AND complaints.status != 'FINAL_RESOLVED'"
        base_where += " AND (complaints.date < ? OR (complaints.last_updated != '' AND complaints.last_updated < ?))"
        params.extend([threshold_date, threshold_dt])

    count_sql = f\"\"\"
        SELECT COUNT(*)
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        {base_where}
    \"\"\"
    total_count = conn.execute(count_sql, params).fetchone()[0]

    page = max(1, int(page))
    per_page = max(1, min(int(per_page), 50))
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    query_sql = f\"\"\"
        SELECT
            complaints.*,
            students.name AS student_name,
            students.email AS student_email
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        {base_where}
        ORDER BY complaints.complaint_id DESC
        LIMIT ? OFFSET ?
    \"\"\"
    query_params = list(params) + [per_page, offset]
    complaints = conn.execute(query_sql, query_params).fetchall()
    conn.close()

    return {
        "items": complaints,
        "total": total_count,
        "total_items": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    }"""
content = content.replace(funcs['get_all_complaints_admin_paginated'], new_get_admin_paginated)


with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated database functions.")
