import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute("""
    CREATE TABLE test (
        id INTEGER PRIMARY KEY,
        active_key TEXT,
        status TEXT
    )
""")
conn.execute("""
    CREATE UNIQUE INDEX idx_test_active ON test(active_key)
    WHERE active_key != '' AND status IN ('NEW', 'PENDING', 'IN_PROGRESS', 'REOPENED', 'FORWARDED')
""")

# Insert first active
conn.execute("INSERT INTO test (active_key, status) VALUES ('1::electrical::block e|329', 'NEW')")
conn.commit()
print("1. First active complaint inserted.")

# Try inserting duplicate active for same student -> should fail at DB level
try:
    conn.execute("INSERT INTO test (active_key, status) VALUES ('1::electrical::block e|329', 'NEW')")
    conn.commit()
    print("ERROR: Duplicate allowed!")
except sqlite3.IntegrityError as e:
    print("2. SQLite IntegrityError successfully caught:", e)

# Different room for same student -> should succeed
conn.execute("INSERT INTO test (active_key, status) VALUES ('1::electrical::block e|330', 'NEW')")
conn.commit()
print("3. Different room allowed.")

# Different category for same student at same location -> should succeed
conn.execute("INSERT INTO test (active_key, status) VALUES ('1::cleaning::block e|329', 'NEW')")
conn.commit()
print("4. Different category allowed.")

# Mark first complaint as resolved
conn.execute("UPDATE test SET status = 'FINAL_RESOLVED' WHERE id = 1")
conn.commit()
print("5. First complaint marked FINAL_RESOLVED.")

# Now re-submitting for same student, category, room -> should succeed!
conn.execute("INSERT INTO test (active_key, status) VALUES ('1::electrical::block e|329', 'NEW')")
conn.commit()
print("6. New complaint allowed after prior resolution.")
