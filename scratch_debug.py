from app import app
import traceback

app.testing = True
client = app.test_client()

try:
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['admin_username'] = 'testadmin'
        sess['admin_role'] = 'Super Admin'
    
    response = client.get('/admin/dashboard')
    print("Status Code:", response.status_code)
    if response.status_code == 500:
        print("500 ERROR CAUGHT!")
        print(response.data.decode('utf-8'))
except Exception as e:
    print("EXCEPTION CAUGHT:")
    traceback.print_exc()
