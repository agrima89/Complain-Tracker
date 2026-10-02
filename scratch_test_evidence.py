import sys, traceback
from app import app
import database
from io import BytesIO

app.testing = True
app.config['TRAP_HTTP_EXCEPTIONS'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    conn = database.get_db_connection()
    s = conn.execute('SELECT * FROM students LIMIT 1').fetchone()
    a = conn.execute('SELECT * FROM admins LIMIT 1').fetchone()
    conn.close()

client = app.test_client()

data = {
    'category': 'IT Support',
    'description': 'Projector is broken in the lab.',
    'block': 'A1 Block',
    'floor_no': '2nd Floor',
    'room_no': '201',
    'priority': 'High',
    'photo': (BytesIO(b'dummy image content'), 'test_image.jpg')
}

print('Submitting as student...')
with client.session_transaction() as sess:
    sess['student_id'] = s['student_id']
    sess['student_email'] = s['email']
    sess['student_name'] = s['name']
    
resp1 = client.post('/student/submit', data=data, content_type='multipart/form-data', follow_redirects=True)
print('Submit Status:', resp1.status_code)

# Check DB for the new photo
with app.app_context():
    conn = database.get_db_connection()
    new_comp = conn.execute('SELECT * FROM complaints ORDER BY complaint_id DESC LIMIT 1').fetchone()
    conn.close()

print('New Complaint ID:', new_comp['complaint_id'])
print('Photo Path in DB:', new_comp['photo_path'])

ui_path = '/' + new_comp['photo_path']
print('UI URL:', ui_path)
resp2 = client.get(ui_path)
print('Download Status (as student):', resp2.status_code)

if resp2.status_code == 200:
    print('Content:', resp2.data)
else:
    print('Failed to download!')
