from app import app
import traceback
try:
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['student_id'] = 1
            sess['student_email'] = 'test@culkomail.in'
            sess['student_name'] = 'Test'
        
        print("Testing /student/dashboard")
        res = client.get('/student/dashboard')
        print("Status:", res.status_code)
        
        print("Testing /student/complaints")
        res2 = client.get('/student/complaints')
        print("Status:", res2.status_code)
        
        print("Testing /student/complaint/1")
        res3 = client.get('/student/complaint/1')
        print("Status:", res3.status_code)
        
except Exception as e:
    traceback.print_exc()
