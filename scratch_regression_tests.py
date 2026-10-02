import database

def run_tests():
    conn = database.get_db_connection()
    students = ['Student_A', 'Student_B', 'Student_C', 'Student_D']
    for s in students:
        try:
            conn.execute("INSERT INTO students (student_id, name, email, password, gender, hostel, room_no, course, admission_year, registered_at) VALUES (?, ?, ?, 'pass', 'M', 'H1', '101', 'BTech', '2023', '2023-01-01')", (s, f"{s} Name", f"{s}@test.com"))
        except:
            pass
    conn.commit()
    conn.close()

    print("\nTEST 1: Student A submits a new issue (broken light)")
    r1 = database.submit_or_attach_complaint('Student_A', 'Electrical', 'broken light', block='Block E', floor_no='2nd Floor', room_no='E-329')
    print(r1['status'])
    
    print("\nTEST 2: Student A submits exactly the same issue again")
    r2 = database.submit_or_attach_complaint('Student_A', 'Electrical', 'broken light', block='Block E', floor_no='2nd Floor', room_no='E-329')
    print(r2['status'])
    
    print("\nTEST 3: Student B submits exactly the same issue")
    r3 = database.submit_or_attach_complaint('Student_B', 'Electrical', 'broken light', block='Block E', floor_no='2nd Floor', room_no='E-329')
    print(r3['status'])
    
    print("\nTEST 4: Student C submits a DIFFERENT issue in the same room (sparking switchboard)")
    r4 = database.submit_or_attach_complaint('Student_C', 'Electrical', 'sparking switchboard', block='Block E', floor_no='2nd Floor', room_no='E-329')
    print(r4['status'])
    
    print("\nTEST 5: Student D submits the same issue using minor wording variation (the light is broken)")
    r5 = database.submit_or_attach_complaint('Student_D', 'Electrical', 'the light is broken', block='Block E', floor_no='2nd Floor', room_no='E-329')
    print(r5['status'])
    
    print("\nTEST 6: Broken light vs broken fan in the same room")
    r6 = database.submit_or_attach_complaint('Student_D', 'Electrical', 'broken fan', block='Block E', floor_no='2nd Floor', room_no='E-329')
    print(r6['status'])
    
    conn = database.get_db_connection()
    c = conn.execute("SELECT complaint_id, complaint_fingerprint FROM complaints WHERE ticket_id IN (?, ?, ?, ?, ?, ?) ORDER BY complaint_id", (
        r1.get('ticket_id'), r2.get('ticket_id'), r3.get('ticket_id'), r4.get('ticket_id'), r5.get('ticket_id'), r6.get('ticket_id')
    )).fetchall()
    
    print("\nFinal Master Complaints created:")
    for row in c:
        print(dict(row))

if __name__ == '__main__':
    run_tests()
