import sqlite3
conn = sqlite3.connect('database.db')
print(conn.execute('SELECT category, department FROM complaints WHERE department = "General"').fetchall())
conn.close()
