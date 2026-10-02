import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

category_dept_map = {
    "Electrical": "Electrical",
    "Cleaning": "Cleaning",
    "Classroom": "Classroom",
    "Hostel": "Hostel",
    "Wi-Fi/Internet": "Wi-Fi/Internet",
    "Library": "Library",
    "Infrastructure": "Infrastructure",
    "Transport Complaint": "Transport",
    "Other": "Other"
}

total_updated = 0
for cat, dept in category_dept_map.items():
    cursor.execute("UPDATE complaints SET department = ? WHERE category = ?", (dept, cat))
    total_updated += cursor.rowcount

conn.commit()
print(f"Normalized department for {total_updated} rows in complaints table.")
conn.close()
