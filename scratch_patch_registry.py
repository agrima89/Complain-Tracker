import sys
with open('database.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Remove filter from get_all_complaints_admin_paginated
target = 'base_where = "WHERE (complaints.is_primary = 1 OR complaints.group_id IS NULL)"'
c = c.replace(target, 'base_where = "WHERE 1=1"')

# 2. Modify submit_or_attach_complaint
# Replace the part that just inserts into complaint_reporters to also insert into complaints
start2 = c.find('print("ACTION = ADD_REPORTER")')
end2 = c.find('conn.commit()', start2)

new_logic = '''print("ACTION = ADD_REPORTER_AND_CREATE_TICKET")
            # Create the non-primary complaint record
            cursor.execute("""
                INSERT INTO complaints (
                    student_id, category, description, photo_path, block, floor_no, room_no,
                    corridor_side, nearby_area, additional_location, priority,
                    transport_type, bus_number, route, pickup_drop_point, transport_complaint_type,
                    department, status, date, location, complaint_fingerprint,
                    affected_student_count, is_primary, group_id, regeneration_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?, ?, ?, 0, ?, 0)
            """, (
                student_id, category, description, photo_path, block, floor_no, room_no,
                corridor_side, nearby_area, additional_location, priority,
                transport_type, bus_number, route, pickup_drop_point, transport_complaint_type,
                department, date_str, location, fingerprint,
                1, master_id
            ))
            
            new_complaint_id = cursor.lastrowid
            new_ticket_id = format_ticket_id(new_complaint_id, date_str)
            
            cursor.execute("UPDATE complaints SET ticket_id = ? WHERE complaint_id = ?", (new_ticket_id, new_complaint_id))
            
            # Insert into complaint_reporters for BOTH master and new complaint
            cursor.execute("""
                INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
                VALUES (?, ?, ?, ?)
            """, (master_id, student_id, student_email, now_timestamp))
            
            cursor.execute("""
                INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
                VALUES (?, ?, ?, ?)
            """, (new_complaint_id, student_id, student_email, now_timestamp))
            
            # Update affected_student_count on master
            cursor.execute("""
                UPDATE complaints 
                SET affected_student_count = affected_student_count + 1 
                WHERE complaint_id = ?
            """, (master_id,))
            
            conn.commit()
            return {
                "status": "ATTACHED_TO_MASTER",
                "complaint_id": new_complaint_id,
                "ticket_id": new_ticket_id,
                "affected_student_count": master["affected_student_count"] + 1,
                "current_status": master["status"],
                "category": category,
                "location": location,
                "message": f"Your complaint has been registered. You have been grouped with an existing active issue. Your Ticket ID is {new_ticket_id}."
            }'''

c = c[:start2] + new_logic + c[end2+13:]

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Patched successfully!')
