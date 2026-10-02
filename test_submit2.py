import threading
import time
import requests
import traceback
from werkzeug.serving import make_server
from app import app
import database

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = make_server('127.0.0.1', 5013, app)
        self.ctx = app.app_context()
        self.ctx.push()
    def run(self):
        self.server.serve_forever()
    def shutdown(self):
        self.server.shutdown()

server = ServerThread(app)
server.start()
time.sleep(1)

try:
    conn = database.get_db_connection()
    student = conn.execute('SELECT email FROM students LIMIT 1').fetchone()
    conn.close()
    
    if student:
        session = requests.Session()
        session.post('http://127.0.0.1:5013/login', data={'email': student['email'], 'password':'password123'})
        
        r = session.get('http://127.0.0.1:5013/student/submit')
        import re
        m = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', r.text)
        csrf_token = m.group(1) if m else ''
        
        files = {'photo': ('test.jpg', b'dummy content', 'image/jpeg')}
        data = {
            'category': 'Hostel',
            'description': 'This is a test description over 5 chars',
            'block': 'Block A',
            'floor_no': '1st Floor',
            'room_no': '101',
            'priority': 'Medium',
            'csrf_token': csrf_token
        }
        resp = session.post('http://127.0.0.1:5013/submit-complaint', data=data, files=files, allow_redirects=False)
        print('Status Code:', resp.status_code)
        if resp.status_code >= 500:
            print(resp.text[:2000])
            
except Exception as e:
    traceback.print_exc()
finally:
    server.shutdown()
    server.join()
