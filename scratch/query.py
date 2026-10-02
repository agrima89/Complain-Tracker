import sqlite3
import os

db_path = r'c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\database.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT email, password FROM students WHERE LOWER(email) LIKE '%25lbcs%'")
rows = cursor.fetchall()
for row in rows:
    print(row)
