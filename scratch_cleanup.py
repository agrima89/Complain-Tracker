import sqlite3
import os

db_path = 'c:/Users/LOQ/OneDrive/Desktop/College_Complaint_Tracker/database.db'
base_dir = 'c:/Users/LOQ/OneDrive/Desktop/College_Complaint_Tracker'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all photo paths before deleting records
cursor.execute("SELECT photo_path FROM complaints WHERE photo_path IS NOT NULL AND photo_path != '';")
photos = cursor.fetchall()
deleted_files = 0
for (photo,) in photos:
    # photo paths are like 'uploads/evidence/filename.jpg'
    full_path = os.path.join(base_dir, photo.replace('/', os.sep))
    if os.path.exists(full_path):
        os.remove(full_path)
        deleted_files += 1

tables_to_clear = [
    'complaint_status_history',
    'admin_notes',
    'complaint_reporters',
    'active_complaint_slots',
    'soc_audit_logs',  # assuming audit logs related to complaints should be cleared
    'complaints'
]

results = {}
for table in tables_to_clear:
    if table == 'soc_audit_logs':
        cursor.execute(f"DELETE FROM {table} WHERE complaint_id IS NOT NULL;")
    else:
        cursor.execute(f"DELETE FROM {table};")
    results[table] = cursor.rowcount

conn.commit()
conn.close()

print(f"Data cleanup successful.")
print(f"Deleted physical evidence files: {deleted_files}")
print("Rows deleted by table:")
for table, count in results.items():
    print(f" - {table}: {count}")
