import database
import sqlite3

def run_tests():
    print("Running Mandatory Database Tests...")

    conn = database.get_db_connection()
    # Ensure students exist
    students = ['Student_A', 'Student_B', 'Student_C', 'Student_D']
    for s in students:
        try:
            conn.execute("INSERT INTO students (student_id, name, email, password, gender, hostel, room_no, course, admission_year, registered_at) VALUES (?, ?, ?, 'pass', 'M', 'H1', '101', 'BTech', '2023', '2023-01-01')", (s, f"{s} Name", f"{s}@test.com"))
        except:
            pass
    conn.commit()
    conn.close()

    print("\\n--- TEST 1: Student A submits new issue ---")
    res1 = database.submit_or_attach_complaint(
        student_id='Student_A', category="Electrical", description="Broken light",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Result:", res1['status'], "| Count:", res1['affected_student_count'])

    print("\\n--- TEST 2: Student A submits exact same issue ---")
    res2 = database.submit_or_attach_complaint(
        student_id='Student_A', category="Electrical", description="Broken light",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Result:", res2['status'], "| Count:", res2['affected_student_count'])

    print("\\n--- TEST 3: Student B submits exact same issue ---")
    res3 = database.submit_or_attach_complaint(
        student_id='Student_B', category="Electrical", description="Broken light",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Result:", res3['status'], "| Count:", res3['affected_student_count'])

    print("\\n--- TEST 4: Student C submits exact same issue ---")
    res4 = database.submit_or_attach_complaint(
        student_id='Student_C', category="Electrical", description="Broken light",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Result:", res4['status'], "| Count:", res4['affected_student_count'])

    print("\\n--- TEST 5: Student B submits exact same issue again ---")
    res5 = database.submit_or_attach_complaint(
        student_id='Student_B', category="Electrical", description="Broken light",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Result:", res5['status'], "| Count:", res5['affected_student_count'])

    print("\\n--- TEST 6: Student D submits different issue ---")
    res6 = database.submit_or_attach_complaint(
        student_id='Student_D', category="Electrical", description="Fan not working",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Result:", res6['status'], "| Count:", res6['affected_student_count'])

    print("\\n--- DIRECT DB CHECKS ---")
    conn = database.get_db_connection()
    c1 = res1['complaint_id']
    c6 = res6['complaint_id']

    print(f"\\nQuerying Complaints Table for Master Tickets:")
    for row in conn.execute("SELECT complaint_id, complaint_fingerprint, affected_student_count FROM complaints WHERE complaint_id IN (?, ?) ORDER BY complaint_id", (c1, c6)).fetchall():
        print(dict(row))
        
    print(f"\\nQuerying Complaint Reporters Table:")
    for row in conn.execute("SELECT complaint_id, student_id FROM complaint_reporters WHERE complaint_id IN (?, ?) ORDER BY complaint_id, student_id", (c1, c6)).fetchall():
        print(dict(row))
        
    conn.close()

if __name__ == '__main__':
    run_tests()
