import sqlite3
import os

db_path = 'database.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    if ('students',) in tables or ('users',) in tables:
        table = 'students' if ('students',) in tables else 'users'
        cursor.execute(f"PRAGMA table_info({table});")
        print(f"{table} schema:", cursor.fetchall())
        
        cursor.execute(f"SELECT * FROM {table} WHERE name LIKE '%agrima bajpai%';")
        print("Matches:", cursor.fetchall())
    conn.close()
else:
    print("No DB")
