from app import app
import database
import traceback

try:
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['student_id'] = 2
            sess['student_email'] = 'test2@culkomail.in'
            sess['student_name'] = 'Test2'
        
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
        
        print("Testing POST /student/complaint/{}/delete".format(comp_id))
        app.config['WTF_CSRF_ENABLED'] = False
        res = client.post(f'/student/complaint/{comp_id}/delete')
        print("Status:", res.status_code)
        print("Response:", res.text)
        
        print("Verify deletion in DB:")
        conn = database.get_db_connection()
        cur = conn.cursor()
        exists = cur.execute("SELECT 1 FROM complaints WHERE complaint_id = ?", (comp_id,)).fetchone()
        print("Complaint exists:", bool(exists))
        conn.close()
        
except Exception as e:
    traceback.print_exc()
