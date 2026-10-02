import sqlite3
import json

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]

schema = {}
for t in tables:
    cursor.execute(f"PRAGMA table_info({t});")
    schema[t] = [row[1] for row in cursor.fetchall()]

print(json.dumps(schema, indent=2))
