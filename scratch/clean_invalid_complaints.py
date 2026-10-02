import os
import sys
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import database

def clean_database():
    conn = database.get_db_connection()
    cursor = conn.cursor()

    try:
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Identify all complaints where reporter email is NOT an official college email
        # Case-insensitive domain matching for college email
        cursor.execute("""
            SELECT c.complaint_id, c.ticket_id, s.email as student_email, s.name as student_name
            FROM complaints c
            LEFT JOIN students s ON c.student_id = s.student_id
            WHERE LOWER(COALESCE(s.email, '')) NOT LIKE '%@culmail.in'
              AND LOWER(COALESCE(s.email, '')) NOT LIKE '%@culkomail.in'
        """)
        invalid_rows = cursor.fetchall()

        if not invalid_rows:
            print("No invalid complaints found to delete.")
            conn.close()
            return

        invalid_ids = [row["complaint_id"] for row in invalid_rows]
        print(f"Found {len(invalid_ids)} complaint(s) with non-college email domains to delete:")
        for r in invalid_rows:
            print(f"  - Ticket: {r['ticket_id']} (ID: {r['complaint_id']}) | Reporter Email: {r['student_email']}")

        # Placeholders for SQL IN clause
        placeholders = ",".join("?" for _ in invalid_ids)

        # 1. Delete associated records in complaint_reporters
        cursor.execute(f"DELETE FROM complaint_reporters WHERE complaint_id IN ({placeholders})", invalid_ids)
        deleted_reporters = cursor.rowcount
        print(f"Deleted {deleted_reporters} row(s) from complaint_reporters.")

        # 2. Delete associated records in complaint_status_history
        cursor.execute(f"DELETE FROM complaint_status_history WHERE complaint_id IN ({placeholders})", invalid_ids)
        deleted_history = cursor.rowcount
        print(f"Deleted {deleted_history} row(s) from complaint_status_history.")

        # 3. Delete associated records in admin_notes
        cursor.execute(f"DELETE FROM admin_notes WHERE complaint_id IN ({placeholders})", invalid_ids)
        deleted_notes = cursor.rowcount
        print(f"Deleted {deleted_notes} row(s) from admin_notes.")

        # 4. Delete complaints from complaints table
        cursor.execute(f"DELETE FROM complaints WHERE complaint_id IN ({placeholders})", invalid_ids)
        deleted_complaints = cursor.rowcount
        print(f"Deleted {deleted_complaints} row(s) from complaints table.")

        # Commit the transaction
        conn.commit()
        print("\nCleanup successfully committed!")

        # Verification of remaining complaints
        cursor.execute("""
            SELECT c.complaint_id, c.ticket_id, c.category, c.status, c.priority, c.date, s.email, s.name
            FROM complaints c
            LEFT JOIN students s ON c.student_id = s.student_id
        """)
        remaining = cursor.fetchall()
        print(f"\nRemaining complaints in database: {len(remaining)}")
        for rem in remaining:
            print(f"  - Ticket: {rem['ticket_id']} | ID: {rem['complaint_id']} | Category: {rem['category']} | Status: {rem['status']} | Email: {rem['email']}")

    except Exception as e:
        conn.rollback()
        print(f"Error during cleanup, rolled back: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    clean_database()
