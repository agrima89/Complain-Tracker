from app import app
import database
import traceback

try:
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['student_id'] = 2
            sess['student_email'] = 'test2@culkomail.in'
            sess['student_name'] = 'Test2'
        
        comp_id = 14
        
        print("Testing POST /student/complaint/{}/delete".format(comp_id))
        app.config['WTF_CSRF_ENABLED'] = False
        res = client.post(f'/student/complaint/{comp_id}/delete')
        print("Status:", res.status_code)
        
        if res.status_code == 302:
            loc = res.headers.get('Location')
            print("Redirecting to:", loc)
            res2 = client.get(loc)
            print("Status after redirect:", res2.status_code)
            if res2.status_code == 500:
                print("500 Response Body:", res2.text)
        
except Exception as e:
    traceback.print_exc()
