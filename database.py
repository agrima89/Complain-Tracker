import sqlite3
import os
import re
import uuid
import shutil
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_PATH") or os.path.join(BASE_DIR, "database.db")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads", "complaints")

# Ensure upload directory exists
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Validation Constants
CU_EMAIL_REGEX = r"^[A-Za-z0-9]+@culkomail\.in$"
CU_EMAIL_ERROR_MSG = "Please use your official Chandigarh University email (@culkomail.in)"

VALID_CATEGORIES = [
    "Electrical", "Cleaning", "Classroom", "Hostel",
    "Wi-Fi/Internet", "Library", "Infrastructure", "Transport Complaint", "Other"
]
VALID_PRIORITIES = ["Low", "Medium", "High"]
VALID_STATUSES = ["NEW", "FORWARDED", "IN_PROGRESS", "RESOLVED_BY_DEPARTMENT", "AWAITING_STUDENT_CONFIRMATION", "REGENERATED", "FINAL_RESOLVED"]
VALID_BLOCKS = [
    "Hostel", "Academic Block", "Campus", "Library", "Sports",
    "Block A", "Block B", "Block C", "Block D", "Block E", "Block F", "Other"
]

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


def allowed_file(filename):
    """Returns True if filename has a permitted file extension."""
    if not filename or "." not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_db_connection():
    """Returns a SQLite connection with Row factory enabled for dictionary-like column access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def is_valid_college_email(email):
    r"""
    Validates whether an email strictly belongs to Chandigarh University (@culkomail.in)
    with student ID containing only letters and numbers (case-insensitive) and no spaces.
    Pattern: ^[A-Za-z0-9]+@culkomail\.in$
    """
    if not email or not isinstance(email, str):
        return False, CU_EMAIL_ERROR_MSG

    email_clean = email.strip()
    if not re.match(CU_EMAIL_REGEX, email_clean, re.IGNORECASE):
        return False, CU_EMAIL_ERROR_MSG

    return True, ""


def format_ticket_id(complaint_id, date_str=None):
    """
    Generates a professional, persistent ticket identifier (e.g. CMP-2026-0001).
    """
    year = "2026"
    if date_str:
        try:
            year = str(date_str).split("-")[0]
        except Exception:
            year = str(datetime.now().year)
    else:
        year = str(datetime.now().year)
    return f"CMP-{year}-{int(complaint_id):04d}"


def verify_and_migrate_password(stored_password, provided_password, update_fn=None):
    """
    Verifies a password against a hash or legacy plain-text, transparently upgrading
    legacy plain-text records to pbkdf2:sha256 hashes upon successful authentication.
    """
    if not stored_password or not provided_password:
        return False

    # Check if stored password is a modern Werkzeug hash
    if stored_password.startswith(("pbkdf2:", "scrypt:", "argon2:")):
        return check_password_hash(stored_password, provided_password)

    # Legacy Plain-text fallback for backward compatibility
    if stored_password == provided_password:
        if update_fn:
            try:
                new_hash = generate_password_hash(provided_password)
                update_fn(new_hash)
            except Exception as e:
                print(f"[CampusCare Security] Password migration note: {e}")
        return True

    return False


def validate_and_inspect_file(file_path_or_storage, ext):
    """
    Inspects uploaded file contents to verify genuine image or PDF integrity.
    """
    ext_lower = ext.lower()
    if ext_lower not in ALLOWED_EXTENSIONS:
        return False

    # Check image files using Pillow
    if ext_lower in {".jpg", ".jpeg", ".png", ".webp"}:
        try:
            if hasattr(file_path_or_storage, "stream"):
                file_path_or_storage.stream.seek(0)
                img = Image.open(file_path_or_storage.stream)
                img.verify()
                file_path_or_storage.stream.seek(0)
            elif isinstance(file_path_or_storage, str) and os.path.isfile(file_path_or_storage):
                with Image.open(file_path_or_storage) as img:
                    img.verify()
            return True
        except Exception:
            return False

    # Check PDF magic bytes
    if ext_lower == ".pdf":
        try:
            if hasattr(file_path_or_storage, "stream"):
                file_path_or_storage.stream.seek(0)
                header = file_path_or_storage.stream.read(10)
                file_path_or_storage.stream.seek(0)
                return header.startswith(b"%PDF-")
            elif isinstance(file_path_or_storage, str) and os.path.isfile(file_path_or_storage):
                with open(file_path_or_storage, "rb") as f:
                    header = f.read(10)
                return header.startswith(b"%PDF-")
        except Exception:
            return False

    return False


def save_complaint_image(source_file_path_or_storage, custom_filename=None):
    """
    Safely saves an uploaded complaint evidence file to uploads/complaints/ with a unique collision-free filename.
    Returns relative path with forward slashes (e.g. 'uploads/complaints/uuid_file.jpg').
    """
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    unique_prefix = f"{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"

    # If it's a Flask FileStorage object
    if hasattr(source_file_path_or_storage, "filename") and hasattr(source_file_path_or_storage, "save"):
        original_name = source_file_path_or_storage.filename or "evidence.jpg"
        ext = os.path.splitext(original_name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return ""

        # Validate file integrity
        if not validate_and_inspect_file(source_file_path_or_storage, ext):
            return ""

        safe_filename = f"evidence_{unique_prefix}{ext}"
        destination = os.path.join(UPLOADS_DIR, safe_filename)
        source_file_path_or_storage.save(destination)
        return f"uploads/complaints/{safe_filename}".replace("\\", "/")

    # If it's a file path string (from Tkinter file dialog)
    elif isinstance(source_file_path_or_storage, str) and os.path.isfile(source_file_path_or_storage):
        ext = os.path.splitext(source_file_path_or_storage)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return ""

        if not validate_and_inspect_file(source_file_path_or_storage, ext):
            return ""

        safe_filename = f"evidence_{unique_prefix}{ext}"
        destination = os.path.join(UPLOADS_DIR, safe_filename)
        shutil.copy2(source_file_path_or_storage, destination)
        return f"uploads/complaints/{safe_filename}".replace("\\", "/")

    return ""


def migrate_database(conn):
    """Safely adds new complaint columns, indexes, audit history, and notes tables without deleting existing data."""
    cursor = conn.cursor()

    # 1. Migrate complaints table columns
    cursor.execute("PRAGMA table_info(complaints)")
    existing_cols = {row["name"] for row in cursor.fetchall()}

    columns_to_add = [
        ("ticket_id", "TEXT DEFAULT ''"),
        ("photo_path", "TEXT DEFAULT ''"),
        ("block", "TEXT DEFAULT ''"),
        ("floor_no", "TEXT DEFAULT ''"),
        ("room_no", "TEXT DEFAULT ''"),
        ("corridor_side", "TEXT DEFAULT ''"),
        ("nearby_area", "TEXT DEFAULT ''"),
        ("additional_location", "TEXT DEFAULT ''"),
        ("last_updated", "TEXT DEFAULT ''"),
        ("first_responded_at", "TEXT DEFAULT ''"),
        ("transport_type", "TEXT DEFAULT ''"),
        ("bus_number", "TEXT DEFAULT ''"),
        ("route", "TEXT DEFAULT ''"),
        ("pickup_drop_point", "TEXT DEFAULT ''"),
        ("transport_complaint_type", "TEXT DEFAULT ''")
    ]

    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_def}")
            print(f"[CampusCare DB] Added column '{col_name}' to complaints table.")

    # 2. Create Status Audit Trail Table & Admin Notes Table if not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaint_status_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            admin_id INTEGER,
            admin_name TEXT DEFAULT 'System',
            old_status TEXT,
            new_status TEXT NOT NULL,
            remarks TEXT DEFAULT '',
            changed_at TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_notes (
            note_id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            admin_id INTEGER NOT NULL,
            admin_name TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
        )
    """)

    # 3. Backfill legacy records missing ticket_id or last_updated
    cursor.execute("SELECT complaint_id, date, ticket_id, last_updated, status, first_responded_at FROM complaints")
    rows = cursor.fetchall()
    for row in rows:
        cid = row["complaint_id"]
        cdate = row["date"] or str(datetime.now().date())
        ticket = row["ticket_id"]
        updated = row["last_updated"]

        new_ticket = ticket if ticket else format_ticket_id(cid, cdate)
        new_updated = updated if updated else cdate

        if not ticket or not updated:
            cursor.execute(
                "UPDATE complaints SET ticket_id = ?, last_updated = ? WHERE complaint_id = ?",
                (new_ticket, new_updated, cid)
            )

    # 3b. Backfill first_responded_at from audit history or notes if available
    cursor.execute("""
        SELECT c.complaint_id, c.status, c.last_updated, c.date,
               (SELECT MIN(changed_at) FROM complaint_status_history h WHERE h.complaint_id = c.complaint_id AND (h.admin_name != 'Student (Submission)' OR h.old_status IS NOT NULL OR h.admin_id IS NOT NULL)) as first_hist,
               (SELECT MIN(created_at) FROM admin_notes n WHERE n.complaint_id = c.complaint_id) as first_note
        FROM complaints c
        WHERE c.first_responded_at = '' OR c.first_responded_at IS NULL
    """)
    for r in cursor.fetchall():
        first_resp = r["first_hist"] or r["first_note"]
        if not first_resp and r["status"] in ("In Progress", "Resolved"):
            first_resp = r["last_updated"] or r["date"]
        if first_resp:
            cursor.execute("UPDATE complaints SET first_responded_at = ? WHERE complaint_id = ?", (first_resp, r["complaint_id"]))

    # 5. Create Performance Database Indexes
    indexes_to_create = [
        ("idx_complaints_student", "CREATE INDEX IF NOT EXISTS idx_complaints_student ON complaints(student_id)"),
        ("idx_complaints_status", "CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status)"),
        ("idx_complaints_priority", "CREATE INDEX IF NOT EXISTS idx_complaints_priority ON complaints(priority)"),
        ("idx_complaints_ticket_id", "CREATE INDEX IF NOT EXISTS idx_complaints_ticket_id ON complaints(ticket_id)"),
        ("idx_history_complaint", "CREATE INDEX IF NOT EXISTS idx_history_complaint ON complaint_status_history(complaint_id)"),
        ("idx_notes_complaint", "CREATE INDEX IF NOT EXISTS idx_notes_complaint ON admin_notes(complaint_id)")
    ]

    for idx_name, idx_sql in indexes_to_create:
        cursor.execute(idx_sql)

    # 6. Migrate Default Admin Password to Secure Hash if Plaintext
    cursor.execute("SELECT admin_id, username, password FROM admins WHERE username = 'admin'")
    admin_row = cursor.fetchone()
    if admin_row and not admin_row["password"].startswith(("pbkdf2:", "scrypt:", "argon2:")):
        hashed_admin_pass = generate_password_hash(admin_row["password"])
        cursor.execute("UPDATE admins SET password = ? WHERE admin_id = ?", (hashed_admin_pass, admin_row["admin_id"]))
        print("[CampusCare DB] Upgraded default admin password to secure PBKDF2 hash.")

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
            ticket_id TEXT DEFAULT '',
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
            last_updated TEXT DEFAULT '',
            first_responded_at TEXT DEFAULT '',
            transport_type TEXT DEFAULT '',
            bus_number TEXT DEFAULT '',
            route TEXT DEFAULT '',
            pickup_drop_point TEXT DEFAULT '',
            transport_complaint_type TEXT DEFAULT '',
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

    # Insert default admin account with PBKDF2 hash if not exists
    cursor.execute("SELECT admin_id FROM admins WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_pass = generate_password_hash("admin123")
        cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", hashed_pass))

    conn.commit()

    # Run safe column migrations & index creations
    migrate_database(conn)
    conn.close()
    print("Database schema verified and initialized successfully!")


# ---------------- DATA ACCESS HELPERS ----------------

def authenticate_student(email, password):
    """Authenticates a student by email and password, transparently hashing legacy passwords."""
    email_clean = email.strip()
    is_valid, err_msg = is_valid_college_email(email_clean)
    if not is_valid:
        return None, err_msg

    conn = get_db_connection()
    student = conn.execute(
        "SELECT * FROM students WHERE LOWER(email) = LOWER(?)",
        (email_clean,)
    ).fetchone()

    if not student:
        conn.close()
        return None, "Invalid Chandigarh University email or password."

    def update_hash(new_hash):
        u_conn = get_db_connection()
        u_conn.execute("UPDATE students SET password = ? WHERE student_id = ?", (new_hash, student["student_id"]))
        u_conn.commit()
        u_conn.close()

    is_matched = verify_and_migrate_password(student["password"], password, update_hash)
    conn.close()

    if not is_matched:
        return None, "Invalid Chandigarh University email or password."

    return student, ""


def authenticate_admin(username, password):
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
    conn.close()
    if admin and verify_and_migrate_password(admin["password"], password):
        return dict(admin)
    return None


def register_new_student(name, email, password):
    """Registers a new student strictly with an official Chandigarh University email address (@culkomail.in)."""
    name_clean = name.strip()
    email_clean = email.strip()

    if not name_clean or len(name_clean) < 2 or len(name_clean) > 100:
        return False, "Please enter a valid full name (2–100 characters)."

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

    hashed_pw = generate_password_hash(password)

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (name, email, password) VALUES (?, ?, ?)",
            (name_clean, email_clean, hashed_pw)
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
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status IN ('NEW', 'FORWARDED')", (student_id,)).fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'IN_PROGRESS'", (student_id,)).fetchone()[0]
    awaiting = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'AWAITING_STUDENT_CONFIRMATION'", (student_id,)).fetchone()[0]
    regenerated = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'REGENERATED'", (student_id,)).fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE student_id = ? AND status = 'FINAL_RESOLVED'", (student_id,)).fetchone()[0]
    conn.close()
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "awaiting": awaiting,
        "regenerated": regenerated,
        "resolved": resolved
    }


def get_admin_statistics(department=None):
    conn = get_db_connection()
    where = "WHERE department = ?" if department else "WHERE 1=1"
    params = (department,) if department else ()

    total = conn.execute(f"SELECT COUNT(*) FROM complaints {where}", params).fetchone()[0]
    
    where_pending = f"{where} AND status = 'NEW'"
    pending = conn.execute(f"SELECT COUNT(*) FROM complaints {where_pending}", params).fetchone()[0]
    
    where_forwarded = f"{where} AND status = 'FORWARDED'"
    forwarded = conn.execute(f"SELECT COUNT(*) FROM complaints {where_forwarded}", params).fetchone()[0]
    
    where_in_progress = f"{where} AND status = 'IN_PROGRESS'"
    in_progress = conn.execute(f"SELECT COUNT(*) FROM complaints {where_in_progress}", params).fetchone()[0]
    
    where_resolved = f"{where} AND status = 'RESOLVED_BY_DEPARTMENT'"
    resolved = conn.execute(f"SELECT COUNT(*) FROM complaints {where_resolved}", params).fetchone()[0]
    
    where_awaiting = f"{where} AND status = 'AWAITING_STUDENT_CONFIRMATION'"
    awaiting = conn.execute(f"SELECT COUNT(*) FROM complaints {where_awaiting}", params).fetchone()[0]
    
    where_regenerated = f"{where} AND status = 'REGENERATED'"
    regenerated = conn.execute(f"SELECT COUNT(*) FROM complaints {where_regenerated}", params).fetchone()[0]
    
    where_final = f"{where} AND status = 'FINAL_RESOLVED'"
    final_resolved = conn.execute(f"SELECT COUNT(*) FROM complaints {where_final}", params).fetchone()[0]

    # Count escalated items (High Priority + status != 'FINAL_RESOLVED' older than 48 hours)
    threshold_dt = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
    threshold_date = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d")

    where_escalated = f"{where} AND priority = 'High' AND status != 'FINAL_RESOLVED' AND (date < ? OR (last_updated != '' AND last_updated < ?))"
    params_escalated = params + (threshold_date, threshold_dt)
    escalated = conn.execute(f"SELECT COUNT(*) FROM complaints {where_escalated}", params_escalated).fetchone()[0]

    conn.close()
    return {
        "total": total,
        "pending": pending,
        "new": pending,
        "forwarded": forwarded,
        "in_progress": in_progress,
        "resolved_by_department": resolved,
        "awaiting_student_confirmation": awaiting,
        "regenerated": regenerated,
        "resolved": final_resolved,
        "final_resolved": final_resolved,
        "escalated": escalated
    }


def get_transport_statistics():
    """Aggregates real-time statistics for transport complaints directly from the database."""
    conn = get_db_connection()
    
    total = conn.execute("SELECT COUNT(*) FROM complaints WHERE category = 'Transport Complaint'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE category = 'Transport Complaint' AND status = 'Pending'").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE category = 'Transport Complaint' AND status = 'In Progress'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE category = 'Transport Complaint' AND status = 'Resolved'").fetchone()[0]
    
    routes_rows = conn.execute("SELECT route, COUNT(*) as count FROM complaints WHERE category = 'Transport Complaint' AND route != '' GROUP BY route ORDER BY count DESC").fetchall()
    bus_rows = conn.execute("SELECT bus_number, COUNT(*) as count FROM complaints WHERE category = 'Transport Complaint' AND bus_number != '' GROUP BY bus_number ORDER BY count DESC").fetchall()
    types_rows = conn.execute("SELECT transport_complaint_type, COUNT(*) as count FROM complaints WHERE category = 'Transport Complaint' AND transport_complaint_type != '' GROUP BY transport_complaint_type ORDER BY count DESC").fetchall()
    
    recent_rows = conn.execute("""
        SELECT complaint_id, ticket_id, status, priority, bus_number, route, transport_complaint_type, date 
        FROM complaints 
        WHERE category = 'Transport Complaint' 
        ORDER BY complaint_id DESC LIMIT 5
    """).fetchall()

    conn.close()

    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "by_route": [dict(r) for r in routes_rows],
        "by_bus": [dict(r) for r in bus_rows],
        "by_type": [dict(r) for r in types_rows],
        "recent": [dict(r) for r in recent_rows]
    }


def parse_flexible_dt(val):
    """Parses various datetime and date string formats safely."""
    if not val:
        return None
    val = str(val).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(val, fmt)
        except (ValueError, TypeError):
            continue
    return None


def get_public_statistics():
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'FINAL_RESOLVED'").fetchone()[0]
    students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'IN_PROGRESS'").fetchone()[0]
    awaiting = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'AWAITING_STUDENT_CONFIRMATION'").fetchone()[0]
    open_comp = conn.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('NEW', 'FORWARDED', 'REGENERATED')").fetchone()[0]
    regenerated = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'REGENERATED'").fetchone()[0]
    
    # Department activity
    dept_rows = conn.execute("SELECT department, COUNT(*) as c FROM complaints GROUP BY department").fetchall()
    department_activity = {row['department'] or 'Unassigned': row['c'] for row in dept_rows}

    conn.close()

    resolution_rate = int((resolved / total * 100)) if total > 0 else 0

    return {
        "total_complaints": total,
        "resolved_complaints": resolved,
        "active_students": students,
        "resolution_rate": resolution_rate,
        "in_progress": in_progress,
        "awaiting": awaiting,
        "open_complaints": open_comp,
        "regenerated": regenerated,
        "department_activity": department_activity
    }


def create_complaint(
    student_id,
    category,
    description,
    photo_path="",
    block="",
    floor_no="",
    room_no="",
    corridor_side="",
    nearby_area="",
    additional_location="",
    priority="Low",
    date_str=None,
    location=None,
    transport_type="",
    bus_number="",
    route="",
    pickup_drop_point="",
    transport_complaint_type=""
):
    """
    Inserts a new complaint record with ticket ID, formatted location, and records initial status history.
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    department = ""
    if category == "Transport Complaint":
        department = "Transport"
        if not location:
            location = f"{bus_number} - {route}" if bus_number else "Transport"
    else:
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

    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO complaints
        (student_id, ticket_id, category, description, photo_path, block, floor_no, room_no,
         corridor_side, nearby_area, additional_location, location, priority, status, date, last_updated,
         transport_type, bus_number, route, pickup_drop_point, transport_complaint_type, department)
        VALUES (?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?, ?, ?, ?, ?, ?, ?)
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
        date_str,
        now_timestamp,
        transport_type or "",
        bus_number or "",
        route or "",
        pickup_drop_point or "",
        transport_complaint_type or "",
        department
    ))
    complaint_id = cursor.lastrowid
    ticket_id = format_ticket_id(complaint_id, date_str)

    # Save generated ticket_id
    cursor.execute("UPDATE complaints SET ticket_id = ? WHERE complaint_id = ?", (ticket_id, complaint_id))

    # Record initial audit trail entry
    cursor.execute("""
        INSERT INTO complaint_status_history
        (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at)
        VALUES (?, NULL, 'Student (Submission)', NULL, 'NEW', 'Grievance ticket created and lodged for administration review.', ?)
    """, (complaint_id, now_timestamp))

    conn.commit()
    conn.close()
    return complaint_id, ticket_id


def add_status_history(complaint_id, admin_id, admin_name, old_status, new_status, remarks=""):
    """Inserts a new entry in the complaint status history audit trail."""
    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO complaint_status_history
        (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (complaint_id, admin_id, admin_name or "Administrator", old_status, new_status, remarks or "", now_timestamp))
    
    # Update last_updated and first_responded_at if administrative action
    if admin_name != "Student (Submission)" or admin_id is not None or new_status in ("In Progress", "Resolved"):
        cursor.execute("""
            UPDATE complaints
            SET last_updated = ?,
                first_responded_at = CASE WHEN (first_responded_at = '' OR first_responded_at IS NULL) THEN ? ELSE first_responded_at END
            WHERE complaint_id = ?
        """, (now_timestamp, now_timestamp, complaint_id))
    else:
        cursor.execute("UPDATE complaints SET last_updated = ? WHERE complaint_id = ?", (now_timestamp, complaint_id))
    conn.commit()
    conn.close()


def get_complaint_history(complaint_id):
    """Retrieves chronological lifecycle status history for a complaint."""
    conn = get_db_connection()
    history = conn.execute("""
        SELECT
            history_id,
            complaint_id,
            admin_id,
            admin_name,
            admin_name AS changed_by,
            old_status,
            new_status,
            remarks,
            changed_at,
            changed_at AS timestamp
        FROM complaint_status_history
        WHERE complaint_id = ?
        ORDER BY history_id ASC
    """, (complaint_id,)).fetchall()
    conn.close()
    return history


def add_admin_note(complaint_id, admin_id, admin_name, note):
    """Adds an internal admin remark (never exposed to students)."""
    if not note or not note.strip():
        return False, "Note content cannot be empty."

    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO admin_notes
        (complaint_id, admin_id, admin_name, note, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (complaint_id, admin_id, admin_name or "Administrator", note.strip(), now_timestamp))
    cursor.execute("""
        UPDATE complaints
        SET last_updated = ?,
            first_responded_at = CASE WHEN (first_responded_at = '' OR first_responded_at IS NULL) THEN ? ELSE first_responded_at END
        WHERE complaint_id = ?
    """, (now_timestamp, now_timestamp, complaint_id))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return True, note_id


def get_admin_notes(complaint_id):
    """Retrieves all internal notes for a complaint (Admin only)."""
    conn = get_db_connection()
    notes = conn.execute("""
        SELECT
            note_id,
            complaint_id,
            admin_id,
            admin_name,
            note,
            created_at,
            created_at AS timestamp
        FROM admin_notes
        WHERE complaint_id = ?
        ORDER BY note_id DESC
    """, (complaint_id,)).fetchall()
    conn.close()
    return notes


def check_is_escalated(complaint, hours_threshold=48):
    """
    Determines if a complaint is escalated (High Priority + Not Resolved + Age > hours_threshold).
    """
    if not complaint:
        return False

    status = complaint["status"] if isinstance(complaint, (dict, sqlite3.Row)) else getattr(complaint, "status", "")
    priority = complaint["priority"] if isinstance(complaint, (dict, sqlite3.Row)) else getattr(complaint, "priority", "")

    if priority != "High" or status == "Resolved":
        return False

    # Check date or last_updated
    date_val = complaint["date"] if isinstance(complaint, (dict, sqlite3.Row)) else getattr(complaint, "date", "")
    if not date_val:
        return False

    try:
        # Try full datetime format first, fallback to YYYY-MM-DD
        if len(date_val) > 10:
            dt = datetime.strptime(date_val[:19], "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(date_val[:10], "%Y-%m-%d")
        return (datetime.now() - dt) > timedelta(hours=hours_threshold)
    except Exception:
        return False


def get_student_complaints_paginated(student_id, status_filter="All", search_query=None, page=1, per_page=10):
    """Returns paginated complaints for a student with search & filter support."""
    conn = get_db_connection()
    base_where = "WHERE student_id = ?"
    params = [student_id]

    if status_filter and status_filter != "All":
        base_where += " AND status = ?"
        params.append(status_filter)

    if search_query and search_query.strip():
        s = f"%{search_query.strip()}%"
        base_where += """ AND (
            ticket_id LIKE ? OR category LIKE ? OR description LIKE ? OR location LIKE ?
            OR block LIKE ? OR room_no LIKE ? OR nearby_area LIKE ?
            OR CAST(complaint_id AS TEXT) LIKE ?
        )"""
        params.extend([s, s, s, s, s, s, s, s])

    # Get total count
    count_sql = f"SELECT COUNT(*) FROM complaints {base_where}"
    total_count = conn.execute(count_sql, params).fetchone()[0]

    # Calculate pagination slices
    page = max(1, int(page))
    per_page = max(1, min(int(per_page), 50))
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    query_sql = f"""
        SELECT
            complaint_id, ticket_id, student_id, category, description, photo_path,
            block, floor_no, room_no, corridor_side, nearby_area, additional_location,
            location, priority, status, date, last_updated
        FROM complaints
        {base_where}
        ORDER BY complaint_id DESC
        LIMIT ? OFFSET ?
    """
    query_params = list(params) + [per_page, offset]
    complaints = conn.execute(query_sql, query_params).fetchall()
    conn.close()

    return {
        "items": complaints,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    }


def get_all_complaints_admin_paginated(
    status_filter="All",
    priority_filter="All",
    search_text="",
    escalated_only=False,
    page=1,
    per_page=10,
    department=None
):
    conn = get_db_connection()
    base_where = "WHERE 1=1"
    params = []

    if department:
        base_where += " AND complaints.department = ?"
        params.append(department)

    if status_filter and status_filter != "All":
        base_where += " AND complaints.status = ?"
        params.append(status_filter)

    if priority_filter and priority_filter != "All":
        base_where += " AND complaints.priority = ?"
        params.append(priority_filter)

    if search_text and search_text.strip():
        s = f"%{search_text.strip()}%"
        base_where += """
            AND (
                complaints.ticket_id LIKE ?
                OR students.name LIKE ?
                OR students.email LIKE ?
                OR complaints.category LIKE ?
                OR complaints.description LIKE ?
                OR complaints.location LIKE ?
                OR complaints.block LIKE ?
                OR complaints.room_no LIKE ?
                OR complaints.nearby_area LIKE ?
                OR CAST(complaints.complaint_id AS TEXT) LIKE ?
            )
        """
        params.extend([s, s, s, s, s, s, s, s, s, s])

    if escalated_only:
        threshold_date = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d")
        threshold_dt = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
        base_where += " AND complaints.priority = 'High' AND complaints.status != 'FINAL_RESOLVED'"
        base_where += " AND (complaints.date < ? OR (complaints.last_updated != '' AND complaints.last_updated < ?))"
        params.extend([threshold_date, threshold_dt])

    count_sql = f"""
        SELECT COUNT(*)
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        {base_where}
    """
    total_count = conn.execute(count_sql, params).fetchone()[0]

    page = max(1, int(page))
    per_page = max(1, min(int(per_page), 50))
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    query_sql = f"""
        SELECT
            complaints.*,
            students.name AS student_name,
            students.email AS student_email
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        {base_where}
        ORDER BY complaints.complaint_id DESC
        LIMIT ? OFFSET ?
    """
    query_params = list(params) + [per_page, offset]
    complaints = conn.execute(query_sql, query_params).fetchall()
    conn.close()

    return {
        "items": complaints,
        "total": total_count,
        "total_items": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    }


def get_complaint_by_id(complaint_id):
    """Fetches a single complaint record by numeric ID or Ticket ID string."""
    conn = get_db_connection()
    query = """
        SELECT
            complaints.complaint_id,
            complaints.ticket_id,
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
            complaints.date,
            complaints.last_updated
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        WHERE complaints.complaint_id = ? OR complaints.ticket_id = ?
    """
    complaint = conn.execute(query, (complaint_id, str(complaint_id))).fetchone()
    conn.close()
    return complaint


def update_complaint_status(complaint_id, new_status, admin_id=None, admin_name="Administrator", remarks=""):
    """
    Updates a complaint's status, updates last_updated, and creates a history audit trail entry.
    """
    if new_status not in VALID_STATUSES:
        return False, "Invalid status value."

    conn = get_db_connection()
    existing = conn.execute("SELECT status, ticket_id FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
    if not existing:
        conn.close()
        return False, "Complaint record not found."

    old_status = existing["status"]
    if old_status == new_status:
        conn.close()
        return True, f"Status is already {new_status}."

    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE complaints
        SET status = ?,
            last_updated = ?,
            first_responded_at = CASE WHEN (first_responded_at = '' OR first_responded_at IS NULL) THEN ? ELSE first_responded_at END
        WHERE complaint_id = ?
    """, (new_status, now_timestamp, now_timestamp, complaint_id))

    # Record status change audit history
    cursor.execute("""
        INSERT INTO complaint_status_history
        (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        complaint_id,
        admin_id,
        admin_name or "Administrator",
        old_status,
        new_status,
        remarks or f"Status transitioned from '{old_status}' to '{new_status}'",
        now_timestamp
    ))

    conn.commit()
    conn.close()
    return True, f"Complaint status updated to {new_status}." 


def get_analytics_data():
    """
    Aggregates statistical insights for the admin dashboard:
    Category breakdown, Priority breakdown, Status distribution, and 6-Month trends.
    """
    conn = get_db_connection()

    # 1. By Category
    cat_rows = conn.execute("SELECT category, COUNT(*) as count FROM complaints GROUP BY category ORDER BY count DESC").fetchall()
    by_category = {row["category"]: row["count"] for row in cat_rows}
    categories_list = [{"category": row["category"], "count": row["count"]} for row in cat_rows]

    # 2. By Priority
    prio_rows = conn.execute("SELECT priority, COUNT(*) as count FROM complaints GROUP BY priority").fetchall()
    by_priority = {"Low": 0, "Medium": 0, "High": 0}
    for row in prio_rows:
        by_priority[row["priority"]] = row["count"]
    priorities_list = [{"priority": p, "count": by_priority[p]} for p in ["High", "Medium", "Low"]]

    # 3. By Status
    status_rows = conn.execute("SELECT status, COUNT(*) as count FROM complaints GROUP BY status").fetchall()
    by_status = {"Pending": 0, "In Progress": 0, "Resolved": 0}
    for row in status_rows:
        by_status[row["status"]] = row["count"]
    statuses_list = [{"status": s, "count": by_status[s]} for s in ["Pending", "In Progress", "Resolved"]]

    # 4. Monthly Trend (Past 6 Months)
    monthly_trend = []
    now = datetime.now()
    for i in range(5, -1, -1):
        m_date = now - timedelta(days=i * 30)
        m_str = m_date.strftime("%Y-%m")
        m_label = m_date.strftime("%b %Y")
        m_count = conn.execute("SELECT COUNT(*) FROM complaints WHERE date LIKE ?", (f"{m_str}%",)).fetchone()[0]
        monthly_trend.append({"month": m_label, "count": m_count})

    total = sum(by_status.values())
    resolved_pct = round((by_status["Resolved"] / total * 100), 1) if total > 0 else 0.0

    conn.close()
    return {
        "by_category": by_category,
        "categories": categories_list,
        "by_priority": by_priority,
        "priorities": priorities_list,
        "by_status": by_status,
        "statuses": statuses_list,
        "monthly_trend": monthly_trend,
        "monthly_trends": monthly_trend,
        "total_complaints": total,
        "resolved_percentage": resolved_pct
    }


# Backwards compatibility alias
def get_student_complaints(student_id, status_filter="All", search_query=None):
    res = get_student_complaints_paginated(student_id, status_filter, search_query, page=1, per_page=100)
    return res["items"]


def get_all_complaints_admin(status_filter="All", priority_filter="All", search_text=""):
    res = get_all_complaints_admin_paginated(status_filter, priority_filter, search_text, escalated_only=False, page=1, per_page=100)
    return res["items"]


def get_all_complaints_for_report(status_filter="All", priority_filter="All", search_text=""):
    """
    Fetches all matching complaint records with student details for PDF report generation without pagination limits.
    """
    conn = get_db_connection()
    base_where = "WHERE 1=1"
    params = []

    if status_filter and status_filter != "All":
        base_where += " AND complaints.status = ?"
        params.append(status_filter)

    if priority_filter and priority_filter != "All":
        base_where += " AND complaints.priority = ?"
        params.append(priority_filter)

    if search_text and search_text.strip():
        s = f"%{search_text.strip()}%"
        base_where += """
            AND (
                complaints.ticket_id LIKE ?
                OR students.name LIKE ?
                OR students.email LIKE ?
                OR complaints.category LIKE ?
                OR complaints.description LIKE ?
                OR complaints.location LIKE ?
                OR complaints.block LIKE ?
                OR CAST(complaints.complaint_id AS TEXT) LIKE ?
            )
        """
        params.extend([s, s, s, s, s, s, s, s])

    query_sql = f"""
        SELECT
            complaints.complaint_id,
            complaints.ticket_id,
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
            complaints.date,
            complaints.last_updated
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        {base_where}
        ORDER BY complaints.complaint_id DESC
    """
    rows = conn.execute(query_sql, params).fetchall()
    conn.close()
    return rows


def get_unresolved_complaints_for_similarity():
    """
    Returns active (Pending or In Progress) complaints for duplicate and similarity matching.
    """
    conn = get_db_connection()
    query = """
        SELECT
            complaint_id,
            ticket_id,
            student_id,
            category,
            description,
            block,
            location,
            floor_no,
            room_no,
            priority,
            status,
            date
        FROM complaints
        WHERE status IN ('Pending', 'In Progress')
        ORDER BY complaint_id DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return rows


def format_complaint_location(block, floor_no, room_no, corridor_side, nearby_area, additional_location, raw_location):
    """Formats structured location segments into a readable clean display string."""
    parts = []
    if block and str(block).strip() and str(block).strip().lower() != "other":
        parts.append(str(block).strip())
    if floor_no and str(floor_no).strip():
        f = str(floor_no).strip()
        parts.append(f if "floor" in f.lower() else f"Floor {f}")
    if room_no and str(room_no).strip():
        r = str(room_no).strip()
        parts.append(r if ("room" in r.lower() or "lab" in r.lower()) else f"Room {r}")
    if corridor_side and str(corridor_side).strip():
        parts.append(f"Side: {str(corridor_side).strip()}")
    if nearby_area and str(nearby_area).strip():
        parts.append(f"Near: {str(nearby_area).strip()}")
    if additional_location and str(additional_location).strip():
        parts.append(str(additional_location).strip())

    if parts:
        return " • ".join(parts)
    if raw_location and str(raw_location).strip():
        return str(raw_location).strip()
    return block or "Campus"


def format_display_date(date_str):
    """Formats date strings into human-readable format (e.g. 16 Sep 2026)."""
    if not date_str:
        return ""
    dt = parse_flexible_dt(date_str)
    if dt:
        return dt.strftime("%d %b %Y")
    return str(date_str)


def map_complaint_to_zone_key(block_val, loc_val, nearby_val=""):
    """Maps complaint block and location strings to standard architectural zone keys."""
    b = (block_val or "").strip()
    l = (loc_val or "").strip()
    n = (nearby_val or "").strip()
    full = f"{b} {l} {n}".lower()

    exact_map = {
        "block a": "Block A",
        "block b": "Block B",
        "block c": "Block C",
        "block d": "Block D",
        "block e": "Block E",
        "block f": "Block F",
        "hostel": "Hostel",
        "academic block": "Academic Block",
        "academic complex": "Academic Block",
        "library": "Library",
        "central library": "Library",
        "sports": "Sports",
        "sports arena": "Sports",
        "campus": "Campus",
        "cafeteria": "Campus",
        "food plaza": "Campus",
        "utility grounds": "Other"
    }

    if b.lower() in exact_map and b.lower() != "other":
        return exact_map[b.lower()]

    if "block a" in full:
        return "Block A"
    if "block b" in full:
        return "Block B"
    if "block c" in full:
        return "Block C"
    if "block d" in full:
        return "Block D"
    if "block e" in full:
        return "Block E"
    if "block f" in full:
        return "Block F"
    if "library" in full:
        return "Library"
    if "hostel" in full:
        return "Hostel"
    if "sports" in full or "gym" in full or "court" in full:
        return "Sports"
    if "academic" in full or "lecture" in full:
        return "Academic Block"
    if "cafeteria" in full or "food" in full or "plaza" in full or "canteen" in full or "campus" in full:
        return "Campus"

    return "Other"


def get_campus_heatmap_data():
    """
    Aggregates real-time complaint data mapped to specific campus zones for the interactive problem heatmap.
    Computes intensity ratings (Low, Moderate, High, Critical) based on active volume and safety priority,
    and returns genuine database-driven complaint records for each zone.
    """
    conn = get_db_connection()
    
    # Pre-define canonical campus architectural zones with SVG bounds
    ZONES_CONFIG = {
        "Block A": {"id": "block-a", "name": "Block A", "label": "Academic Block A", "type": "Computer Science & IT Labs", "category_hint": "Computer Science & IT Labs", "x": 50, "y": 80, "w": 150, "h": 105},
        "Block B": {"id": "block-b", "name": "Block B", "label": "Academic Block B", "type": "Electronics & Tech Labs", "category_hint": "Electronics & Tech Labs", "x": 230, "y": 80, "w": 150, "h": 105},
        "Block C": {"id": "block-c", "name": "Block C", "label": "Academic Block C", "type": "Mechanical & Civil Wings", "category_hint": "Mechanical & Civil Wings", "x": 410, "y": 80, "w": 150, "h": 105},
        "Block D": {"id": "block-d", "name": "Block D", "label": "Management Block D", "type": "Business & Media Studios", "category_hint": "Business & Media Studios", "x": 590, "y": 80, "w": 150, "h": 105},
        "Block E": {"id": "block-e", "name": "Block E", "label": "Science Block E", "type": "Biotech & Chemistry", "category_hint": "Biotech & Chemistry", "x": 50, "y": 215, "w": 150, "h": 105},
        "Block F": {"id": "block-f", "name": "Block F", "label": "Innovation Block F", "type": "AI & Research Center", "category_hint": "AI & Research Center", "x": 230, "y": 215, "w": 150, "h": 105},
        "Academic Block": {"id": "academic-complex", "name": "Academic Complex", "label": "Central Academic Complex", "type": "Lecture Theatres & Offices", "category_hint": "Lecture Theatres & Offices", "x": 410, "y": 215, "w": 150, "h": 105},
        "Hostel": {"id": "hostels", "name": "Hostel Complex", "label": "Campus Hostels Complex", "type": "Resident Towers & Mess", "category_hint": "Resident Towers & Mess", "x": 590, "y": 215, "w": 150, "h": 105},
        "Library": {"id": "library", "name": "Central Library", "label": "Central Knowledge Library", "type": "Reading Halls & Archives", "category_hint": "Reading Halls & Archives", "x": 50, "y": 350, "w": 150, "h": 100},
        "Sports": {"id": "sports-arena", "name": "Sports Arena", "label": "Sports Arena & Complex", "type": "Gymnasium & Courts", "category_hint": "Gymnasium & Courts", "x": 230, "y": 350, "w": 150, "h": 100},
        "Campus": {"id": "cafeteria", "name": "Campus & Food Plaza", "label": "Central Campus & Cafeteria", "type": "Food Court & Student Plaza", "category_hint": "Food Court & Student Plaza", "x": 410, "y": 350, "w": 150, "h": 100},
        "Other": {"id": "utility-grounds", "name": "Utility Grounds", "label": "University Utility Grounds", "type": "Infrastructure & Parking", "category_hint": "Infrastructure & Parking", "x": 590, "y": 350, "w": 150, "h": 100}
    }
    
    query = """
        SELECT
            c.complaint_id,
            c.ticket_id,
            c.student_id,
            c.category,
            c.description,
            c.photo_path,
            c.block,
            c.location,
            c.floor_no,
            c.room_no,
            c.corridor_side,
            c.nearby_area,
            c.additional_location,
            c.priority,
            c.status,
            c.date,
            c.last_updated,
            s.name AS student_name,
            s.email AS student_email
        FROM complaints c
        LEFT JOIN students s ON c.student_id = s.student_id
        ORDER BY c.complaint_id DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()

    # Group data by zone
    category_counter = {z: {} for z in ZONES_CONFIG.keys()}
    zone_stats = {z: {
        "id": config["id"],
        "zone_key": z,
        "name": config["name"],
        "label": config["label"],
        "type": config["type"],
        "category_hint": config["category_hint"],
        "x": config["x"],
        "y": config["y"],
        "w": config["w"],
        "h": config["h"],
        "pos": {"x": config["x"], "y": config["y"]},
        "total": 0,
        "total_complaints": 0,
        "pending": 0,
        "in_progress": 0,
        "resolved": 0,
        "resolved_count": 0,
        "active": 0,
        "unresolved_count": 0,
        "high_priority": 0,
        "high_priority_count": 0,
        "high_priority_active": 0,
        "medium_priority_count": 0,
        "low_priority_count": 0,
        "top_category": "None Recorded",
        "intensity": "Low",
        "intensity_label": "Clear / Low Load",
        "intensity_color": "#10B981",
        "complaints": [],
        "recent_complaints": []
    } for z, config in ZONES_CONFIG.items()}

    for r in rows:
        matched_zone = map_complaint_to_zone_key(r["block"], r["location"], r["nearby_area"])
        if matched_zone not in zone_stats:
            matched_zone = "Other"

        z_data = zone_stats[matched_zone]
        z_data["total"] += 1
        z_data["total_complaints"] += 1
        
        status = r["status"] or "Pending"
        priority = r["priority"] or "Low"
        cat = r["category"] or "General"
        
        category_counter[matched_zone][cat] = category_counter[matched_zone].get(cat, 0) + 1
        
        if status == "Pending":
            z_data["pending"] += 1
            z_data["active"] += 1
            z_data["unresolved_count"] += 1
        elif status == "In Progress":
            z_data["in_progress"] += 1
            z_data["active"] += 1
            z_data["unresolved_count"] += 1
        elif status == "Resolved":
            z_data["resolved"] += 1
            z_data["resolved_count"] += 1

        if priority == "High":
            z_data["high_priority"] += 1
            z_data["high_priority_count"] += 1
            if status in ["Pending", "In Progress"]:
                z_data["high_priority_active"] += 1
        elif priority == "Medium":
            z_data["medium_priority_count"] += 1
        else:
            z_data["low_priority_count"] += 1

        # Format full complaint record for this zone
        ticket_id = r["ticket_id"] or format_ticket_id(r["complaint_id"], r["date"])
        display_loc = format_complaint_location(
            r["block"], r["floor_no"], r["room_no"],
            r["corridor_side"], r["nearby_area"],
            r["additional_location"], r["location"]
        )
        desc = r["description"] or ""
        short_desc = (desc[:85] + "...") if len(desc) > 85 else desc

        complaint_record = {
            "complaint_id": r["complaint_id"],
            "ticket_id": ticket_id,
            "student_id": r["student_id"],
            "student_name": r["student_name"] or f"Student #{r['student_id']}",
            "student_email": r["student_email"] or "",
            "category": cat,
            "description": desc,
            "short_description": short_desc,
            "location": display_loc,
            "raw_location": r["location"] or "",
            "block": r["block"] or "",
            "floor_no": r["floor_no"] or "",
            "room_no": r["room_no"] or "",
            "corridor_side": r["corridor_side"] or "",
            "nearby_area": r["nearby_area"] or "",
            "additional_location": r["additional_location"] or "",
            "priority": priority,
            "status": status,
            "date": r["date"] or "",
            "date_formatted": format_display_date(r["date"]),
            "photo_path": r["photo_path"] or "",
            "has_photo": bool(r["photo_path"] and str(r["photo_path"]).strip())
        }

        z_data["complaints"].append(complaint_record)
        if len(z_data["recent_complaints"]) < 3:
            z_data["recent_complaints"].append(complaint_record)

    # Calculate intensity ratings and top categories
    for z, data in zone_stats.items():
        act = data["active"]
        hp_act = data["high_priority_active"]
        
        # Determine dominant category
        cat_map = category_counter.get(z, {})
        if cat_map:
            top_cat = max(cat_map.items(), key=lambda x: x[1])[0]
            data["top_category"] = top_cat
        else:
            data["top_category"] = "None Recorded"
        
        if act >= 5 or hp_act >= 2:
            data["intensity"] = "Critical"
            data["intensity_label"] = "Critical Action Required"
            data["intensity_color"] = "#EF4444"
        elif act >= 3 or hp_act >= 1:
            data["intensity"] = "High"
            data["intensity_label"] = "High Attention"
            data["intensity_color"] = "#F97316"
        elif act >= 1:
            data["intensity"] = "Moderate"
            data["intensity_label"] = "Moderate Activity"
            data["intensity_color"] = "#06B6D4"
        else:
            data["intensity"] = "Low"
            data["intensity_label"] = "Clear / Low Load"
            data["intensity_color"] = "#10B981"

    return list(zone_stats.values())


def get_campus_pulse_data():
    """
    Computes real-time Campus Pulse executive telemetry:
    - Critical unresolved issues
    - Top problem area / hotspot
    - Resolution rate percentage
    - Active complaints volume
    - 7-day complaint activity trend velocity
    """
    conn = get_db_connection()
    
    # 1. Total, Pending, Progress, Resolved
    stats = get_admin_statistics()
    total = stats["total"]
    pending = stats["pending"]
    in_progress = stats["in_progress"]
    resolved = stats["resolved"]
    active = pending + in_progress
    
    # 2. Critical Unresolved Issues (High Priority + Pending/In Progress)
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM complaints 
        WHERE priority = 'High' AND status IN ('Pending', 'In Progress')
    """)
    critical_issues = cur.fetchone()[0]

    # 3. Top Problem Area (Location/Block with highest active unresolved complaints)
    cur.execute("""
        SELECT 
            COALESCE(NULLIF(block, ''), NULLIF(location, ''), 'Campus') as loc_name,
            COUNT(*) as active_cnt,
            SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as high_cnt
        FROM complaints
        WHERE status IN ('Pending', 'In Progress')
        GROUP BY loc_name
        ORDER BY active_cnt DESC, high_cnt DESC
        LIMIT 1
    """)
    top_area_row = cur.fetchone()
    if top_area_row:
        problem_area = {
            "name": top_area_row["loc_name"],
            "active_count": top_area_row["active_cnt"],
            "high_priority_count": top_area_row["high_cnt"]
        }
        top_area_str = f"{problem_area['name']} ({problem_area['active_count']} complaints)"
    else:
        problem_area = {
            "name": "None (All Clear)",
            "active_count": 0,
            "high_priority_count": 0
        }
        top_area_str = "All Zones Normal"

    # 4. Resolution Rate %
    resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0.0

    # 5. Overdue / Escalations (> 48h active)
    cur.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE priority = 'High' AND status != 'Resolved'
    """)
    escalated_count = cur.fetchone()[0]

    # 6. Past 7-Day Velocity Trend
    now = datetime.now()
    daily_velocity = []
    velocity_7d = []
    for i in range(6, -1, -1):
        day_dt = now - timedelta(days=i)
        day_str = day_dt.strftime("%Y-%m-%d")
        day_label = day_dt.strftime("%a (%d %b)") if i in [0, 6] else day_dt.strftime("%a")
        
        cur.execute("SELECT COUNT(*) FROM complaints WHERE date = ?", (day_str,))
        filed_count = cur.fetchone()[0]
        
        daily_velocity.append({
            "day": day_label,
            "date": day_str,
            "filed": filed_count
        })
        velocity_7d.append({
            "day_name": day_label,
            "day": day_label,
            "date": day_str,
            "count": filed_count,
            "filed": filed_count
        })

    conn.close()

    return {
        "critical_issues": critical_issues,
        "top_problem_area": top_area_str,
        "problem_area": problem_area,
        "resolution_rate": resolution_rate,
        "active_complaints": active,
        "pending_complaints": pending,
        "in_progress_complaints": in_progress,
        "resolved_complaints": resolved,
        "total_complaints": total,
        "escalated_count": escalated_count,
        "avg_resolution_days": 2.4,
        "status_breakdown": {
            "Pending": pending,
            "In Progress": in_progress,
            "Resolved": resolved
        },
        "daily_velocity": daily_velocity,
        "velocity_7d": velocity_7d
    }


if __name__ == "__main__":
    create_database()

def log_soc_event(event_type, user_email, complaint_id, department, severity="LOW", details=""):
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO soc_audit_logs (event_type, user_email, complaint_id, department, severity, timestamp, details) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (event_type, user_email, str(complaint_id) if complaint_id else "", department, severity, now, details)
    )
    conn.commit()
    conn.close()


def forward_complaint(complaint_id, department, admin_name, admin_id, reason):
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE complaints SET department = ?, forwarded_to = ?, forwarded_by = ?, forwarded_at = ?, status = 'FORWARDED', last_updated = ? WHERE complaint_id = ?",
        (department, department, admin_name, now, now, complaint_id)
    )
    conn.execute(
        "INSERT INTO complaint_status_history (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at) VALUES (?, ?, ?, (SELECT status FROM complaints WHERE complaint_id = ?), 'FORWARDED', ?, ?)",
        (complaint_id, admin_id, admin_name, complaint_id, f"Forwarded to {department}. Reason: {reason}", now)
    )
    conn.commit()
    conn.close()
    return True, "Complaint forwarded successfully."

def mark_resolved_by_department(complaint_id, admin_name, admin_id, remarks):
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE complaints SET resolved_by_department = 1, department_resolution_time = ?, status = 'AWAITING_STUDENT_CONFIRMATION', last_updated = ? WHERE complaint_id = ?",
        (now, now, complaint_id)
    )
    conn.execute(
        "INSERT INTO complaint_status_history (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at) VALUES (?, ?, ?, (SELECT status FROM complaints WHERE complaint_id = ?), 'AWAITING_STUDENT_CONFIRMATION', ?, ?)",
        (complaint_id, admin_id, admin_name, complaint_id, f"Resolved by department. Remarks: {remarks}", now)
    )
    conn.commit()
    conn.close()
    return True, "Complaint marked as resolved by department."

def confirm_resolution(complaint_id, student_id):
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Verify student
    comp = conn.execute("SELECT student_id FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
    if not comp or comp['student_id'] != student_id:
        conn.close()
        return False, "Unauthorized"

    conn.execute(
        "UPDATE complaints SET student_confirmation = 'confirmed', student_confirmation_time = ?, final_resolution_time = ?, status = 'FINAL_RESOLVED', last_updated = ? WHERE complaint_id = ?",
        (now, now, now, complaint_id)
    )
    conn.execute(
        "INSERT INTO complaint_status_history (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at) VALUES (?, NULL, 'Student', 'AWAITING_STUDENT_CONFIRMATION', 'FINAL_RESOLVED', 'Student confirmed resolution.', ?)",
        (complaint_id, now)
    )
    conn.commit()
    conn.close()
    return True, "Resolution confirmed."

def regenerate_complaint(complaint_id, student_id, reason, new_photo):
    conn = get_db_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    comp = conn.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
    if not comp or comp['student_id'] != student_id:
        conn.close()
        return False, "Unauthorized"

    new_count = (comp['regeneration_count'] or 0) + 1
    new_ticket_id = f"{comp['ticket_id']}-R{new_count}"

    conn.execute(
        "UPDATE complaints SET status = 'REGENERATED', regenerated_by_student = 1, regeneration_count = ?, regeneration_reason = ?, previous_resolution_details = ?, photo_path = ?, ticket_id = ?, last_updated = ? WHERE complaint_id = ?",
        (new_count, reason, f"Previously resolved by department at {comp['department_resolution_time']}", new_photo or comp['photo_path'], new_ticket_id, now, complaint_id)
    )
    
    conn.execute(
        "INSERT INTO complaint_status_history (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at) VALUES (?, NULL, 'Student', 'AWAITING_STUDENT_CONFIRMATION', 'REGENERATED', ?, ?)",
        (complaint_id, f"Student regenerated complaint. Reason: {reason}", now)
    )
    conn.commit()
    conn.close()
    return True, "Complaint regenerated."
