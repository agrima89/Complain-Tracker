import database
import traceback

try:
    print("Testing delete_student_complaint...")
    success, msg, status = database.delete_student_complaint(13, 2) # complaint 13 from my previous insert
    print("Success:", success)
    print("Message:", msg)
    print("Status:", status)
    
except Exception as e:
    traceback.print_exc()
