import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='active_complaint_slots'")
row = cursor.fetchone()
print(row[0] if row else "Table active_complaint_slots not found")
conn.close()
