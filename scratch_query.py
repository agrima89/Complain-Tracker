import sqlite3
import pprint

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn = sqlite3.connect('database.db')
conn.row_factory = dict_factory
cursor = conn.cursor()

cursor.execute("SELECT * FROM complaints WHERE description LIKE '%fan is not working%' AND room_no='323'")
rows = cursor.fetchall()

if not rows:
    print("No matching complaints found!")
else:
    for row in rows:
        print(f"--- Complaint ID {row['complaint_id']} ---")
        for k, v in row.items():
            if v:
                print(f"{k}: {v}")

conn.close()
