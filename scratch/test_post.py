import traceback
from app import app
import database
import io

def test_post_routes():
    app.testing = True
    client = app.test_client()

    print("--- 1. Forward Complaint ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess['admin_id'] = 1
        sess['admin_username'] = 'admin'
        sess['admin_role'] = 'Super Admin'
        sess['admin_department'] = ''
    try:
        resp = client.post('/admin/api/forward-complaint', data={
            'complaint_id': '33',
            'department': 'Electrical',
            'reason': 'Test Reason'
        })
        print(f"Status: {resp.status_code}")
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        traceback.print_exc()

    print("\n--- 2. Mark Resolved ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess['admin_id'] = 1
        sess['admin_username'] = 'admin'
        sess['admin_role'] = 'Super Admin'
        sess['admin_department'] = ''
    try:
        resp = client.post('/admin/api/mark-resolved', data={
            'complaint_id': '33',
            'remarks': 'Fixed'
        })
        print(f"Status: {resp.status_code}")
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        traceback.print_exc()

    print("\n--- 3. Confirm Resolution ---")
    # Need to find the correct student_id for complaint 33
    conn = database.get_db_connection()
    student_id = conn.execute("SELECT student_id FROM complaints WHERE complaint_id = 33").fetchone()['student_id']
    conn.close()

    with client.session_transaction() as sess:
        sess.clear()
        sess['student_id'] = student_id
        sess['student_email'] = 'test@student.com'
        sess['student_name'] = 'Test Student'
    try:
        resp = client.post('/student/api/confirm-resolution', data={
            'complaint_id': '33'
        })
        print(f"Status: {resp.status_code}")
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        traceback.print_exc()

    print("\n--- 4. Regenerate Complaint ---")
    with client.session_transaction() as sess:
        sess.clear()
        sess['student_id'] = student_id
        sess['student_email'] = 'test@student.com'
        sess['student_name'] = 'Test Student'
    try:
        resp = client.post('/student/api/regenerate', data={
            'complaint_id': '33',
            'reason': 'Not actually fixed',
            'photo': (io.BytesIO(b"fake image data"), 'test.jpg')
        }, content_type='multipart/form-data')
        print(f"Status: {resp.status_code}")
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        traceback.print_exc()

test_post_routes()
