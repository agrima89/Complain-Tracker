import sqlite3

db_path = r'c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\database.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("TABLES:")
for table in tables:
    t_name = table[0]
    print(f"\n--- {t_name} ---")
    cursor.execute(f"PRAGMA table_info({t_name})")
    cols = cursor.fetchall()
    for col in cols:
        print(col)

conn.close()
