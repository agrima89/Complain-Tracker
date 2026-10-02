import database
import time

def run_tests():
    print("Running 6 Business Logic Scenarios...")

    conn = database.get_db_connection()
    # Reset state for clean test (don't do this on prod but we will just use unique fake student IDs)
    student_a = "S_TEST_A"
    student_b = "S_TEST_B"
    student_c = "S_TEST_C"
    student_d = "S_TEST_D"
    
    # ensure students exist
    for s in [student_a, student_b, student_c, student_d]:
        try:
            conn.execute("INSERT INTO students (student_id, name, email, password, gender, hostel, room_no, course, admission_year, registered_at) VALUES (?, ?, ?, 'pass', 'M', 'H1', '101', 'BTech', '2023', '2023-01-01')", (s, f"Name {s}", f"{s}@test.com"))
        except:
            pass
    conn.commit()
    conn.close()

    print("\n--- TEST 1 ---")
    res1 = database.submit_or_attach_complaint(
        student_id=student_a, category="Electrical", description="Broken light",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Res1:", res1)
    
    print("\n--- TEST 2 ---")
    res2 = database.submit_or_attach_complaint(
        student_id=student_a, category="Electrical", description="Broken light",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Res2 (Same Student Duplicate):", res2)

    print("\n--- TEST 3 ---")
    res3 = database.submit_or_attach_complaint(
        student_id=student_b, category="Electrical", description="Broken light",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Res3 (Different Student):", res3)
    
    print("\n--- TEST 4 ---")
    res4 = database.submit_or_attach_complaint(
        student_id=student_c, category="Electrical", description="The light is broken",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Res4 (Different Student 2):", res4)

    print("\n--- TEST 5 ---")
    res5 = database.submit_or_attach_complaint(
        student_id=student_b, category="Electrical", description="Broken light",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Res5 (Student B again):", res5)
    
    print("\n--- TEST 6 ---")
    res6 = database.submit_or_attach_complaint(
        student_id=student_d, category="Electrical", description="Fan not working",
        block="Block E", floor_no="2nd Floor", room_no="E-329", corridor_side="RHS", date_str="2026-09-25"
    )
    print("Res6 (Different Issue):", res6)
    
    # DB Checks
    print("\n--- DB CHECKS ---")
    conn = database.get_db_connection()
    c_count = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ?", (student_a,)).fetchone()[0]
    print(f"Master complaints for {student_a}: {c_count}")
    
    reporters = conn.execute("SELECT * FROM complaint_reporters WHERE complaint_id = ?", (res1['complaint_id'],)).fetchall()
    print(f"Reporters for Master Ticket {res1['ticket_id']}: {len(reporters)}")
    for r in reporters:
        print(f"  - {dict(r)['student_id']}")

if __name__ == "__main__":
    run_tests()
