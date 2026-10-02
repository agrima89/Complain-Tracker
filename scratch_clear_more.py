import sqlite3

def clear_more():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('BEGIN TRANSACTION')
    cursor.execute('DELETE FROM admin_notes')
    cursor.execute('DELETE FROM soc_audit_logs')
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='admin_notes'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='soc_audit_logs'")
    cursor.execute('COMMIT')
    
    cursor.execute('SELECT COUNT(*) FROM admin_notes')
    print(f"admin_notes count: {cursor.fetchone()[0]}")
    
    cursor.execute('SELECT COUNT(*) FROM soc_audit_logs')
    print(f"soc_audit_logs count: {cursor.fetchone()[0]}")
    
    conn.close()

if __name__ == '__main__':
    clear_more()
