import database
import traceback

try:
    print("Inserting valid complaint for student 2...")
    conn = database.get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO complaints (student_id, ticket_id, category, description, location, priority, status, date) 
        VALUES (2, 'CC-999', 'Cleaning', 'Test', 'Hostel', 'Low', 'NEW', '2026-10-02')
    """)
    conn.commit()
    comp_id = cur.lastrowid
    print("Complaint ID:", comp_id)
    
    cur.execute("""
        INSERT INTO complaint_reporters (complaint_id, student_id, reported_at)
        VALUES (?, 2, '2026-10-02')
    """, (comp_id,))
    conn.commit()
    conn.close()
    
    print("Testing delete_student_complaint...")
    success, msg, status = database.delete_student_complaint(comp_id, 2)
    print("Success:", success)
    print("Message:", msg)
    print("Status:", status)
    
except Exception as e:
    traceback.print_exc()
