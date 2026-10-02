import requests
import re
import sqlite3

try:
    s = requests.Session()
    # Need to login first or we get 302
    r_login = s.get('http://127.0.0.1:5000/login')
    csrf_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', r_login.text)
    csrf = csrf_match.group(1) if csrf_match else ''
    
    # Let's get one from db
    conn = sqlite3.connect('database.db')
    student = conn.execute('SELECT email FROM students LIMIT 1').fetchone()
    conn.close()
    
    email = student[0] if student else 'test@culkomail.in'
    
    r_post = s.post('http://127.0.0.1:5000/login', data={'email': email, 'password': 'password123', 'csrf_token': csrf})
    
    # Now submit complaint
    r_sub_get = s.get('http://127.0.0.1:5000/submit_complaint')
    csrf_sub = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', r_sub_get.text)
    csrf2 = csrf_sub.group(1) if csrf_sub else ''
    
    with open('static/images/campus-bg.jpg', 'rb') as f:
        valid_img = f.read()
        
    data = {
        'category': 'Hostel',
        'description': 'This is a test description over 5 chars',
        'block': 'Block A',
        'floor_no': '1st Floor',
        'room_no': '101',
        'priority': 'Medium',
        'csrf_token': csrf2
    }
    files = {'photo': ('campus-bg.jpg', valid_img, 'image/jpeg')}
    
    resp = s.post('http://127.0.0.1:5000/submit_complaint', data=data, files=files)
    print('Status:', resp.status_code)
    if resp.status_code == 500:
        print('Got 500! Response text:')
        print(resp.text[:500])
except Exception as e:
    print('Error hitting server:', e)
