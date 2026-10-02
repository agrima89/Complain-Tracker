import sys
sys.path.insert(0, r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker")
from app import app
import traceback

app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['TESTING'] = False
app.config['DEBUG'] = True
client = app.test_client()

try:
    res = client.get('/')
    print("Status code:", res.status_code)
    print(res.get_data(as_text=True)[:500])
except Exception as e:
    print("EXACT EXCEPTION OCCURRED:")
    traceback.print_exc()
