from app import app
import database
import io
import traceback
import re

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
app.config['TRAP_HTTP_EXCEPTIONS'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

try:
    with app.test_client() as client:
        conn = database.get_db_connection()
        student = conn.execute('SELECT student_id, name FROM students LIMIT 1').fetchone()
        conn.close()
        
        if student:
            with client.session_transaction() as sess:
                sess['student_id'] = student['student_id']
                sess['student_name'] = student['name']
                
            dummy_file = (io.BytesIO(b'dummy content'), 'test.jpg')
            data = {
                'category': 'Hostel',
                'description': 'This is a test description over 5 chars',
                'block': 'Block A',
                'floor_no': '1st Floor',
                'room_no': '101',
                'priority': 'Medium',
                'photo': dummy_file
            }
            
            resp = client.post('/submit-complaint', data=data, content_type='multipart/form-data', follow_redirects=False)
            print('Status Code:', resp.status_code)
            if resp.status_code == 302:
                print('Redirect to:', resp.headers['Location'])
            else:
                html = resp.get_data(as_text=True)
                # Print any flashed messages
                matches = re.findall(r'alert alert-[^\"]+\">(.*?)</div>', html, re.DOTALL)
                for m in matches:
                    print('FLASH:', m.strip())
except Exception as e:
    traceback.print_exc()
