from app import app
import traceback
try:
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['student_id'] = 1
            sess['student_email'] = 'test@culkomail.in'
            sess['student_name'] = 'Test'
        
        print("Testing POST /student/complaint/1/delete")
        # Ensure we have CSRF token bypassed or disabled for testing
        app.config['WTF_CSRF_ENABLED'] = False
        res = client.post('/student/complaint/1/delete')
        print("Status:", res.status_code)
        print("Response:", res.text)
except Exception as e:
    traceback.print_exc()
