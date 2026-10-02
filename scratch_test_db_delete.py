from database import delete_student_complaint
import traceback

try:
    print("Testing delete_student_complaint(1, 1)")
    success, msg, status = delete_student_complaint(1, 1)
    print("Success:", success)
    print("Message:", msg)
    print("Status:", status)
except Exception as e:
    traceback.print_exc()
