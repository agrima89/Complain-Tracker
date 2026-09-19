import os
import sys
import webbrowser
import threading
import time

# Guarantee execution from the PROJECT ROOT
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app


def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    print("\n=======================================================")
    print("  STUDENT COMPLAINT & SOLUTION TRACKER (SCST) - WEB PORTAL")
    print("=======================================================")
    print("  Server is starting on: http://127.0.0.1:5000")
    print("  Default Admin Login: admin / admin123")
    print("=======================================================\n")
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
