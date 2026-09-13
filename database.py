import sqlite3
import os
import re
import uuid
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads", "complaints")

# Ensure upload directory exists
os.makedirs(UPLOADS_DIR, exist_ok=True)

def get_db_connection():
    """Returns a SQLite connection with Row factory enabled for dictionary-like column access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


CU_EMAIL_REGEX = r"^[A-Za-z0-9]+@culkomail\.in$"
CU_EMAIL_ERROR_MSG = "Please use your official Chandigarh University email (@culkomail.in)"


def is_valid_college_email(email):
    r"""
    Validates whether an email strictly belongs to Chandigarh University (@culkomail.in)
    with student ID containing only letters and numbers (case-insensitive) and no spaces.
    Pattern: ^[A-Za-z0-9]+@culkomail\.in$
    """
    if not email or not isinstance(email, str):
        return False, CU_EMAIL_ERROR_MSG

    email_clean = email.strip()
    if not re.match(r"^[A-Za-z0-9]+@culkomail\.in$", email_clean, re.IGNORECASE):
        return False, CU_EMAIL_ERROR_MSG

    return True, ""


def save_complaint_image(source_file_path_or_storage, custom_filename=None):
    """
    Safely saves an uploaded complaint image file to uploads/complaints/ with a unique collision-free filename.
    Returns the relative path with forward slashes (e.g., 'uploads/complaints/uuid_file.jpg').
    """
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    unique_prefix = f"{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"

    # If it's a Flask FileStorage object (has .save and .filename)
    if hasattr(source_file_path_or_storage, "filename") and hasattr(source_file_path_or_storage, "save"):
        original_name = source_file_path_or_storage.filename or "evidence.jpg"
        ext = os.path.splitext(original_name)[1].lower()
        if not ext or ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"
        safe_filename = f"evidence_{unique_prefix}{ext}"
        destination = os.path.join(UPLOADS_DIR, safe_filename)
        source_file_path_or_storage.save(destination)
        return f"uploads/complaints/{safe_filename}".replace("\\", "/")

    # If it's a file path string (from Tkinter file dialog)
    elif isinstance(source_file_path_or_storage, str) and os.path.isfile(source_file_path_or_storage):
        ext = os.path.splitext(source_file_path_or_storage)[1].lower()
        if not ext or ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"
        safe_filename = f"evidence_{unique_prefix}{ext}"
        destination = os.path.join(UPLOADS_DIR, safe_filename)
        shutil.copy2(source_file_path_or_storage, destination)
        return f"uploads/complaints/{safe_filename}".replace("\\", "/")

    return ""


def migrate_database(conn):
    """Safely adds new complaint columns without deleting any existing data."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(complaints)")
    existing_cols = {row["name"] for row in cursor.fetchall()}

    columns_to_add = [
        ("photo_path", "TEXT DEFAULT ''"),
        ("block", "TEXT DEFAULT ''"),
        ("floor_no", "TEXT DEFAULT ''"),
        ("room_no", "TEXT DEFAULT ''"),
        ("corridor_side", "TEXT DEFAULT ''"),
        ("nearby_area", "TEXT DEFAULT ''"),
        ("additional_location", "TEXT DEFAULT ''")
    ]

    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_def}")
            print(f"Migrated complaints table: Added column '{col_name}'")

    # Backfill legacy records if block is empty
    cursor.execute("SELECT complaint_id, location, block FROM complaints WHERE block IS NULL OR block = ''")
    legacy_rows = cursor.fetchall()
    for row in legacy_rows:
        cid = row["complaint_id"]
        loc = row["location"] or ""
        # Try to infer block if string contains "Block"
        inferred_block = "Other"
        for b in ["Block A", "Block B", "Block C", "Block D", "Block E", "Block F"]:
            if b.lower() in loc.lower():
                inferred_block = b
                break
        cursor.execute("UPDATE complaints SET block = ? WHERE complaint_id = ?", (inferred_block, cid))

    conn.commit()


def create_database():
    """Initializes SQLite database tables, runs safe migrations, and sets default admin account."""
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
            photo_path TEXT DEFAULT '',
            block TEXT DEFAULT '',
            floor_no TEXT DEFAULT '',
            room_no TEXT DEFAULT '',
            corridor_side TEXT DEFAULT '',
            nearby_area TEXT DEFAULT '',
            additional_location TEXT DEFAULT '',
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

    # Run safe column migration for existing tables
    migrate_database(conn)
    conn.close()
    print("Database schema verified and initialized successfully!")


# ---------------- DATA ACCESS HELPERS ----------------

def authenticate_student(email, password):
    """Authenticates a student by email and password, validating official Chandigarh University email (@culkomail.in)."""
    email_clean = email.strip()
    is_valid, err_msg = is_valid_college_email(email_clean)
    if not is_valid:
        return None, err_msg

    conn = get_db_connection()
    student = conn.execute(
        "SELECT * FROM students WHERE LOWER(email) = LOWER(?) AND password = ?",
        (email_clean, password)
    ).fetchone()
    conn.close()
    if not student:
        return None, "Invalid Chandigarh University email or password."
    return student, ""


def authenticate_admin(username, password):
    conn = get_db_connection()
    admin = conn.execute(
        "SELECT * FROM admins WHERE username = ? AND password = ?",
        (username.strip(), password)
    ).fetchone()
    conn.close()
    return admin


def register_new_student(name, email, password):
    """Registers a new student strictly with an official Chandigarh University email address (@culkomail.in)."""
    name_clean = name.strip()
    email_clean = email.strip()

    if not name_clean:
        return False, "Please enter your full name."

    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters long."

    is_valid, err_msg = is_valid_college_email(email_clean)
    if not is_valid:
        return False, err_msg

    conn = get_db_connection()
    # Check if already exists case-insensitively
    existing = conn.execute("SELECT * FROM students WHERE LOWER(email) = LOWER(?)", (email_clean,)).fetchone()
    if existing:
        conn.close()
        return False, "An account with this Chandigarh University email already exists. Please sign in."

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (name, email, password) VALUES (?, ?, ?)",
            (name_clean, email_clean, password)
        )
        conn.commit()
        student_id = cursor.lastrowid
        conn.close()
        return True, student_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "An account with this Chandigarh University email already exists. Please sign in."
    except Exception as e:
        conn.close()
        return False, f"Database error: {str(e)}"


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


def create_complaint(
    student_id,
    category,
    description,
    photo_path,
    block,
    floor_no,
    room_no,
    corridor_side,
    nearby_area,
    additional_location,
    priority,
    date_str,
    location=None
):
    """
    Inserts a new complaint record with all detailed location attributes and mandatory photo path.
    """
    # Build human-readable formatted location if not provided
    if not location:
        loc_parts = []
        if block:
            loc_parts.append(block)
        if floor_no:
            loc_parts.append(f"Floor {floor_no}")
        if room_no:
            loc_parts.append(f"Room {room_no}")
        if corridor_side:
            loc_parts.append(f"Side: {corridor_side}")
        if nearby_area:
            loc_parts.append(f"Near: {nearby_area}")
        location = ", ".join(loc_parts) if loc_parts else (block or "Campus")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO complaints
        (student_id, category, description, photo_path, block, floor_no, room_no,
         corridor_side, nearby_area, additional_location, location, priority, status, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
    """, (
        student_id,
        category,
        description,
        photo_path or "",
        block or "",
        floor_no or "",
        room_no or "",
        corridor_side or "",
        nearby_area or "",
        additional_location or "",
        location,
        priority,
        date_str
    ))
    conn.commit()
    complaint_id = cursor.lastrowid
    conn.close()
    return complaint_id


def get_student_complaints(student_id, status_filter="All", search_query=None):
    conn = get_db_connection()
    query = """
        SELECT
            complaint_id, student_id, category, description, photo_path,
            block, floor_no, room_no, corridor_side, nearby_area, additional_location,
            location, priority, status, date
        FROM complaints
        WHERE student_id = ?
    """
    params = [student_id]

    if status_filter and status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)

    if search_query:
        query += """ AND (
            category LIKE ? OR description LIKE ? OR location LIKE ?
            OR block LIKE ? OR room_no LIKE ? OR nearby_area LIKE ?
        )"""
        s = f"%{search_query}%"
        params.extend([s, s, s, s, s, s])

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
            complaints.photo_path,
            complaints.block,
            complaints.floor_no,
            complaints.room_no,
            complaints.corridor_side,
            complaints.nearby_area,
            complaints.additional_location,
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
                OR complaints.block LIKE ?
                OR complaints.room_no LIKE ?
                OR complaints.nearby_area LIKE ?
                OR complaints.complaint_id LIKE ?
            )
        """
        params.extend([s, s, s, s, s, s, s, s, s])

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
            complaints.photo_path,
            complaints.block,
            complaints.floor_no,
            complaints.room_no,
            complaints.corridor_side,
            complaints.nearby_area,
            complaints.additional_location,
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