import sys

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = 'def submit_or_attach_complaint('
end_marker = 'def create_complaint('
start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print('Failed to find markers')
    sys.exit(1)

new_func = '''def submit_or_attach_complaint(
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
    import time
    from datetime import datetime, date
    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not date_str:
        date_str = str(date.today())

    # STEP 1 & 2: Normalize and generate ONE deterministic fingerprint
    fingerprint = compute_complaint_fingerprint(
        category=category,
        description=description,
        block=block,
        floor_no=floor_no,
        room_no=room_no,
        corridor_side=corridor_side,
        nearby_area=nearby_area,
        additional_location=additional_location,
        location=location,
        transport_type=transport_type,
        bus_number=bus_number,
        route=route,
        pickup_drop_point=pickup_drop_point,
        transport_complaint_type=transport_complaint_type
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    # STEP 4: Server Console Logging
    student_row = cursor.execute("SELECT email, name FROM students WHERE student_id = ?", (student_id,)).fetchone()
    student_email = student_row["email"] if student_row else ""
    print(f"\\n--- SUBMISSION DEBUG ---")
    print(f"student_id = {student_id}")
    print(f"email = {student_email}")
    print(f"fingerprint = {fingerprint}")

    # STEP 3: Search for existing ACTIVE master complaint with that exact fingerprint
    master = cursor.execute("""
        SELECT * FROM complaints 
        WHERE complaint_fingerprint = ? 
          AND status != 'FINAL_RESOLVED' 
        ORDER BY complaint_id DESC LIMIT 1
    """, (fingerprint,)).fetchone()
    
    if master:
        master_id = master["complaint_id"]
        master_ticket = master["ticket_id"] or format_ticket_id(master_id, master["date"])
        print(f"existing_master_complaint_id = {master_id}")
        
        # Check complaint_reporters for current student
        is_reporter = cursor.execute(
            "SELECT 1 FROM complaint_reporters WHERE complaint_id = ? AND student_id = ?",
            (master_id, student_id)
        ).fetchone()
        
        if is_reporter:
            print("existing_reporter = True")
            print("ACTION = REJECT_DUPLICATE")
            conn.close()
            return {
                "status": "DUPLICATE_REJECTED",
                "complaint_id": master_id,
                "ticket_id": master_ticket,
                "affected_student_count": master["affected_student_count"],
                "current_status": master["status"],
                "category": master["category"],
                "location": (master["block"] or "") + (f", Room {master['room_no']}" if master["room_no"] else ""),
                "message": f"Duplicate Complaint Detected. You already have an active complaint ({master_ticket}) for this issue. No new complaint was created."
            }
        else:
            print("existing_reporter = False")
            print("ACTION = ADD_REPORTER")
            # Insert ONLY into complaint_reporters
            cursor.execute("""
                INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
                VALUES (?, ?, ?, ?)
            """, (master_id, student_id, student_email, now_timestamp))
            
            # Update affected_student_count
            cursor.execute("""
                UPDATE complaints 
                SET affected_student_count = affected_student_count + 1 
                WHERE complaint_id = ?
            """, (master_id,))
            
            conn.commit()
            
            # Fetch updated count
            new_count = cursor.execute("SELECT affected_student_count FROM complaints WHERE complaint_id = ?", (master_id,)).fetchone()[0]
            conn.close()
            
            return {
                "status": "ATTACHED_TO_MASTER",
                "complaint_id": master_id,
                "ticket_id": master_ticket,
                "affected_student_count": new_count,
                "message": f"Your complaint has been successfully attached to an existing issue report. Ticket ID: {master_ticket}"
            }

    # STEP 5: ONLY when no matching master complaint exists
    print("existing_master_complaint_id = None")
    print("existing_reporter = False")
    print("ACTION = CREATE_MASTER")
    
    # Assign department (basic assignment logic based on category)
    department = "General"
    if category == "Electrical":
        department = "Electrical"
    elif category == "Cleaning":
        department = "Cleaning"
    elif category == "Plumbing":
        department = "Plumbing"
    elif category == "IT / Network":
        department = "IT Support"
    elif category == "Transport Complaint":
        department = "Transport"

    cursor.execute("""
        INSERT INTO complaints
        (student_id, ticket_id, category, description, photo_path, block, floor_no, room_no,
         corridor_side, nearby_area, additional_location, location, priority, status, date, last_updated,
         transport_type, bus_number, route, pickup_drop_point, transport_complaint_type, department,
         complaint_fingerprint, affected_student_count, group_id, is_primary)
        VALUES (?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, NULL, 1)
    """, (
        student_id, category, description, photo_path or "", block or "", floor_no or "", room_no or "",
        corridor_side or "", nearby_area or "", additional_location or "", location or "", priority, date_str,
        now_timestamp, transport_type or "", bus_number or "", route or "", pickup_drop_point or "",
        transport_complaint_type or "", department, fingerprint
    ))
    
    complaint_id = cursor.lastrowid
    ticket_id = format_ticket_id(complaint_id, date_str)
    
    cursor.execute("UPDATE complaints SET ticket_id = ?, group_id = ? WHERE complaint_id = ?", (ticket_id, complaint_id, complaint_id))
    
    cursor.execute("""
        INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
        VALUES (?, ?, ?, ?)
    """, (complaint_id, student_id, student_email, now_timestamp))
    
    cursor.execute("""
        INSERT INTO complaint_status_history
        (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at)
        VALUES (?, NULL, 'Student (Submission)', NULL, 'NEW', 'Grievance ticket created and lodged for administration review.', ?)
    """, (complaint_id, now_timestamp))
    
    conn.commit()
    conn.close()
    
    return {
        "status": "CREATED_NEW",
        "complaint_id": complaint_id,
        "ticket_id": ticket_id,
        "affected_student_count": 1,
        "message": f"Grievance ticket {ticket_id} submitted successfully."
    }
'''

content = content[:start_idx] + new_func + '\n' + content[end_idx:]

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched submit_or_attach_complaint!')
