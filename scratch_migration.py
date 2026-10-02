import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("UPDATE complaints SET department = 'Wi-Fi/Internet' WHERE department = 'Wi-Fi / Internet'")
conn.commit()
print(f"Migrated {cursor.rowcount} rows in complaints table.")
conn.close()
