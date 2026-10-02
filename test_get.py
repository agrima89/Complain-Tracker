import requests
import re
import sqlite3

try:
    s = requests.Session()
    r_login = s.get('http://127.0.0.1:5000/login')
    csrf_match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', r_login.text)
    csrf = csrf_match.group(1) if csrf_match else ''
    
    conn = sqlite3.connect('database.db')
    student = conn.execute('SELECT email FROM students LIMIT 1').fetchone()
    conn.close()
    email = student[0] if student else 'test@culkomail.in'
    
    r_post = s.post('http://127.0.0.1:5000/login', data={'email': email, 'password': 'password123', 'csrf_token': csrf})
    
    resp = s.get('http://127.0.0.1:5000/submit_complaint')
    print('Status:', resp.status_code)
    if resp.status_code == 500:
        print('Got 500 on GET!')
        print(resp.text[:500])
except Exception as e:
    print('Error:', e)
