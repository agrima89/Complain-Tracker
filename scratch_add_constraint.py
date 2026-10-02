import sqlite3

def add_constraint():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Check if we neepd to clean up any existing duplicate reporters before applying the UNIQUE constraint
    # We will keep the earliest reported_at for each (complaint_id, student_id)
    cursor.execute("""
        DELETE FROM complaint_reporters
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM complaint_reporters
            GROUP BY complaint_id, student_id
        )
    """)
    
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_reporter ON complaint_reporters (complaint_id, student_id)")
        print("Successfully added UNIQUE index to complaint_reporters.")
    except Exception as e:
        print(f"Error creating index: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_constraint()
