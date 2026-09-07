import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")


def get_db_connection():
    """Returns a SQLite connection with Row factory enabled for dictionary-like column access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    """Initializes SQLite database tables and default admin account if not already present."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Complaints table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # Admins table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Create default admin account if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO admins (username, password)
        VALUES (?, ?)
    """, ("admin", "admin123"))

    conn.commit()
    conn.close()
    print("Database and tables initialized successfully!")


# ---------------- DATA ACCESS HELPERS ----------------

def authenticate_student(email, password):
    conn = get_db_connection()
    student = conn.execute(
        "SELECT * FROM students WHERE email = ? AND password = ?",
        (email, password)
    ).fetchone()
    conn.close()
    return student


def authenticate_admin(username, password):
    conn = get_db_connection()
    admin = conn.execute(
        "SELECT * FROM admins WHERE username = ? AND password = ?",
        (username, password)
    ).fetchone()
    conn.close()
    return admin


def register_new_student(name, email, password):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )
        conn.commit()
        student_id = cursor.lastrowid
        conn.close()
        return True, student_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "This email is already registered."


def get_student_statistics(student_id):
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ?", (student_id,)).fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'Pending'", (student_id,)).fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'In Progress'", (student_id,)).fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'Resolved'", (student_id,)).fetchone()[0]
    conn.close()
    return {"total": total, "pending": pending, "in_progress": in_progress, "resolved": resolved}


def get_admin_statistics():
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Pending'").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'").fetchone()[0]
    conn.close()
    return {"total": total, "pending": pending, "in_progress": in_progress, "resolved": resolved}


def create_complaint(student_id, category, description, location, priority, date_str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO complaints
        (student_id, category, description, location, priority, status, date)
        VALUES (?, ?, ?, ?, ?, 'Pending', ?)
    """, (student_id, category, description, location, priority, date_str))
    conn.commit()
    complaint_id = cursor.lastrowid
    conn.close()
    return complaint_id


def get_student_complaints(student_id, status_filter="All", search_query=None):
    conn = get_db_connection()
    query = """
        SELECT complaint_id, category, description, location, priority, status, date
        FROM complaints
        WHERE student_id = ?
    """
    params = [student_id]

    if status_filter and status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)

    if search_query:
        query += " AND (category LIKE ? OR description LIKE ? OR location LIKE ?)"
        s = f"%{search_query}%"
        params.extend([s, s, s])

    query += " ORDER BY complaint_id DESC"
    complaints = conn.execute(query, params).fetchall()
    conn.close()
    return complaints


def get_all_complaints_admin(status_filter="All", priority_filter="All", search_text=""):
    conn = get_db_connection()
    query = """
        SELECT
            complaints.complaint_id,
            students.name AS student_name,
            students.email AS student_email,
            complaints.student_id,
            complaints.category,
            complaints.description,
            complaints.location,
            complaints.priority,
            complaints.status,
            complaints.date
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        WHERE 1=1
    """
    params = []

    if status_filter and status_filter != "All":
        query += " AND complaints.status = ?"
        params.append(status_filter)

    if priority_filter and priority_filter != "All":
        query += " AND complaints.priority = ?"
        params.append(priority_filter)

    if search_text and search_text.strip():
        s = f"%{search_text.strip()}%"
        query += """
            AND (
                students.name LIKE ?
                OR students.email LIKE ?
                OR complaints.category LIKE ?
                OR complaints.description LIKE ?
                OR complaints.location LIKE ?
                OR complaints.complaint_id LIKE ?
            )
        """
        params.extend([s, s, s, s, s, s])

    query += " ORDER BY complaints.complaint_id DESC"
    complaints = conn.execute(query, params).fetchall()
    conn.close()
    return complaints


def get_complaint_by_id(complaint_id):
    conn = get_db_connection()
    query = """
        SELECT
            complaints.complaint_id,
            complaints.student_id,
            students.name AS student_name,
            students.email AS student_email,
            complaints.category,
            complaints.description,
            complaints.location,
            complaints.priority,
            complaints.status,
            complaints.date
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        WHERE complaints.complaint_id = ?
    """
    complaint = conn.execute(query, (complaint_id,)).fetchone()
    conn.close()
    return complaint


def update_complaint_status(complaint_id, new_status):
    valid_statuses = ["Pending", "In Progress", "Resolved"]
    if new_status not in valid_statuses:
        return False, "Invalid status value."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE complaints
        SET status = ?
        WHERE complaint_id = ?
    """, (new_status, complaint_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0, "Status updated successfully."


if __name__ == "__main__":
    create_database()