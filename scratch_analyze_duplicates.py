import sqlite3

def analyze_and_migrate():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    groups = {
        'GROUP A (oidrggoewi)': ['CMP-2026-0103', 'CMP-2026-0104', 'CMP-2026-0133'],
        'GROUP B (wires)': ['CMP-2026-0134', 'CMP-2026-0143']
    }

    for group_name, tickets in groups.items():
        print(f"\n=== Analyzing {group_name} ===")
        # Get all complaints in the group
        placeholders = ','.join(['?'] * len(tickets))
        complaints = cursor.execute(f"SELECT * FROM complaints WHERE ticket_id IN ({placeholders}) ORDER BY complaint_id DESC", tickets).fetchall()
        
        if not complaints:
            print("No complaints found for this group.")
            continue
            
        master_complaint = complaints[0] # Newest is master (ORDER BY complaint_id DESC)
        master_id = master_complaint['complaint_id']
        print(f"Candidate Master: {master_complaint['ticket_id']} (ID: {master_id})")
        
        # Get all reporters for all complaints in this group
        complaint_ids = [c['complaint_id'] for c in complaints]
        placeholders_ids = ','.join(['?'] * len(complaint_ids))
        
        reporters = cursor.execute(f"SELECT * FROM complaint_reporters WHERE complaint_id IN ({placeholders_ids})", complaint_ids).fetchall()
        
        unique_reporters = {}
        for r in reporters:
            if r['student_id'] not in unique_reporters:
                unique_reporters[r['student_id']] = r
            else:
                # Keep the earliest report date
                if r['reported_at'] < unique_reporters[r['student_id']]['reported_at']:
                    unique_reporters[r['student_id']] = r
                    
        print(f"Total Unique Reporters found across the group: {len(unique_reporters)}")
        for s_id, r in unique_reporters.items():
            print(f" - Student ID: {s_id}, Email: {r['student_email']}")
            
        # Perform Migration
        print(f"Performing Migration for {group_name}...")
        
        # 1. Update the reporters to point to the master complaint ID
        # First, delete all existing reporters for these complaints to avoid unique constraint issues
        cursor.execute(f"DELETE FROM complaint_reporters WHERE complaint_id IN ({placeholders_ids})", complaint_ids)
        
        # Re-insert the unique reporters pointing to the master
        for s_id, r in unique_reporters.items():
            cursor.execute("""
                INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
                VALUES (?, ?, ?, ?)
            """, (master_id, s_id, r['student_email'], r['reported_at']))
            
        # 2. Update affected_student_count on master
        cursor.execute("UPDATE complaints SET affected_student_count = ? WHERE complaint_id = ?", (len(unique_reporters), master_id))
        
        # 3. Delete the redundant master complaints
        redundant_ids = [c['complaint_id'] for c in complaints if c['complaint_id'] != master_id]
        if redundant_ids:
            placeholders_red = ','.join(['?'] * len(redundant_ids))
            print(f"Deleting redundant master complaints: {redundant_ids}")
            cursor.execute(f"DELETE FROM complaints WHERE complaint_id IN ({placeholders_red})", redundant_ids)
            # Also clean up status history for redundant
            cursor.execute(f"DELETE FROM complaint_status_history WHERE complaint_id IN ({placeholders_red})", redundant_ids)
            cursor.execute(f"DELETE FROM active_complaint_slots WHERE complaint_id IN ({placeholders_red})", redundant_ids)
            
        print(f"Migration completed for {group_name}.")

    conn.commit()
    conn.close()
    
    print("\nDatabase Migration Finished.")

if __name__ == '__main__':
    analyze_and_migrate()
