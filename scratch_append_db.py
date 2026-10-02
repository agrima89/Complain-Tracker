import os
with open("database.py", "a", encoding="utf-8") as f:
    f.write("\n\n")
    f.write('''def delete_student_complaint(complaint_id, student_id):
    """
    Deletes or disassociates a student from a complaint.
    Returns: (success, message, http_status_code)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Fetch the complaint
    complaint = cursor.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
    
    if not complaint:
        conn.close()
        return False, "Complaint not found", 404
        
    # Check if student is associated
    is_reporter = cursor.execute("SELECT 1 FROM complaint_reporters WHERE complaint_id = ? AND student_id = ?", (complaint_id, student_id)).fetchone()
    is_main_submitter = complaint['student_id'] == student_id
    
    if not is_reporter and not is_main_submitter:
        conn.close()
        return False, "Unauthorized: You can only delete your own complaints.", 403
        
    if complaint['status'] != 'NEW':
        conn.close()
        return False, "This complaint can no longer be deleted because it is already being processed by the administration.", 403

    try:
        cursor.execute("BEGIN TRANSACTION")
        
        reporters_count = cursor.execute("SELECT COUNT(*) FROM complaint_reporters WHERE complaint_id = ?", (complaint_id,)).fetchone()[0]
        affected_count = complaint.get('affected_student_count', 1)
        
        if reporters_count <= 1 and affected_count <= 1:
            # Safe to delete completely
            cursor.execute("DELETE FROM complaint_reporters WHERE complaint_id = ?", (complaint_id,))
            cursor.execute("DELETE FROM complaint_status_history WHERE complaint_id = ?", (complaint_id,))
            cursor.execute("DELETE FROM active_complaint_slots WHERE ticket_id = ?", (complaint['ticket_id'],))
            
            photo_path = complaint.get('photo_path')
            if photo_path:
                usage = cursor.execute("SELECT COUNT(*) FROM complaints WHERE photo_path = ?", (photo_path,)).fetchone()[0]
                if usage <= 1:
                    full_path = os.path.join(BASE_DIR, photo_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        
            cursor.execute("DELETE FROM complaints WHERE complaint_id = ?", (complaint_id,))
            
        else:
            # Grouped complaint: disassociate this student
            cursor.execute("DELETE FROM complaint_reporters WHERE complaint_id = ? AND student_id = ?", (complaint_id, student_id))
            cursor.execute("UPDATE complaints SET affected_student_count = MAX(1, affected_student_count - 1) WHERE complaint_id = ?", (complaint_id,))
            
            if is_main_submitter:
                next_reporter = cursor.execute("SELECT student_id FROM complaint_reporters WHERE complaint_id = ? LIMIT 1", (complaint_id,)).fetchone()
                if next_reporter:
                    cursor.execute("UPDATE complaints SET student_id = ? WHERE complaint_id = ?", (next_reporter['student_id'], complaint_id))
        
        conn.commit()
        return True, "Complaint deleted successfully.", 200
        
    except Exception as e:
        conn.rollback()
        return False, f"Database error during deletion: {str(e)}", 500
    finally:
        conn.close()
''')
