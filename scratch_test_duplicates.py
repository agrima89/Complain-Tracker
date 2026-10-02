import database
import sqlite3

def run_tests():
    conn = database.get_db_connection()
    students = ['Student_A', 'Student_B']
    for s in students:
        try:
            conn.execute("INSERT INTO students (student_id, name, email, password, gender, hostel, room_no, course, admission_year, registered_at) VALUES (?, ?, ?, 'pass', 'M', 'H1', '101', 'BTech', '2023', '2023-01-01')", (s, f"{s} Name", f"{s}@test.com"))
        except:
            pass
    conn.commit()
    conn.close()

    print("\n--- TEST 1: SAME STUDENT, SAME WORDING ---")
    r1 = database.submit_or_attach_complaint('Student_A', 'Cleaning', 'floor is not cleaned properly', block='Block E', floor_no='3rd Floor', room_no='323', corridor_side='RHS')
    print("Test 1 First Submission:", r1['status'])
    r2 = database.submit_or_attach_complaint('Student_A', 'Cleaning', 'floor is not cleaned properly', block='Block E', floor_no='3rd Floor', room_no='323', corridor_side='RHS')
    print("Test 1 Second Submission:", r2['status'])

    print("\n--- TEST 2: SAME STUDENT, DIFFERENT CAPITALIZATION ---")
    r3 = database.submit_or_attach_complaint('Student_A', 'Cleaning', 'FLOOR IS NOT CLEANED PROPERLY', block='Block E', floor_no='3rd Floor', room_no='323', corridor_side='RHS')
    print("Test 2 Submission:", r3['status'])

    print("\n--- TEST 3: SAME STUDENT, \"THE\" ADDED ---")
    r4 = database.submit_or_attach_complaint('Student_A', 'Cleaning', 'The floor is not cleaned properly', block='Block E', floor_no='3rd Floor', room_no='323', corridor_side='RHS')
    print("Test 3 Submission:", r4['status'])

    print("\n--- TEST 4: SAME STUDENT, PUNCTUATION DIFFERENCE ---")
    r5 = database.submit_or_attach_complaint('Student_A', 'Cleaning', 'Floor is not cleaned properly.', block='Block E', floor_no='3rd Floor', room_no='323', corridor_side='RHS')
    print("Test 4 Submission:", r5['status'])

    print("\n--- TEST 5: SAME STUDENT, SAME ISSUE, SAME LOCATION WITH FORMATTING DIFFERENCE ---")
    r6 = database.submit_or_attach_complaint('Student_A', 'Cleaning', 'floor is not cleaned properly', block='block e', floor_no='3rd floor', room_no='room 323', corridor_side='rhs')
    print("Test 5 Submission:", r6['status'])

    print("\n--- TEST 6: SAME STUDENT, SAME ISSUE, INCONSISTENT FLOOR ENTRY ---")
    r7 = database.submit_or_attach_complaint('Student_A', 'Cleaning', 'floor is not cleaned properly', block='Block E', floor_no='2nd Floor', room_no='323', corridor_side='RHS')
    print("Test 6 Submission:", r7['status'])
    if 'message' in r7: print("Test 6 Message:", r7['message'])

    print("\n--- TEST 7: DIFFERENT STUDENT, SAME ACTIVE ISSUE ---")
    r8 = database.submit_or_attach_complaint('Student_B', 'Cleaning', 'The floor is not cleaned properly', block='Block E', floor_no='3rd Floor', room_no='323', corridor_side='RHS')
    print("Test 7 Submission:", r8['status'], "| Affected count:", r8.get('affected_student_count'))

    print("\n--- TEST 8: SAME STUDENT, DIFFERENT ISSUE ---")
    r9 = database.submit_or_attach_complaint('Student_A', 'Cleaning', 'fan is not working', block='Block E', floor_no='3rd Floor', room_no='323', corridor_side='RHS')
    print("Test 8 Submission:", r9['status'])

    print("\n--- TEST 9: SAME STUDENT, DIFFERENT ROOM ---")
    r10 = database.submit_or_attach_complaint('Student_A', 'Cleaning', 'floor not cleaned', block='Block E', floor_no='3rd Floor', room_no='324', corridor_side='RHS')
    print("Test 9 Submission:", r10['status'])

if __name__ == '__main__':
    run_tests()
