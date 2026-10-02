import traceback
from app import app
import database

def test_all():
    app.testing = True
    client = app.test_client()

    print("--- 1. Landing Page ---")
    try:
        resp = client.get('/')
        print(f"Status: {resp.status_code}")
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        traceback.print_exc()

    print("\n--- 2. Student Dashboard (Logged in) ---")
    with client.session_transaction() as sess:
        sess['student_id'] = 1
        sess['student_email'] = 'test@student.com'
        sess['student_name'] = 'Test Student'
    try:
        resp = client.get('/student/dashboard')
        print(f"Status: {resp.status_code}")
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        traceback.print_exc()

    print("\n--- 3. Admin Dashboard (Logged in as Super Admin) ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess['admin_id'] = 1
        sess['admin_username'] = 'admin'
        sess['admin_role'] = 'Super Admin'
        sess['admin_department'] = ''
    try:
        resp = client.get('/admin/dashboard')
        print(f"Status: {resp.status_code}")
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        traceback.print_exc()

    print("\n--- 4. HOD Dashboard (Logged in as HOD Transport) ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess['admin_id'] = 2
        sess['admin_username'] = 'hod_transport'
        sess['admin_role'] = 'HOD'
        sess['admin_department'] = 'Transport'
    try:
        resp = client.get('/admin/dashboard')
        print(f"Status: {resp.status_code}")
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        traceback.print_exc()

    print("\n--- 5. SOC Dashboard (Super Admin) ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess['admin_id'] = 1
        sess['admin_username'] = 'admin'
        sess['admin_role'] = 'Super Admin'
        sess['admin_department'] = ''
    try:
        resp = client.get('/admin/soc')
        print(f"Status: {resp.status_code}")
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        traceback.print_exc()
        
    print("\n--- 6. Profile (Student) ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess['student_id'] = 1
        sess['student_email'] = 'test@student.com'
        sess['student_name'] = 'Test Student'
    try:
        resp = client.get('/profile')
        print(f"Status: {resp.status_code}")
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        traceback.print_exc()

test_all()
