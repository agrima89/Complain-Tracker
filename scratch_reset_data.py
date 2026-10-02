import sqlite3
import shutil
import os

def reset_complaint_data():
    db_path = 'database.db'
    backup_path = 'database_backup.db'
    
    # 1. Create a backup
    print(f"Creating backup of {db_path} to {backup_path}")
    shutil.copy2(db_path, backup_path)
    print("Backup created successfully.\n")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 2. Inspect schema to find complaint-related tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r['name'] for r in cursor.fetchall()]
    print(f"All tables: {tables}")
    
    # Identify complaint tables
    complaint_tables = [
        'complaints',
        'complaint_reporters',
        'complaint_status_history',
        'active_complaint_slots',
        'grievance_system_logs' # based on earlier logs / system log events
    ]
    
    # Add any other complaint related tables
    for t in tables:
        if 'complaint' in t.lower() and t not in complaint_tables:
            complaint_tables.append(t)
            
    print(f"\nComplaint-related tables to clear: {complaint_tables}")

    # 3. Perform Deletion in a transaction
    try:
        cursor.execute("BEGIN TRANSACTION")
        
        counts_removed = {}
        # Clear tables
        for table in complaint_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                counts_removed[table] = count
                
                cursor.execute(f"DELETE FROM {table}")
                print(f"Cleared {count} records from {table}")

        # 4. Reset auto-increment / sequence
        print("\nResetting sqlite_sequence for cleared tables...")
        for table in complaint_tables:
            if table in tables:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name=?", (table,))
                
        cursor.execute("COMMIT")
        print("\nTransaction committed successfully.")
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"Error occurred: {e}. Transaction rolled back.")
        return

    # 5. Verify database counts
    print("\n--- POST-RESET VERIFICATION ---")
    for table in complaint_tables:
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"{table} count: {cursor.fetchone()[0]}")
            
    # Verify users exist
    cursor.execute("SELECT COUNT(*) FROM students")
    print(f"students count: {cursor.fetchone()[0]}")
    
    if 'admins' in tables:
        cursor.execute("SELECT COUNT(*) FROM admins")
        print(f"admins count: {cursor.fetchone()[0]}")
        
    conn.close()

    # 6. File Cleanup (Evidences / Attachments)
    print("\n--- FILE CLEANUP ---")
    uploads_dir = os.path.join('static', 'uploads')
    if os.path.exists(uploads_dir):
        files_removed = 0
        for filename in os.listdir(uploads_dir):
            file_path = os.path.join(uploads_dir, filename)
            if os.path.isfile(file_path):
                # Don't delete placeholder or non-complaint files if any. Typically uploads/ has only user uploads.
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
                    os.remove(file_path)
                    files_removed += 1
        print(f"Removed {files_removed} files from {uploads_dir}")
    else:
        print(f"Directory {uploads_dir} not found. Skipping file cleanup.")
        
    print("\nRESET COMPLETE.")

if __name__ == '__main__':
    reset_complaint_data()
