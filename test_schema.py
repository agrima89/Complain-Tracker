import database
conn = database.get_db_connection()
schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='complaints'").fetchone()[0]
print(schema)
