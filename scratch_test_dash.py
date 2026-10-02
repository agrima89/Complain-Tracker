from app import app
import traceback
try:
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['student_id'] = 1
            sess['student_email'] = 'test@culkomail.in'
            sess['student_name'] = 'Test'
        res = client.get('/student/dashboard')
        print("Status:", res.status_code)
        if res.status_code == 500:
            print("Response:", res.text)
except Exception as e:
    traceback.print_exc()
