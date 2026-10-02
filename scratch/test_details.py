import traceback
from app import app
import database

def test_details():
    app.testing = True
    client = app.test_client()

    conn = database.get_db_connection()
    complaint = conn.execute('SELECT complaint_id FROM complaints LIMIT 1').fetchone()
    conn.close()

    if not complaint:
        print('No complaints in DB to test details.')
        return

    cid = complaint['complaint_id']
    print(f'Testing complaint details for ID {cid}')
    
    with client.session_transaction() as sess:
        sess.clear()
        sess['student_id'] = 1
        sess['student_email'] = 'test@student.com'
        sess['student_name'] = 'Test Student'
    
    try:
        resp = client.get(f'/complaint/{cid}')
        print(f'Student view complaint status: {resp.status_code}')
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        print('Exception in Student view complaint:')
        traceback.print_exc()

    with client.session_transaction() as sess:
        sess.clear()
        sess['admin_id'] = 1
        sess['admin_username'] = 'admin'
        sess['admin_role'] = 'Super Admin'
        sess['admin_department'] = ''
        
    try:
        resp = client.get(f'/admin/complaint/{cid}')
        print(f'Admin view complaint status: {resp.status_code}')
        if resp.status_code == 500: print(resp.data.decode('utf-8'))
    except Exception as e:
        print('Exception in Admin view complaint:')
        traceback.print_exc()

test_details()
