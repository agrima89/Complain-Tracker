import sys
sys.path.insert(0, r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker")
from app import app
import traceback

app.config['PROPAGATE_EXCEPTIONS'] = False
app.config['TESTING'] = False
app.config['DEBUG'] = False

client = app.test_client()

routes = [
    '/',
    '/login',
    '/register',
    '/admin/login',
    '/student/dashboard',
    '/student/submit',
    '/student/complaints',
    '/profile',
    '/admin/dashboard',
    '/admin/api/analytics'
]

for r in routes:
    try:
        res = client.get(r)
        print(f"[{res.status_code}] GET {r}")
        if res.status_code == 500:
            print(">>> 500 ERROR BODY:\n", res.get_data(as_text=True))
    except Exception:
        print(f">>> EXCEPTION ON GET {r}:")
        traceback.print_exc()
