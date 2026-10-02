import sqlite3
import datetime

DRY_RUN = False

def migrate_duplicates():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    master_ticket = 'CMP-2026-0133'
    duplicate_tickets = ['CMP-2026-0106', 'CMP-2026-0132']
    all_tickets = duplicate_tickets + [master_ticket]

    print(f"--- MIGRATION SCRIPT {'(DRY RUN)' if DRY_RUN else '(EXECUTE)'} ---")
    print(f"Master Candidate: {master_ticket}")
    print(f"Duplicate Tickets: {duplicate_tickets}")

    # 1. Get complaint IDs
    placeholders = ','.join(['?'] * len(all_tickets))
    complaints = cursor.execute(f"SELECT complaint_id, ticket_id, status FROM complaints WHERE ticket_id IN ({placeholders})", all_tickets).fetchall()
    
    complaint_map = {c['ticket_id']: c['complaint_id'] for c in complaints}
    if master_ticket not in complaint_map:
        print(f"Error: Master ticket {master_ticket} not found.")
        return

    master_id = complaint_map[master_ticket]
    dup_ids = [complaint_map[t] for t in duplicate_tickets if t in complaint_map]

    print(f"Master ID: {master_id}")
    print(f"Duplicate IDs: {dup_ids}")

    # 2. Collect all reporters
    c_ids = [master_id] + dup_ids
    ph_ids = ','.join(['?'] * len(c_ids))
    reporters = cursor.execute(f"SELECT * FROM complaint_reporters WHERE complaint_id IN ({ph_ids})", c_ids).fetchall()

    print(f"\nAll reporters found across these tickets: {len(reporters)}")
    unique_reporters = {}
    for r in reporters:
        sid = r['student_id']
        if sid not in unique_reporters:
            unique_reporters[sid] = dict(r)
        else:
            # Keep earliest reported_at
            if r['reported_at'] < unique_reporters[sid]['reported_at']:
                unique_reporters[sid] = dict(r)

    print(f"Unique reporters: {len(unique_reporters)}")
    for sid, r in unique_reporters.items():
        print(f" - Student: {sid} | Email: {r['student_email']} | Original Ticket: {r['complaint_id']}")

    final_count = len(unique_reporters)
    print(f"\nFinal affected_student_count for {master_ticket} will be: {final_count}")

    if not DRY_RUN:
        # A. Safely move all unique reporters to master ticket
        # First, delete reporters from all these tickets to avoid unique constraint issues
        cursor.execute(f"DELETE FROM complaint_reporters WHERE complaint_id IN ({ph_ids})", c_ids)
        
        # Insert back only the unique ones for the master ticket
        for sid, r in unique_reporters.items():
            cursor.execute("""
                INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
                VALUES (?, ?, ?, ?)
            """, (master_id, sid, r['student_email'], r['reported_at']))
            
        # B. Update affected_student_count on master
        cursor.execute("UPDATE complaints SET affected_student_count = ? WHERE complaint_id = ?", (final_count, master_id))
        
        # C. Handle duplicate master complaints (Mark as 'CLOSED' and 'merged' in remarks)
        # Assuming status 'CLOSED' or similar exists. Let's use 'FINAL_RESOLVED' or similar. 
        # The user requested marking them merged/closed/inactive.
        # "FINAL_RESOLVED" is used in the app to exclude them from active searches.
        for dup_id in dup_ids:
            cursor.execute("UPDATE complaints SET status = 'FINAL_RESOLVED', is_primary = 0, group_id = ? WHERE complaint_id = ?", (master_id, dup_id))
            # Insert status history for the merge
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO complaint_status_history (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at)
                VALUES (?, 0, 'System Migration', 'NEW', 'FINAL_RESOLVED', 'Complaint merged into master ticket CMP-2026-0133', ?)
            """, (dup_id, now))
            
            # Remove from active slots
            cursor.execute("DELETE FROM active_complaint_slots WHERE complaint_id = ?", (dup_id,))
            
        conn.commit()
        print("\nMigration executed successfully.")
        
    conn.close()

if __name__ == '__main__':
    migrate_duplicates()
