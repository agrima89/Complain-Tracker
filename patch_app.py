with open('app.py', 'r') as f:
    c = f.read()

patch = '''
import traceback
import sys
import os

@app.errorhandler(Exception)
def handle_exception(e):
    with open("500_traceback.log", "w") as log_f:
        traceback.print_exc(file=log_f)
    return "Internal Server Error - Check 500_traceback.log in the project root!", 500
'''

if 'handle_exception' not in c:
    c = c.replace('static_folder="static"\n)', 'static_folder="static"\n)\n' + patch)
    with open('app.py', 'w') as f:
        f.write(c)
