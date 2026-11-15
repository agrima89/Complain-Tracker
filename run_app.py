import os
import sys
import webbrowser
import threading
import time

sys.stderr = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_stderr.log"), "w", buffering=1)

# Guarantee execution from the PROJECT ROOT
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app



PORT = int(os.environ.get("PORT", 5001))


def open_browser():
    time.sleep(1.2)
    webbrowser.open(f"http://127.0.0.1:{PORT}")


if __name__ == "__main__":
    print("\n=======================================================")
    print("  STUDENT COMPLAINT & SOLUTION TRACKER (SCST) - WEB PORTAL")
    print("=======================================================")
    print(f"  Server is starting on: http://127.0.0.1:{PORT}")
    print("  Default Admin Login: admin / admin123")
    print("=======================================================\n")
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=PORT, debug=False)
