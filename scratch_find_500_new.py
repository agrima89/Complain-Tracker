import traceback
from app import app
from flask import session

with app.test_client() as client:
    print("Testing Student Dashboard (no complaints)")
    with client.session_transaction() as sess:
        sess['student_id'] = 1
    
    response = client.get('/student/dashboard')
    if response.status_code == 500:
        print("Student dashboard 500 error:")
        # We can't see the full traceback this way easily unless we use app.config['TESTING'] = False or just look at logs
    print("Student dashboard status:", response.status_code)

    print("Testing Admin Dashboard (no complaints)")
    with client.session_transaction() as sess:
        sess['admin_id'] = 1
        sess['admin_username'] = 'admin'
        sess['department'] = 'Master'
    
    response = client.get('/admin/dashboard')
    print("Admin dashboard status:", response.status_code)

    # Let's run it with a context to catch the exact exception if possible
