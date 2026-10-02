import sys
import traceback
from app import app
import database

app.testing = True
app.config['TRAP_HTTP_EXCEPTIONS'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

# We need a student and an admin to test auth routes
with app.app_context():
    # create dummy student
    database.register_new_student("Test Student", "test.student@cuchd.in", "password123")
    s, _ = database.authenticate_student("test.student@cuchd.in", "password123")
    
    # get super admin
    a = database.authenticate_admin("admin", "admin123") # default admin

client = app.test_client()

student_routes = [
    '/student/dashboard',
    '/student/submit',
    '/my-complaints'
]

admin_routes = [
    '/admin/dashboard',
    '/admin/soc'
]

print("Testing student routes...")
with client.session_transaction() as sess:
    if s:
        sess['student_id'] = s['student_id']
        sess['student_email'] = s['email']
        sess['student_name'] = s['name']

for r in student_routes:
    try:
        resp = client.get(r, follow_redirects=True)
        print(f"Student GET {r} -> {resp.status_code}")
    except Exception as e:
        print(f"Student GET {r} FAILED with exception:")
        traceback.print_exc()

print("Testing admin routes...")
with client.session_transaction() as sess:
    sess.clear()
    if a:
        sess['admin_id'] = a['admin_id']
        sess['admin_username'] = a['username']
        sess['admin_role'] = a['role']
        sess['admin_department'] = a['department']

for r in admin_routes:
    try:
        resp = client.get(r, follow_redirects=True)
        print(f"Admin GET {r} -> {resp.status_code}")
    except Exception as e:
        print(f"Admin GET {r} FAILED with exception:")
        traceback.print_exc()
