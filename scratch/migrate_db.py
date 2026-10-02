import sqlite3
import os

db_path = r'c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\database.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. Remove specific student
email_to_remove = '25LBCS3099@culkomail.in'
c.execute("DELETE FROM students WHERE email = ?", (email_to_remove,))
print(f"Deleted student {email_to_remove}: {c.rowcount} rows affected")

# 2. Add SOC Audit Logs table
c.execute("""
CREATE TABLE IF NOT EXISTS soc_audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    user_email TEXT NOT NULL,
    complaint_id TEXT,
    department TEXT,
    severity TEXT DEFAULT 'LOW',
    timestamp TEXT NOT NULL,
    details TEXT
)
""")
print("Created soc_audit_logs table")

# 3. Alter admins table to add role and department
try:
    c.execute("ALTER TABLE admins ADD COLUMN role TEXT DEFAULT 'Super Admin'")
    print("Added role column to admins")
except sqlite3.OperationalError:
    pass

try:
    c.execute("ALTER TABLE admins ADD COLUMN department TEXT DEFAULT ''")
    print("Added department column to admins")
except sqlite3.OperationalError:
    pass

# 4. Alter complaints table
columns_to_add = [
    ("department", "TEXT DEFAULT ''"),
    ("forwarded_to", "TEXT DEFAULT ''"),
    ("forwarded_by", "TEXT DEFAULT ''"),
    ("forwarded_at", "TEXT DEFAULT ''"),
    ("resolved_by_department", "INTEGER DEFAULT 0"),
    ("department_resolution_time", "TEXT DEFAULT ''"),
    ("student_confirmation", "TEXT DEFAULT ''"),
    ("student_confirmation_time", "TEXT DEFAULT ''"),
    ("final_resolution_time", "TEXT DEFAULT ''"),
    ("original_complaint_id", "INTEGER DEFAULT NULL"),
    ("regeneration_count", "INTEGER DEFAULT 0"),
    ("regenerated_by_student", "INTEGER DEFAULT 0"),
    ("regeneration_reason", "TEXT DEFAULT ''"),
    ("previous_resolution_details", "TEXT DEFAULT ''")
]

for col_name, col_def in columns_to_add:
    try:
        c.execute(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_def}")
        print(f"Added {col_name} to complaints")
    except sqlite3.OperationalError:
        pass

conn.commit()
conn.close()
print("Database migration completed.")
