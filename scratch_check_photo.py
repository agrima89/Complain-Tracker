import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("SELECT complaint_id, ticket_id, photo_path FROM complaints WHERE photo_path != ''")
rows = cursor.fetchall()
print(f"Total: {len(rows)}")
for r in rows[:5]:
    print(r)
conn.close()
