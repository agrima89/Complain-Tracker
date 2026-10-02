import sqlite3

db_path = 'c:/Users/LOQ/OneDrive/Desktop/College_Complaint_Tracker/database.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

emails_to_remove = ['25LBCS3099@culkomail.in', '25LBBC3049@culkomail.in']

for email in emails_to_remove:
    cursor.execute("DELETE FROM students WHERE email = ?", (email,))
    if cursor.rowcount > 0:
        print(f"Successfully deleted {email} from the database.")
    else:
        print(f"Email {email} not found in the database.")

conn.commit()
conn.close()
