import sys
import re

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace everything from `group_id = None` down to `conn.commit()` in `submit_or_attach_complaint`
start_marker = '    group_id = None\n    is_primary = 1'
end_marker = '    conn.commit()\n    conn.close()'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print("Could not find markers in database.py")
    sys.exit(1)

new_logic = '''
    if master:
        # ATTACH TO EXISTING MASTER COMPLAINT
        complaint_id = master["complaint_id"]
        ticket_id = master["ticket_id"] or format_ticket_id(complaint_id, master["date"])
        
        # Check if student is already a reporter for this exact master complaint
        # (This acts as a failsafe if find_active_duplicate_complaint missed it)
        is_reporter = cursor.execute(
            "SELECT 1 FROM complaint_reporters WHERE complaint_id = ? AND student_id = ?",
            (complaint_id, student_id)
        ).fetchone()
        
        if is_reporter:
            conn.close()
            return {
                "status": "DUPLICATE_REJECTED",
                "complaint_id": complaint_id,
                "ticket_id": ticket_id,
                "affected_student_count": master.get("affected_student_count", 1),
                "current_status": master["status"],
                "category": master["category"],
                "location": (master["block"] or "") + (f", Room {master['room_no']}" if master["room_no"] else ""),
                "message": f"Duplicate Complaint Detected. You already have an active complaint ({ticket_id}) for this issue. No new complaint was created."
            }

        # Add current student as a reporter to existing master
        cursor.execute("""
            INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
            VALUES (?, ?, ?, ?)
        """, (complaint_id, student_id, student_email, now_timestamp))
        
        # Update the affected student count on the master complaint
        cursor.execute("""
            UPDATE complaints SET affected_student_count = affected_student_count + 1 WHERE complaint_id = ?
        """, (complaint_id,))
        
        # Register active slot
        active_slot_key = f"{student_id}::{fingerprint}"
        try:
            cursor.execute("""
                INSERT INTO active_complaint_slots (slot_key, complaint_id, student_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (active_slot_key, complaint_id, student_id, now_timestamp))
        except sqlite3.IntegrityError:
            pass # Ignore if duplicate slot, they are attached anyway
            
        conn.commit()
        new_count = (master.get("affected_student_count") or 1) + 1
        conn.close()
        
        return {
            "status": "ATTACHED_TO_MASTER",
            "complaint_id": complaint_id,
            "ticket_id": ticket_id,
            "affected_student_count": new_count,
            "message": f"Your complaint has been successfully attached to an existing issue report. Ticket ID: {ticket_id}"
        }

    # ==============================================================
    # IF NO MASTER COMPLAINT FOUND -> CREATE A NEW MASTER COMPLAINT
    # ==============================================================
    
    # Generate placeholders for group_id and is_primary
    group_id = None
    is_primary = 1
    
    cursor.execute("""
        INSERT INTO complaints
        (student_id, ticket_id, category, description, photo_path, block, floor_no, room_no,
         corridor_side, nearby_area, additional_location, location, priority, status, date, last_updated,
         transport_type, bus_number, route, pickup_drop_point, transport_complaint_type, department,
         complaint_fingerprint, affected_student_count, group_id, is_primary)
        VALUES (?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
    """, (
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
        department,
        fingerprint,
        group_id,
        is_primary
    ))
    complaint_id = cursor.lastrowid
    ticket_id = format_ticket_id(complaint_id, date_str)
    
    group_id = complaint_id

    # Save generated ticket_id and group_id
    cursor.execute("UPDATE complaints SET ticket_id = ?, group_id = ? WHERE complaint_id = ?", (ticket_id, group_id, complaint_id))

    # Link initial submitter in complaint_reporters
    cursor.execute("""
        INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
        VALUES (?, ?, ?, ?)
    """, (complaint_id, student_id, student_email, now_timestamp))

    # Initial audit history entry
    cursor.execute("""
        INSERT INTO complaint_status_history
        (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at)
        VALUES (?, NULL, 'Student (Submission)', NULL, 'NEW', 'Grievance ticket created and lodged for administration review.', ?)
    """, (complaint_id, now_timestamp))

    # Register active slot for database-level concurrency protection
    active_slot_key = f"{student_id}::{fingerprint}"
    try:
        cursor.execute("""
            INSERT INTO active_complaint_slots (slot_key, complaint_id, student_id, created_at)
            VALUES (?, ?, ?, ?)
        """, (active_slot_key, complaint_id, student_id, now_timestamp))
    except sqlite3.IntegrityError:
        conn.rollback()
        cursor.execute("SELECT complaint_id FROM active_complaint_slots WHERE slot_key = ?", (active_slot_key,))
        race_row = cursor.fetchone()
        race_id = race_row["complaint_id"] if race_row else complaint_id
        race_comp = get_complaint_by_id(race_id)
        race_ticket = race_comp["ticket_id"] if race_comp else format_ticket_id(race_id)
        conn.close()
        return {
            "status": "DUPLICATE_REJECTED",
            "complaint_id": race_id,
            "ticket_id": race_ticket,
            "affected_student_count": 1,
            "current_status": "NEW",
            "category": category,
            "location": block,
            "message": f"Duplicate Complaint Detected. You already have an active complaint ({race_ticket}) for this issue at this location. Please wait for your existing complaint to be resolved before submitting another complaint."
        }

'''

new_content = content[:start_idx] + new_logic.strip() + '\n\n' + content[end_idx:]

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
    
print("Successfully patched submit_or_attach_complaint in database.py")
