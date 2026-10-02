import sys
import traceback
from app import app
import database
from io import BytesIO

app.testing = True
app.config['TRAP_HTTP_EXCEPTIONS'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

# Disable CSRF in tests
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    conn = database.get_db_connection()
    s = conn.execute("SELECT * FROM students LIMIT 1").fetchone()
    conn.close()
    
    if not s:
        print("No student found!")
        sys.exit(1)

client = app.test_client()

with client.session_transaction() as sess:
    sess['student_id'] = s['student_id']
    sess['student_email'] = s['email']
    sess['student_name'] = s['name']

print("Submitting complaint via POST...")

try:
    resp = client.post('/student/submit', data={
        'category': 'IT Support',
        'description': 'Internet is not working in the lab.',
        'block': 'A1 Block',
        'floor_no': '1st Floor',
        'room_no': '101',
        'priority': 'High',
        'photo': (BytesIO(b'dummy image content'), 'test.png')
    }, content_type='multipart/form-data', follow_redirects=True)
    
    print(f"POST /student/submit -> {resp.status_code}")
except Exception as e:
    print(f"POST /student/submit FAILED with exception:")
    traceback.print_exc()
