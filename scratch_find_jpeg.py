import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
tables = ['students', 'complaints', 'admins', 'complaint_status_history', 'admin_notes', 'soc_audit_logs', 'complaint_reporters', 'active_complaint_slots']
for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cursor.fetchall() if r[2] in ('TEXT', 'VARCHAR')]
    for col in cols:
        try:
            cursor.execute(f"SELECT {col} FROM {table} WHERE {col} LIKE '%jpeg%'")
            res = cursor.fetchall()
            if res:
                print(f"Found in {table}.{col}: {res}")
        except Exception as e:
            pass
conn.close()
