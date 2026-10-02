import sqlite3
conn = sqlite3.connect('database.db')
c = conn.execute("SELECT complaint_id, ticket_id, status FROM complaints WHERE ticket_id = 'CMP-2026-0133'").fetchone()
print(c)
conn.close()
