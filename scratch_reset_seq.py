import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

tables = [
    'complaint_status_history',
    'admin_notes',
    'complaint_reporters',
    'active_complaint_slots',
    'soc_audit_logs',
    'complaints'
]

placeholders = ', '.join(['?'] * len(tables))
cursor.execute(f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})", tables)

conn.commit()
conn.close()

print('Sequence reset successfully!')
