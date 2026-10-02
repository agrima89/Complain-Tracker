from app import app
import traceback
try:
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['student_id'] = 1
            sess['student_email'] = 'test@culkomail.in'
            sess['student_name'] = 'Test'
        
        print("Testing /student/complaint/1")
        res3 = client.get('/student/complaint/1')
        print("Status:", res3.status_code)
        if res3.status_code == 302:
            print("Redirect location:", res3.headers.get("Location"))
            # Follow redirect
            res4 = client.get(res3.headers.get("Location"))
            print("Status after redirect:", res4.status_code)
except Exception as e:
    traceback.print_exc()
