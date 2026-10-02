import sys, traceback
from app import app

app.testing = True
# Disable error catching to get traceback
app.config['TRAP_HTTP_EXCEPTIONS'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

client = app.test_client()
routes = ['/', '/login', '/register', '/admin/login', '/student/dashboard', '/admin/dashboard']
for r in routes:
    print(f"Testing {r}...")
    try:
        resp = client.get(r, follow_redirects=True)
        if resp.status_code >= 500:
            print(f'ERROR on {r}: {resp.status_code}')
        else:
            print(f'OK on {r}: {resp.status_code}')
    except Exception as e:
        print(f'Exception on {r}')
        traceback.print_exc()
