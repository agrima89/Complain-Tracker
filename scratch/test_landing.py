import traceback
from app import app
import database

def test_routes():
    app.testing = True
    client = app.test_client()

    print("Testing Landing Page...")
    try:
        response = client.get('/')
        if response.status_code == 500:
            print("Landing Page Failed with 500!")
        else:
            print(f"Landing Page Success: {response.status_code}")
    except Exception as e:
        print("Exception in Landing Page:")
        traceback.print_exc()

test_routes()
