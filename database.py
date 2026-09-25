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
VALID_STATUSES = ["NEW", "FORWARDED", "IN_PROGRESS", "RESOLUTION_SUBMITTED", "AWAITING_STUDENT_CONFIRMATION", "REOPENED", "FINAL_RESOLVED"]
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


# ---------------- COMPLAINT FINGERPRINTING & NORMALIZATION ----------------

def normalize_issue_text(text, room_no=""):
    """
    Normalizes issue description for robust complaint fingerprinting:
    - Lowercase conversion
    - Contraction expansion (e.g. isn't -> is not)
    - Punctuation removal
    - Stop word filtering (preserving negations like 'not', 'no')
    - Removal of room number digits already accounted for in location
    - Canonical stemming for common university fixture and failure terms
    - Sorted unique token set to prevent word-order bypass
    """
    if not text:
        return ""
    text = str(text).lower().strip()

    # Contraction expansion
    contractions = {
        "isn't": "is not", "aren't": "are not", "wasn't": "was not",
        "weren't": "were not", "don't": "do not", "doesn't": "does not",
        "didn't": "did not", "can't": "can not", "won't": "will not",
        "hasn't": "has not", "haven't": "have not", "hadn't": "had not",
        "it's": "it is", "that's": "that is"
    }
    for c, expanded in contractions.items():
        text = text.replace(c, expanded)

    # Tokenize alphanumeric words
    words = re.findall(r"[a-z0-9]+", text)

    # Room number digits to ignore from description if mentioned in location
    room_digits = set(re.findall(r"[0-9]+", str(room_no)))

    # Conversational & auxiliary stop words to ignore (keeps negations: 'not', 'no', 'off', 'down')
    stop_words = {
        "a", "an", "the", "is", "are", "am", "was", "were", "be", "been", "being",
        "and", "or", "in", "on", "at", "to", "for", "of", "with", "my", "our",
        "your", "this", "that", "these", "those", "it", "its", "there", "has",
        "have", "had", "do", "does", "did", "please", "kindly", "sir", "madam",
        "help", "issue", "problem", "complaint", "facing", "got", "get", "very",
        "really", "urgently", "urgent", "also", "just", "from", "by", "again",
        "room", "rooms", "ceiling", "properly", "all", "completely", "entirely",
        "totally", "well", "badly", "now", "still", "side", "area", "hall", "lab"
    }

    # Canonical stemming mappings for typical campus maintenance nouns & verbs
    stem_map = {
        "working": "work", "works": "work", "worked": "work",
        "leaking": "leak", "leaks": "leak", "leaked": "leak", "leakage": "leak",
        "flickering": "flicker", "flickers": "flicker", "flickered": "flicker",
        "sparking": "spark", "sparks": "spark", "sparked": "spark",
        "broken": "break", "breaking": "break", "breaks": "break",
        "choked": "choke", "choking": "choke", "chokes": "choke",
        "clogged": "clog", "clogging": "clog", "clogs": "clog",
        "dripping": "drip", "drips": "drip", "dripped": "drip",
        "fans": "fan", "lights": "light", "lighting": "light", "tubelights": "tubelight",
        "switches": "switch", "switchboards": "switchboard", "sockets": "socket",
        "taps": "tap", "sinks": "sink", "pipes": "pipe", "doors": "door",
        "windows": "window", "chairs": "chair", "benches": "bench",
        "tables": "table", "desks": "desk", "projectors": "projector",
        "routers": "router", "smelling": "smell", "smells": "smell", "ac": "ac",
        "airconditioner": "ac", "airconditioners": "ac",
        "cleaned": "clean", "cleaning": "clean", "cleans": "clean"   }

    cleaned_tokens = []
    for w in words:
        if w in room_digits:
            continue
        if w not in stop_words and len(w) > 1:
            stemmed = stem_map.get(w, w)
            cleaned_tokens.append(stemmed)

    # Sorted unique tokens guarantee consistent fingerprint regardless of minor wording order
    return " ".join(sorted(set(cleaned_tokens)))


ACTIVE_COMPLAINT_STATUSES = ("NEW", "PENDING", "IN_PROGRESS", "REOPENED", "FORWARDED")


def extract_canonical_room(room_str):
    """
    Extracts canonical room identifier from various free-text notations:
    e.g. 'E-329, RHS', 'Block E 2nd Floor , Room E-329, RHS (RHS)',
    'Room 204', 'rm 204', '204', 'Lab 2' -> '329', '204', 'lab 2'
    """
    if not room_str:
        return ""
    # Look for room/rm followed by room code or 2-4 digits with optional letters
    m = re.search(r"\b(?:room|rm)?[ -]?(?:[a-z]-?)?([0-9]{2,4}[a-z]?)\b", str(room_str), re.IGNORECASE)
    if m:
        return m.group(1).lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", str(room_str).lower()).strip()
    return cleaned


def get_canonical_location_key(
    category,
    block="",
    floor_no="",
    room_no="",
    location="",
    bus_number="",
    route="",
    transport_type=""
):
    """
    Computes a canonical location key for duplicate complaint detection:
    - Campus: {normalized_block}::{canonical_room}
    - Transport: transport::{type}::{bus}::{route}
    """
    cat_norm = (category or "").strip().lower()
    if cat_norm == "transport complaint":
        norm_bus = re.sub(r"(?i)\b(?:bus|no|#|\s)+\b", "", bus_number or "").strip().lower()
        norm_route = re.sub(r"\s+", " ", (route or "").strip().lower())
        norm_type = (transport_type or "").strip().lower()
        return f"transport::{norm_type}::{norm_bus}::{norm_route}"

    b = (block or location or "").strip().lower()
    b = re.sub(r"[\-_]+", " ", b)
    b = re.sub(r"\s+", " ", b)
    block_match = re.search(r"\bblock\s*([a-z0-9]+)\b|\b([a-z0-9]+)\s*block\b", b)
    if block_match:
        letter = block_match.group(1) or block_match.group(2)
        norm_block = f"block {letter}"
    else:
        norm_block = b

    norm_room = extract_canonical_room(room_no or location)
    return f"{norm_block}::{norm_room}"


def normalize_location_key(
    category,
    block="",
    floor_no="",
    room_no="",
    corridor_side="",
    nearby_area="",
    additional_location="",
    location="",
    transport_type="",
    bus_number="",
    route="",
    pickup_drop_point="",
    transport_complaint_type=""
):
    """
    Builds a normalized, canonical location string:
    - Transport: transport:{type}:{bus_number}:{route}
    - Campus: {normalized_block}|{normalized_floor}|{canonical_room}
    """
    cat_norm = (category or "").strip().lower()
    if cat_norm == "transport complaint":
        norm_bus = re.sub(r"(?i)\b(?:bus|no|#|\s)+\b", "", bus_number or "").strip().lower()
        norm_route = re.sub(r"\s+", " ", (route or "").strip().lower())
        norm_type = (transport_type or "").strip().lower()
        return f"transport:{norm_type}:{norm_bus}:{norm_route}"

    # Campus block normalization (e.g. 'Block E', 'block-e', 'E Block' -> 'block e')
    b = (block or location or "").strip().lower()
    b = re.sub(r"[\-_]+", " ", b)
    b = re.sub(r"\s+", " ", b)
    block_match = re.search(r"\bblock\s*([a-z0-9]+)\b|\b([a-z0-9]+)\s*block\b", b)
    if block_match:
        letter = block_match.group(1) or block_match.group(2)
        norm_block = f"block {letter}"
    else:
        norm_block = b

    # Canonical Room normalization
    norm_room = extract_canonical_room(room_no or location)

    # Floor normalization: e.g. 'Ground Floor', '2nd Floor' -> 'ground', '2'
    f = (floor_no or "").strip().lower()
    f = re.sub(r"(?i)\b(?:floor|flr|fl)\b", "", f).strip(" -_,.#")

    return f"{norm_block}|{f}|{norm_room}"


def is_similar_issue(desc1, desc2, room_no=""):
    tokens1 = set(normalize_issue_text(desc1, room_no).split())
    tokens2 = set(normalize_issue_text(desc2, room_no).split())
    
    ignore_words = {"not", "work", "break", "stop", "stopped", "fix", "repair", "issue", "problem", "fault", "faulty", "bad", "damage", "damaged"}
    
    meaningful1 = tokens1 - ignore_words
    meaningful2 = tokens2 - ignore_words
    
    if meaningful1 and meaningful2:
        return len(meaningful1 & meaningful2) > 0
        
    if not tokens1 or not tokens2:
        return True
        
    return len(tokens1 & tokens2) > 0


def find_active_duplicate_complaint(
    student_id,
    category,
    description,
    block="",
    floor_no="",
    room_no="",
    location="",
    bus_number="",
    route="",
    transport_type="",
    conn=None
):
    """
    Checks if the same student already has an active complaint for:
    1. Same student / registered account
    2. Same complaint category
    3. Same block / building
    4. Same room / location
    5. Same/similar issue description
    6. Existing complaint is still active (NEW, PENDING, IN_PROGRESS, REOPENED, FORWARDED)

    Returns the matching active complaint dict, or None if no active duplicate exists.
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    try:
        sub_loc_key = get_canonical_location_key(
            category=category,
            block=block,
            floor_no=floor_no,
            room_no=room_no,
            location=location,
            bus_number=bus_number,
            route=route,
            transport_type=transport_type
        )

        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*
            FROM complaints c
            WHERE (c.student_id = ? OR c.complaint_id IN (SELECT complaint_id FROM complaint_reporters WHERE student_id = ?))
              AND LOWER(c.category) = LOWER(?)
              AND c.status IN ('NEW', 'PENDING', 'IN_PROGRESS', 'REOPENED', 'FORWARDED')
            ORDER BY c.complaint_id DESC
        """, (student_id, student_id, (category or "").strip()))

        active_candidates = cursor.fetchall()
        for cand in active_candidates:
            cand_loc_key = get_canonical_location_key(
                category=cand["category"],
                block=cand["block"],
                floor_no=cand["floor_no"],
                room_no=cand["room_no"],
                location=cand["location"],
                bus_number=cand["bus_number"],
                route=cand["route"],
                transport_type=cand["transport_type"]
            )
            if cand_loc_key == sub_loc_key:
                if is_similar_issue(description, cand["description"], room_no):
                    return dict(cand)

        return None
    finally:
        if should_close:
            conn.close()


def compute_complaint_fingerprint(
    category,
    description,
    block="",
    floor_no="",
    room_no="",
    corridor_side="",
    nearby_area="",
    additional_location="",
    location="",
    transport_type="",
    bus_number="",
    route="",
    pickup_drop_point="",
    transport_complaint_type=""
):
    """
    Generates a deterministic complaint fingerprint string based on normalized:
    - category
    - location / room / bus route
    - meaningful issue description tokens
    """
    cat_norm = (category or "").strip().lower()
    loc_key = normalize_location_key(
        category=category,
        block=block,
        floor_no=floor_no,
        room_no=room_no,
        corridor_side=corridor_side,
        nearby_area=nearby_area,
        additional_location=additional_location,
        location=location,
        transport_type=transport_type,
        bus_number=bus_number,
        route=route,
        pickup_drop_point=pickup_drop_point,
        transport_complaint_type=transport_complaint_type
    )
    issue_tokens = normalize_issue_text(description, room_no=room_no)
    return f"{cat_norm}::{loc_key}::{issue_tokens}"


def migrate_database(conn):
    """Safely adds new complaint columns, indexes, audit history, notes, and reporters tables without deleting existing data."""
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
        ("transport_complaint_type", "TEXT DEFAULT ''"),
        ("department", "TEXT DEFAULT ''"),
        ("complaint_fingerprint", "TEXT DEFAULT ''"),
        ("affected_student_count", "INTEGER DEFAULT 1")
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

    # 2.1 Create Complaint Reporters Table (Grouped complaints mapping)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaint_reporters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            student_email TEXT DEFAULT '',
            reported_at TEXT NOT NULL,
            UNIQUE(complaint_id, student_id),
            FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id),
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    # 2.2 Create Active Complaint Slots Table (Database-level duplicate lock protection)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_complaint_slots (
            slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_key TEXT UNIQUE NOT NULL,
            complaint_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_active_slots_complaint ON active_complaint_slots(complaint_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_active_slots_student ON active_complaint_slots(student_id)")

    # 2.3 Backfill active_complaint_slots from active complaints
    cursor.execute("""
        SELECT complaint_id, student_id, complaint_fingerprint, date
        FROM complaints
        WHERE status IN ('NEW', 'PENDING', 'IN_PROGRESS', 'REOPENED', 'FORWARDED')
    """)
    for r in cursor.fetchall():
        s_key = f"{r['student_id']}::{r['complaint_fingerprint']}"
        cursor.execute("""
            INSERT OR IGNORE INTO active_complaint_slots (slot_key, complaint_id, student_id, created_at)
            VALUES (?, ?, ?, ?)
        """, (s_key, r["complaint_id"], r["student_id"], r["date"] or ""))

    # 2.5 Migrate legacy status strings
    status_mapping = {
        'Pending': 'NEW',
        'In Progress': 'IN_PROGRESS',
        'Resolved': 'FINAL_RESOLVED',
        'REGENERATED': 'REOPENED',
        'RESOLVED_BY_DEPARTMENT': 'RESOLUTION_SUBMITTED'
    }
    for old_status, new_status in status_mapping.items():
        cursor.execute("UPDATE complaints SET status = ? WHERE status = ?", (new_status, old_status))
        cursor.execute("UPDATE complaint_status_history SET new_status = ? WHERE new_status = ?", (new_status, old_status))
        cursor.execute("UPDATE complaint_status_history SET old_status = ? WHERE old_status = ?", (new_status, old_status))

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
        if not first_resp and r["status"] in ("IN_PROGRESS", "FINAL_RESOLVED", "RESOLUTION_SUBMITTED"):
            first_resp = r["last_updated"] or r["date"]
        if first_resp:
            cursor.execute("UPDATE complaints SET first_responded_at = ? WHERE complaint_id = ?", (first_resp, r["complaint_id"]))

    # 4. Backfill complaint_fingerprint and complaint_reporters for legacy data
    cursor.execute("""
        SELECT c.complaint_id, c.student_id, c.category, c.description, c.block, c.floor_no,
               c.room_no, c.corridor_side, c.nearby_area, c.additional_location, c.location,
               c.date, c.last_updated, c.complaint_fingerprint, c.affected_student_count,
               c.transport_type, c.bus_number, c.route, c.pickup_drop_point, c.transport_complaint_type,
               s.email AS student_email
        FROM complaints c
        LEFT JOIN students s ON c.student_id = s.student_id
    """)
    existing_complaints = cursor.fetchall()
    for row in existing_complaints:
        cid = row["complaint_id"]
        sid = row["student_id"]
        semail = row["student_email"] or ""
        r_at = row["last_updated"] or row["date"] or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate fingerprint if missing
        fp = row["complaint_fingerprint"]
        if not fp:
            fp = compute_complaint_fingerprint(
                category=row["category"],
                description=row["description"],
                block=row["block"],
                floor_no=row["floor_no"],
                room_no=row["room_no"],
                corridor_side=row["corridor_side"],
                nearby_area=row["nearby_area"],
                additional_location=row["additional_location"],
                location=row["location"],
                transport_type=row["transport_type"],
                bus_number=row["bus_number"],
                route=row["route"],
                pickup_drop_point=row["pickup_drop_point"],
                transport_complaint_type=row["transport_complaint_type"]
            )
            cursor.execute("UPDATE complaints SET complaint_fingerprint = ? WHERE complaint_id = ?", (fp, cid))

        # Ensure original submitter is registered in complaint_reporters
        if sid:
            cursor.execute("""
                INSERT OR IGNORE INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
                VALUES (?, ?, ?, ?)
            """, (cid, sid, semail, r_at))

    # Synchronize affected_student_count from complaint_reporters
    cursor.execute("""
        UPDATE complaints
        SET affected_student_count = (
            SELECT MAX(1, COUNT(*)) FROM complaint_reporters WHERE complaint_reporters.complaint_id = complaints.complaint_id
        )
    """)

    # 5. Create Performance Database Indexes
    indexes_to_create = [
        ("idx_complaints_student", "CREATE INDEX IF NOT EXISTS idx_complaints_student ON complaints(student_id)"),
        ("idx_complaints_status", "CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status)"),
        ("idx_complaints_priority", "CREATE INDEX IF NOT EXISTS idx_complaints_priority ON complaints(priority)"),
        ("idx_complaints_ticket_id", "CREATE INDEX IF NOT EXISTS idx_complaints_ticket_id ON complaints(ticket_id)"),
        ("idx_history_complaint", "CREATE INDEX IF NOT EXISTS idx_history_complaint ON complaint_status_history(complaint_id)"),
        ("idx_notes_complaint", "CREATE INDEX IF NOT EXISTS idx_notes_complaint ON admin_notes(complaint_id)"),
        ("idx_reporters_complaint", "CREATE INDEX IF NOT EXISTS idx_reporters_complaint ON complaint_reporters(complaint_id)"),
        ("idx_reporters_student", "CREATE INDEX IF NOT EXISTS idx_reporters_student ON complaint_reporters(student_id)"),
        ("idx_complaints_fingerprint", "CREATE INDEX IF NOT EXISTS idx_complaints_fingerprint ON complaints(complaint_fingerprint)")
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

    # 7. Ensure admins table has role and department columns
    cursor.execute("PRAGMA table_info(admins)")
    admin_cols = {row["name"] for row in cursor.fetchall()}
    if "role" not in admin_cols:
        cursor.execute("ALTER TABLE admins ADD COLUMN role TEXT DEFAULT 'Super Admin'")
    if "department" not in admin_cols:
        cursor.execute("ALTER TABLE admins ADD COLUMN department TEXT DEFAULT ''")

    # 8. Backfill empty complaint departments based on category
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
    for cat, dept in category_dept_map.items():
        cursor.execute(
            "UPDATE complaints SET department = ? WHERE category = ? AND (department = '' OR department IS NULL)",
            (dept, cat)
        )

    # 9. Seed/Update Department Admin Accounts
    department_accounts = [
        ("admin", "admin123", "Super Admin", ""),
        ("electrical_admin", "electrical123", "HOD", "Electrical"),
        ("electrical", "electrical123", "HOD", "Electrical"),
        ("cleaning_admin", "cleaning123", "HOD", "Cleaning"),
        ("cleaning", "cleaning123", "HOD", "Cleaning"),
        ("classroom_admin", "classroom123", "HOD", "Classroom"),
        ("classroom", "classroom123", "HOD", "Classroom"),
        ("hostel_admin", "hostel123", "HOD", "Hostel"),
        ("hostel", "hostel123", "HOD", "Hostel"),
        ("wifi_admin", "wifi123", "HOD", "Wi-Fi/Internet"),
        ("wifi", "wifi123", "HOD", "Wi-Fi/Internet"),
        ("library_admin", "library123", "HOD", "Library"),
        ("library", "library123", "HOD", "Library"),
        ("infra_admin", "infra123", "HOD", "Infrastructure"),
        ("infra", "infra123", "HOD", "Infrastructure"),
        ("transport_admin", "transport123", "HOD", "Transport"),
        ("transport", "transport123", "HOD", "Transport"),
        ("other_admin", "other123", "HOD", "Other"),
        ("other", "other123", "HOD", "Other"),
    ]
    for uname, pword, urole, udept in department_accounts:
        cursor.execute("SELECT admin_id, password, role, department FROM admins WHERE LOWER(username) = LOWER(?)", (uname,))
        existing_acc = cursor.fetchone()
        if not existing_acc:
            cursor.execute(
                "INSERT INTO admins (username, password, role, department) VALUES (?, ?, ?, ?)",
                (uname, generate_password_hash(pword), urole, udept)
            )
            print(f"[CampusCare DB] Created department admin account: {uname} ({udept})")
        else:
            # Keep role and department synced
            cursor.execute(
                "UPDATE admins SET role = ?, department = ? WHERE admin_id = ?",
                (urole, udept, existing_acc["admin_id"])
            )

    conn.commit()


def create_database():
    """Initializes SQLite database tables, runs safe migrations, and sets default admin account."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("BEGIN EXCLUSIVE")

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
    student_where = """
        complaint_id IN (
            SELECT complaint_id FROM complaint_reporters WHERE student_id = ?
            UNION
            SELECT complaint_id FROM complaints WHERE student_id = ?
        )
    """
    total = conn.execute(f"SELECT COUNT(*) FROM complaints WHERE {student_where}", (student_id, student_id)).fetchone()[0]
    pending = conn.execute(f"SELECT COUNT(*) FROM complaints WHERE ({student_where}) AND status IN ('NEW', 'FORWARDED')", (student_id, student_id)).fetchone()[0]
    in_progress = conn.execute(f"SELECT COUNT(*) FROM complaints WHERE ({student_where}) AND status IN ('IN_PROGRESS', 'REOPENED')", (student_id, student_id)).fetchone()[0]
    awaiting = conn.execute(f"SELECT COUNT(*) FROM complaints WHERE ({student_where}) AND status IN ('RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION')", (student_id, student_id)).fetchone()[0]
    regenerated = conn.execute(f"SELECT COUNT(*) FROM complaints WHERE ({student_where}) AND status = 'REOPENED'", (student_id, student_id)).fetchone()[0]
    resolved = conn.execute(f"SELECT COUNT(*) FROM complaints WHERE ({student_where}) AND status = 'FINAL_RESOLVED'", (student_id, student_id)).fetchone()[0]
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
    where = "WHERE (is_primary = 1 OR group_id IS NULL)"
    if department:
        where += " AND department = ?"
        params = (department,)
    else:
        params = ()

    # 1. Unique Grievances (Total Master Complaints)
    total = conn.execute(f"SELECT COUNT(*) FROM complaints {where}", params).fetchone()[0]

    # 2 & 3. Student Reports and Students Affected
    # Only count reporters that belong to a valid active master complaint
    # (to prevent double counting if an old/merged record still has reporters)
    if department:
        total_reports = conn.execute(f"""
            SELECT COUNT(*) FROM complaint_reporters cr
            JOIN complaints c ON cr.complaint_id = c.complaint_id
            {where}
        """, params).fetchone()[0]
        students_affected = conn.execute(f"""
            SELECT COUNT(DISTINCT cr.student_id) FROM complaint_reporters cr
            JOIN complaints c ON cr.complaint_id = c.complaint_id
            {where}
        """, params).fetchone()[0]
    else:
        total_reports = conn.execute(f"""
            SELECT COUNT(*) FROM complaint_reporters cr
            JOIN complaints c ON cr.complaint_id = c.complaint_id
            {where}
        """, params).fetchone()[0]
        students_affected = conn.execute(f"""
            SELECT COUNT(DISTINCT cr.student_id) FROM complaint_reporters cr
            JOIN complaints c ON cr.complaint_id = c.complaint_id
            {where}
        """, params).fetchone()[0]

    # Ensure reports/affected are at least equal to master complaints count
    total_reports = max(total_reports, total)
    students_affected = max(students_affected, total)
    
    # 4. Pending Action
    # The application uses NEW, FORWARDED, RESOLUTION_SUBMITTED, AWAITING_STUDENT_CONFIRMATION for Pending Action
    # Let's count them according to the rules defined previously.
    where_pending = f"{where} AND status IN ('NEW', 'FORWARDED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION')"
    pending = conn.execute(f"SELECT COUNT(*) FROM complaints {where_pending}", params).fetchone()[0]
    
    where_in_progress = f"{where} AND status IN ('IN_PROGRESS', 'REOPENED')"
    in_progress = conn.execute(f"SELECT COUNT(*) FROM complaints {where_in_progress}", params).fetchone()[0]
    
    where_resolved = f"{where} AND status = 'FINAL_RESOLVED'"
    resolved = conn.execute(f"SELECT COUNT(*) FROM complaints {where_resolved}", params).fetchone()[0]

    # Count escalated items (High Priority + status != 'FINAL_RESOLVED' older than 48 hours)
    from datetime import datetime, timedelta
    threshold_dt = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
    threshold_date = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d")

    where_escalated = f"{where} AND priority = 'High' AND status != 'FINAL_RESOLVED' AND (date < ? OR (last_updated != '' AND last_updated < ?))"
    params_escalated = params + (threshold_date, threshold_dt)
    escalated = conn.execute(f"SELECT COUNT(*) FROM complaints {where_escalated}", params_escalated).fetchone()[0]

    conn.close()
    return {
        "total": total,
        "unique_complaints": total,
        "total_reports": total_reports,
        "students_affected": students_affected,
        "pending": pending,
        "new": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "final_resolved": resolved,
        "escalated": escalated
    }

def get_transport_statistics():
    """Aggregates real-time statistics for transport complaints directly from the database."""
    conn = get_db_connection()
    
    total = conn.execute("SELECT COUNT(*) FROM complaints WHERE category = 'Transport Complaint'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE category = 'Transport Complaint' AND status IN ('NEW', 'FORWARDED')").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE category = 'Transport Complaint' AND status IN ('IN_PROGRESS', 'REOPENED')").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE category = 'Transport Complaint' AND status IN ('FINAL_RESOLVED', 'RESOLUTION_SUBMITTED')").fetchone()[0]
    
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
    in_progress = conn.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('IN_PROGRESS', 'REOPENED')").fetchone()[0]
    awaiting = conn.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION')").fetchone()[0]
    open_comp = conn.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('NEW', 'FORWARDED', 'REOPENED')").fetchone()[0]
    regenerated = conn.execute("SELECT COUNT(*) FROM complaints WHERE status = 'REOPENED'").fetchone()[0]
    
    total_reports = conn.execute("SELECT COUNT(*) FROM complaint_reporters").fetchone()[0]
    students_affected = conn.execute("SELECT COUNT(DISTINCT student_id) FROM complaint_reporters").fetchone()[0]
    total_reports = max(total_reports, total)
    students_affected = max(students_affected, total)

    # Department activity
    dept_rows = conn.execute("SELECT department, COUNT(*) as c FROM complaints GROUP BY department").fetchall()
    department_activity = {row['department'] or 'Unassigned': row['c'] for row in dept_rows}

    conn.close()

    resolution_rate = int((resolved / total * 100)) if total > 0 else 0

    return {
        "total_complaints": total,
        "unique_complaints": total,
        "total_reports": total_reports,
        "students_affected": students_affected,
        "resolved_complaints": resolved,
        "active_students": students,
        "resolution_rate": resolution_rate,
        "in_progress": in_progress,
        "awaiting": awaiting,
        "open_complaints": open_comp,
        "regenerated": regenerated,
        "department_activity": department_activity
    }


def get_complaint_reporters(complaint_id):
    """
    Retrieves all students who reported or are associated with this master complaint.
    Returns list of dicts with student details and reported timestamp.
    """
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT 
            cr.id,
            cr.complaint_id,
            cr.student_id,
            cr.student_email,
            cr.reported_at,
            s.name AS student_name,
            COALESCE(NULLIF(cr.student_email, ''), s.email, '') AS email
        FROM complaint_reporters cr
        LEFT JOIN students s ON cr.student_id = s.student_id
        WHERE cr.complaint_id = ?
        ORDER BY cr.id ASC
    """, (complaint_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def is_student_associated_with_complaint(complaint_id, student_id):
    """Checks whether the student is the creator or an attached reporter of the complaint."""
    if not complaint_id or not student_id:
        return False
    conn = get_db_connection()
    row = conn.execute("""
        SELECT 1 FROM complaints WHERE complaint_id = ? AND student_id = ?
        UNION
        SELECT 1 FROM complaint_reporters WHERE complaint_id = ? AND student_id = ?
    """, (complaint_id, student_id, complaint_id, student_id)).fetchone()
    conn.close()
    return row is not None


def submit_or_attach_complaint(
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
    import time
    from datetime import datetime, date
    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not date_str:
        date_str = str(date.today())

    # Room/Floor Inconsistency Validation
    if room_no and floor_no:
        canon_room = extract_canonical_room(room_no)
        if canon_room and canon_room[0].isdigit():
            implied_floor = None
            first_digit = canon_room[0]
            if first_digit == '0': implied_floor = 'ground'
            elif first_digit == '1': implied_floor = '1st'
            elif first_digit == '2': implied_floor = '2nd'
            elif first_digit == '3': implied_floor = '3rd'
            elif first_digit == '4': implied_floor = '4th'
            elif first_digit == '5': implied_floor = '5th'
            
            if implied_floor and implied_floor not in floor_no.lower():
                return {
                    "status": "VALIDATION_FAILED",
                    "message": f"Inconsistent location: Room {room_no} appears to be on the {implied_floor} floor, but you selected '{floor_no}'. Please correct the location."
                }


    # STEP 1 & 2: Normalize and generate ONE deterministic fingerprint
    fingerprint = compute_complaint_fingerprint(
        category=category,
        description=description,
        block=block,
        floor_no=floor_no,
        room_no=room_no,
        corridor_side=corridor_side,
        nearby_area=nearby_area,
        additional_location=additional_location,
        location=location,
        transport_type=transport_type,
        bus_number=bus_number,
        route=route,
        pickup_drop_point=pickup_drop_point,
        transport_complaint_type=transport_complaint_type
    )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("BEGIN EXCLUSIVE")

    # STEP 4: Server Console Logging
    student_row = cursor.execute("SELECT email, name FROM students WHERE student_id = ?", (student_id,)).fetchone()
    student_email = student_row["email"] if student_row else ""
    print(f"\n--- SUBMISSION DEBUG ---")
    print(f"student_id = {student_id}")
    print(f"email = {student_email}")
    print(f"fingerprint = {fingerprint}")

    # STEP 3: Search for existing ACTIVE master complaint with that exact fingerprint
    master = cursor.execute("""
        SELECT * FROM complaints 
        WHERE complaint_fingerprint = ? 
          AND status != 'FINAL_RESOLVED' 
        ORDER BY complaint_id DESC LIMIT 1
    """, (fingerprint,)).fetchone()
    
    if master:
        master_id = master["complaint_id"]
        master_ticket = master["ticket_id"] or format_ticket_id(master_id, master["date"])
        print(f"existing_master_complaint_id = {master_id}")
        
        # Check complaint_reporters for current student
        is_reporter = cursor.execute(
            "SELECT 1 FROM complaint_reporters WHERE complaint_id = ? AND student_id = ?",
            (master_id, student_id)
        ).fetchone()
        
        if is_reporter:
            print("existing_reporter = True")
            print("ACTION = REJECT_DUPLICATE")
            conn.rollback()
            conn.close()
            return {
                "status": "DUPLICATE_REJECTED",
                "complaint_id": master_id,
                "ticket_id": master_ticket,
                "affected_student_count": master["affected_student_count"],
                "current_status": master["status"],
                "category": master["category"],
                "location": (master["block"] or "") + (f", Room {master['room_no']}" if master["room_no"] else ""),
                "message": f"Duplicate Complaint Detected. You already have an active complaint ({master_ticket}) for this issue. You have already reported this issue at this location. Please track your existing complaint instead of submitting the same issue again."
            }
        else:
            print("existing_reporter = False")
            print("ACTION = ADD_REPORTER_AND_CREATE_TICKET")
            # Create the non-primary complaint record
            cursor.execute("""
                INSERT INTO complaints (
                    student_id, category, description, photo_path, block, floor_no, room_no,
                    corridor_side, nearby_area, additional_location, priority,
                    transport_type, bus_number, route, pickup_drop_point, transport_complaint_type,
                    department, status, date, location, complaint_fingerprint,
                    affected_student_count, is_primary, group_id, regeneration_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?, ?, ?, 0, ?, 0)
            """, (
                student_id, category, description, photo_path, block, floor_no, room_no,
                corridor_side, nearby_area, additional_location, priority,
                transport_type, bus_number, route, pickup_drop_point, transport_complaint_type,
                master["department"], date_str, master["location"], fingerprint,
                1, master_id
            ))
            
            new_complaint_id = cursor.lastrowid
            new_ticket_id = format_ticket_id(new_complaint_id, date_str)
            
            cursor.execute("UPDATE complaints SET ticket_id = ? WHERE complaint_id = ?", (new_ticket_id, new_complaint_id))
            
            # Insert into complaint_reporters for BOTH master and new complaint
            cursor.execute("""
                INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
                VALUES (?, ?, ?, ?)
            """, (master_id, student_id, student_email, now_timestamp))
            
            cursor.execute("""
                INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
                VALUES (?, ?, ?, ?)
            """, (new_complaint_id, student_id, student_email, now_timestamp))
            
            # Update affected_student_count on master
            cursor.execute("""
                UPDATE complaints 
                SET affected_student_count = affected_student_count + 1 
                WHERE complaint_id = ?
            """, (master_id,))
            
            conn.commit()
            return {
                "status": "ATTACHED_TO_MASTER",
                "complaint_id": new_complaint_id,
                "ticket_id": new_ticket_id,
                "affected_student_count": master["affected_student_count"] + 1,
                "current_status": master["status"],
                "category": category,
                "location": location,
                "message": f"Your complaint has been registered. You have been grouped with an existing active issue. Your Ticket ID is {new_ticket_id}."
            }
            
            # Fetch updated count
            new_count = cursor.execute("SELECT affected_student_count FROM complaints WHERE complaint_id = ?", (master_id,)).fetchone()[0]
            conn.close()
            
            return {
                "status": "ATTACHED_TO_MASTER",
                "complaint_id": master_id,
                "ticket_id": master_ticket,
                "affected_student_count": new_count,
                "message": f"Your complaint has been successfully attached to an existing issue report. Ticket ID: {master_ticket}"
            }

    # STEP 5: ONLY when no matching master complaint exists
    print("existing_master_complaint_id = None")
    print("existing_reporter = False")
    print("ACTION = CREATE_MASTER")
    
    # Assign department (basic assignment logic based on category)
    department = "General"
    if category == "Electrical":
        department = "Electrical"
    elif category == "Cleaning":
        department = "Cleaning"
    elif category == "Plumbing":
        department = "Plumbing"
    elif category == "IT / Network":
        department = "IT Support"
    elif category == "Transport Complaint":
        department = "Transport"

    cursor.execute("""
        INSERT INTO complaints
        (student_id, ticket_id, category, description, photo_path, block, floor_no, room_no,
         corridor_side, nearby_area, additional_location, location, priority, status, date, last_updated,
         transport_type, bus_number, route, pickup_drop_point, transport_complaint_type, department,
         complaint_fingerprint, affected_student_count, group_id, is_primary)
        VALUES (?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NEW', ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, NULL, 1)
    """, (
        student_id, category, description, photo_path or "", block or "", floor_no or "", room_no or "",
        corridor_side or "", nearby_area or "", additional_location or "", location or "", priority, date_str,
        now_timestamp, transport_type or "", bus_number or "", route or "", pickup_drop_point or "",
        transport_complaint_type or "", department, fingerprint
    ))
    
    complaint_id = cursor.lastrowid
    ticket_id = format_ticket_id(complaint_id, date_str)
    
    cursor.execute("UPDATE complaints SET ticket_id = ?, group_id = ? WHERE complaint_id = ?", (ticket_id, complaint_id, complaint_id))
    
    cursor.execute("""
        INSERT INTO complaint_reporters (complaint_id, student_id, student_email, reported_at)
        VALUES (?, ?, ?, ?)
    """, (complaint_id, student_id, student_email, now_timestamp))
    
    cursor.execute("""
        INSERT INTO complaint_status_history
        (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at)
        VALUES (?, NULL, 'Student (Submission)', NULL, 'NEW', 'Grievance ticket created and lodged for administration review.', ?)
    """, (complaint_id, now_timestamp))
    
    conn.commit()
    conn.close()
    
    return {
        "status": "CREATED_NEW",
        "complaint_id": complaint_id,
        "ticket_id": ticket_id,
        "affected_student_count": 1,
        "message": f"Grievance ticket {ticket_id} submitted successfully."
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
    Backward-compatible complaint creation helper. Calls submit_or_attach_complaint
    and returns (complaint_id, ticket_id).
    """
    res = submit_or_attach_complaint(
        student_id=student_id,
        category=category,
        description=description,
        photo_path=photo_path,
        block=block,
        floor_no=floor_no,
        room_no=room_no,
        corridor_side=corridor_side,
        nearby_area=nearby_area,
        additional_location=additional_location,
        priority=priority,
        date_str=date_str,
        location=location,
        transport_type=transport_type,
        bus_number=bus_number,
        route=route,
        pickup_drop_point=pickup_drop_point,
        transport_complaint_type=transport_complaint_type
    )
    return res["complaint_id"], res["ticket_id"]


def add_status_history(complaint_id, admin_id, admin_name, old_status, new_status, remarks=""):
    """Inserts a new entry in the complaint status history audit trail."""
    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("BEGIN EXCLUSIVE")
    cursor.execute("""
        INSERT INTO complaint_status_history
        (complaint_id, admin_id, admin_name, old_status, new_status, remarks, changed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (complaint_id, admin_id, admin_name or "Administrator", old_status, new_status, remarks or "", now_timestamp))
    
    # Update last_updated and first_responded_at if administrative action
    if admin_name != "Student (Submission)" or admin_id is not None or new_status in ("IN_PROGRESS", "FINAL_RESOLVED", "RESOLUTION_SUBMITTED"):
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
    cursor.execute("BEGIN EXCLUSIVE")
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


def get_all_complaints():
    """Returns all complaint records directly from database for reporting and audit verification."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM complaints ORDER BY complaint_id DESC").fetchall()
    conn.close()
    return rows


def get_student_complaints_paginated(student_id, status_filter="All", search_query=None, page=1, per_page=10):
    """Returns paginated complaints for a student with search & filter support, showing each master complaint once."""
    conn = get_db_connection()
    base_where = "WHERE (complaints.complaint_id IN (SELECT complaint_id FROM complaint_reporters WHERE student_id = ?) OR complaints.student_id = ?)"
    params = [student_id, student_id]

    if status_filter and status_filter != "All":
        base_where += " AND complaints.status = ?"
        params.append(status_filter)

    if search_query and search_query.strip():
        s = f"%{search_query.strip()}%"
        base_where += """ AND (
            complaints.ticket_id LIKE ? OR complaints.category LIKE ? OR complaints.description LIKE ? OR complaints.location LIKE ?
            OR complaints.block LIKE ? OR complaints.room_no LIKE ? OR complaints.nearby_area LIKE ?
            OR CAST(complaints.complaint_id AS TEXT) LIKE ?
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
            complaints.complaint_id, complaints.ticket_id, complaints.student_id, complaints.category,
            complaints.description, complaints.photo_path, complaints.block, complaints.floor_no,
            complaints.room_no, complaints.corridor_side, complaints.nearby_area,
            complaints.additional_location, complaints.location, complaints.priority,
            complaints.status, complaints.date, complaints.last_updated,
            COALESCE(complaints.affected_student_count, 1) AS affected_student_count
        FROM complaints
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
    complaints_raw = conn.execute(query_sql, query_params).fetchall()
    conn.close()

    items = []
    for r in complaints_raw:
        c = dict(r)
        related = get_related_complaints(c['complaint_id'])
        if related:
            c['affected_student_count'] = related['affected_student_count']
            c['related_complaints_data'] = related
        else:
            c['affected_student_count'] = 1
            c['related_complaints_data'] = None
        items.append(c)

    return {
        "items": items,
        "total": total_count,
        "total_items": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    }

def get_complaint_collections():
    conn = get_db_connection()
    # Fetch all master complaints
    query_sql = """
        SELECT
            complaints.*,
            students.name AS student_name,
            students.email AS student_email
        FROM complaints
        JOIN students ON complaints.student_id = students.student_id
        WHERE complaints.is_primary = 1 OR complaints.group_id IS NULL
        ORDER BY complaints.complaint_id DESC
    """
    complaints_raw = conn.execute(query_sql).fetchall()
    
    collections = []
    
    summary = {
        'total_issues': 0,
        'affected_students': 0,
        'open_issues': 0,
        'in_progress': 0,
        'resolved': 0
    }
    
    for row in complaints_raw:
        c = dict(row)
        c['ticket_id'] = c.get('ticket_id') or format_ticket_id(c['complaint_id'], c['date'])
        
        # In the new paradigm, each collection is just a 1-to-1 mapping with a master complaint.
        reporters = conn.execute(
            "SELECT student_id, student_email, reported_at FROM complaint_reporters WHERE complaint_id = ?",
            (c['complaint_id'],)
        ).fetchall()
        
        is_transport = c.get('category') == 'Transport Complaint'
        location_str = f"{c.get('block', '')} • {c.get('floor_no', '')} • {c.get('room_no', '')}" if not is_transport else f"Bus {c.get('bus_number', '')} • Route {c.get('route', '')}"
        
        status_counts = {'NEW': 0, 'IN_PROGRESS': 0, 'RESOLVED': 0}
        s = c['status']
        # The user requested mapping:
        # NEW, FORWARDED, RESOLUTION_SUBMITTED, AWAITING_STUDENT_CONFIRMATION -> Pending (NEW)
        # IN_PROGRESS, REOPENED -> In Progress
        # FINAL_RESOLVED -> Resolved
        if s in ('NEW', 'FORWARDED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION'):
            status_counts['NEW'] = 1
            summary['open_issues'] += 1
        elif s in ('IN_PROGRESS', 'REOPENED'):
            status_counts['IN_PROGRESS'] = 1
            summary['in_progress'] += 1
        elif s == 'FINAL_RESOLVED':
            status_counts['RESOLVED'] = 1
            summary['resolved'] += 1
            
        student_count = c.get('affected_student_count', 1)
        summary['affected_students'] += student_count
        summary['total_issues'] += 1
        
        # Build pseudo-complaints for the UI modal so it can display the list of reporters
        pseudo_complaints = []
        for r in reporters:
            pc = dict(c) # copy master
            pc['student_id'] = r['student_id']
            pc['student_email'] = r['student_email']
            # Try to get the student's name
            student_row = conn.execute("SELECT name FROM students WHERE student_id = ?", (r['student_id'],)).fetchone()
            if student_row:
                pc['student_name'] = student_row['name']
            pseudo_complaints.append(pc)
            
        if not pseudo_complaints:
            pseudo_complaints = [c] # Failsafe
            
        col = {
            'collection_id': f"COL-{c['complaint_id']:04d}",
            'issue': c.get('description', ''),
            'representative_description': c.get('description', ''),
            'category': c.get('category', ''),
            'location': location_str,
            'block': c.get('block', ''),
            'floor_no': c.get('floor_no', ''),
            'room_no': c.get('room_no', ''),
            'bus_number': c.get('bus_number', ''),
            'route': c.get('route', ''),
            'pickup_drop_point': c.get('pickup_drop_point', ''),
            'priority': c.get('priority', 'Low'),
            'student_count': student_count,
            'report_count': student_count,
            'complaints': pseudo_complaints,
            'status_counts': status_counts,
            'status': c['status'] # Important: direct master status!
        }
        collections.append(col)
        
    conn.close()
    return collections, summary

def get_complaint_by_id(complaint_id):
    """Fetches a single complaint record by numeric ID or Ticket ID string."""
    conn = get_db_connection()
    query = """
        SELECT
            complaints.*,
            COALESCE(complaints.affected_student_count, 1) AS affected_student_count,
            students.name AS student_name,
            students.email AS student_email
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

    # Synchronize active_complaint_slots: release if resolved/closed, acquire if reopened/active
    if new_status in ("FINAL_RESOLVED", "RESOLUTION_SUBMITTED", "RESOLVED"):
        cursor.execute("DELETE FROM active_complaint_slots WHERE complaint_id = ?", (complaint_id,))
    elif new_status in ("REOPENED", "IN_PROGRESS", "NEW", "PENDING", "FORWARDED"):
        comp_row = cursor.execute("SELECT student_id, complaint_fingerprint FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
        if comp_row:
            s_key = f"{comp_row['student_id']}::{comp_row['complaint_fingerprint']}"
            cursor.execute("INSERT OR IGNORE INTO active_complaint_slots (slot_key, complaint_id, student_id, created_at) VALUES (?, ?, ?, ?)", (s_key, complaint_id, comp_row["student_id"], now_timestamp))

    conn.commit()
    conn.close()
    return True, f"Complaint status updated to {new_status}." 


def get_analytics_data(department=None):
    """
    Aggregates statistical insights for the admin dashboard:
    Category breakdown, Priority breakdown, Status distribution, and 6-Month trends.
    Optionally scoped to a specific department.
    """
    conn = get_db_connection()
    where = "WHERE (is_primary = 1 OR group_id IS NULL)"
    if department:
        where += " AND department = ?"
        params = (department,)
    else:
        params = ()

    # 1. By Category
    cat_rows = conn.execute(f"SELECT category, COUNT(*) as count FROM complaints {where} GROUP BY category ORDER BY count DESC", params).fetchall()
    by_category = {row["category"]: row["count"] for row in cat_rows}
    categories_list = [{"category": row["category"], "count": row["count"]} for row in cat_rows]

    # 2. By Priority
    prio_rows = conn.execute(f"SELECT priority, COUNT(*) as count FROM complaints {where} GROUP BY priority", params).fetchall()
    by_priority = {"Low": 0, "Medium": 0, "High": 0}
    for row in prio_rows:
        by_priority[row["priority"]] = row["count"]
    priorities_list = [{"priority": p, "count": by_priority[p]} for p in ["High", "Medium", "Low"]]

    # 3. By Status
    status_rows = conn.execute(f"SELECT status, COUNT(*) as count FROM complaints {where} GROUP BY status", params).fetchall()
    by_status = {"Pending": 0, "In Progress": 0, "Resolved": 0}
    for row in status_rows:
        s = row["status"]
        if s in ("NEW", "FORWARDED", "RESOLUTION_SUBMITTED", "AWAITING_STUDENT_CONFIRMATION"):
            by_status["Pending"] += row["count"]
        elif s in ("IN_PROGRESS", "REOPENED"):
            by_status["In Progress"] += row["count"]
        elif s == "FINAL_RESOLVED":
            by_status["Resolved"] += row["count"]
    statuses_list = [{"status": s, "count": by_status[s]} for s in ["Pending", "In Progress", "Resolved"]]

    # 4. Monthly Trend (Past 6 Months)
    monthly_trend = []
    from datetime import datetime, timedelta
    now = datetime.now()
    for i in range(5, -1, -1):
        m_date = now - timedelta(days=i * 30)
        m_str = m_date.strftime("%Y-%m")
        m_label = m_date.strftime("%b %Y")
        m_count = conn.execute(f"SELECT COUNT(*) FROM complaints {where} AND date LIKE ?", params + (f"{m_str}%",)).fetchone()[0]
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


def get_all_complaints_for_report(status_filter="All", priority_filter="All", search_text="", department=None):
    """
    Fetches all matching complaint records with student details for PDF report generation without pagination limits.
    """
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


def get_campus_heatmap_data(department=None):
    """
    Aggregates real-time complaint data mapped to specific campus zones for the interactive problem heatmap.
    Computes intensity ratings (Low, Moderate, High, Critical) based on active volume and safety priority,
    and returns genuine database-driven complaint records for each zone.
    Optionally scoped to a specific department.
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
    
    where = "WHERE c.department = ?" if department else ""
    params = (department,) if department else ()
    query = f"""
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
        {where}
        ORDER BY c.complaint_id DESC
    """
    rows = conn.execute(query, params).fetchall()
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
        
        status = r["status"] or "NEW"
        priority = r["priority"] or "Low"
        cat = r["category"] or "General"
        
        category_counter[matched_zone][cat] = category_counter[matched_zone].get(cat, 0) + 1
        
        if status in ("NEW", "FORWARDED"):
            z_data["pending"] += 1
            z_data["active"] += 1
            z_data["unresolved_count"] += 1
        elif status in ("IN_PROGRESS", "REOPENED"):
            z_data["in_progress"] += 1
            z_data["active"] += 1
            z_data["unresolved_count"] += 1
        elif status in ("FINAL_RESOLVED", "RESOLUTION_SUBMITTED", "AWAITING_STUDENT_CONFIRMATION"):
            z_data["resolved"] += 1
            z_data["resolved_count"] += 1

        if priority == "High":
            z_data["high_priority"] += 1
            z_data["high_priority_count"] += 1
            if status in ["NEW", "FORWARDED", "IN_PROGRESS", "REOPENED"]:
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


def get_campus_pulse_data(department=None):
    """
    Computes real-time Campus Pulse executive telemetry:
    - Critical unresolved issues
    - Top problem area / hotspot
    - Resolution rate percentage
    - Active complaints volume
    - 7-day complaint activity trend velocity
    Optionally scoped to a specific department.
    """
    conn = get_db_connection()
    where = "WHERE department = ?" if department else "WHERE 1=1"
    params = (department,) if department else ()
    
    # 1. Total, Pending, Progress, Resolved
    stats = get_admin_statistics(department)
    total = stats["total"]
    pending = stats["pending"]
    in_progress = stats["in_progress"]
    resolved = stats["resolved"]
    active = pending + in_progress
    
    # 2. Critical Unresolved Issues (High Priority + Pending/In Progress)
    cur = conn.cursor()
    cur.execute(f"""
        SELECT COUNT(*) FROM complaints 
        {where} AND priority = 'High' AND status IN ('NEW', 'FORWARDED', 'IN_PROGRESS', 'REOPENED')
    """, params)
    critical_issues = cur.fetchone()[0]

    # 3. Top Problem Area (Location/Block with highest active unresolved complaints)
    cur.execute(f"""
        SELECT 
            COALESCE(NULLIF(block, ''), NULLIF(location, ''), 'Campus') as loc_name,
            COUNT(*) as active_cnt,
            SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as high_cnt
        FROM complaints
        {where} AND status IN ('NEW', 'FORWARDED', 'IN_PROGRESS', 'REOPENED')
        GROUP BY loc_name
        ORDER BY active_cnt DESC, high_cnt DESC
        LIMIT 1
    """, params)
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
    cur.execute(f"""
        SELECT COUNT(*) FROM complaints
        {where} AND priority = 'High' AND status != 'FINAL_RESOLVED'
    """, params)
    escalated_count = cur.fetchone()[0]

    # 6. Past 7-Day Velocity Trend
    now = datetime.now()
    daily_velocity = []
    velocity_7d = []
    for i in range(6, -1, -1):
        day_dt = now - timedelta(days=i)
        day_str = day_dt.strftime("%Y-%m-%d")
        day_label = day_dt.strftime("%a (%d %b)") if i in [0, 6] else day_dt.strftime("%a")
        
        cur.execute(f"SELECT COUNT(*) FROM complaints {where} AND date = ?", params + (day_str,))
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

    # Real DB calculation for avg resolution days
    cur.execute(f"""
        SELECT AVG(julianday(last_updated) - julianday(date)) 
        FROM complaints 
        {where} AND status = 'FINAL_RESOLVED' AND last_updated != '' AND date != ''
    """, params)
    avg_turnaround = cur.fetchone()[0]
    avg_resolution_days = round(float(avg_turnaround), 1) if avg_turnaround is not None else "N/A"

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
        "avg_resolution_days": avg_resolution_days,
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

def get_grouped_admin_issues():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT c.*, s.name AS student_name, s.email AS student_email 
        FROM complaints c 
        LEFT JOIN students s ON c.student_id = s.student_id
        ORDER BY c.complaint_id ASC
    """).fetchall()
    conn.close()

    groups = []
    
    for row in rows:
        c = dict(row)
        c['ticket_id'] = c.get('ticket_id') or format_ticket_id(c['complaint_id'], c['date'])
        
        is_transport = c.get('category') == 'Transport Complaint'
        
        found_group = False
        for g in groups:
            if g['category'] != c.get('category'):
                continue
                
            if is_transport:
                if g.get('bus_number') != c.get('bus_number') or \
                   g.get('route') != c.get('route') or \
                   g.get('pickup_drop_point') != c.get('pickup_drop_point') or \
                   g.get('transport_complaint_type') != c.get('transport_complaint_type'):
                    continue
            else:
                if g.get('block') != c.get('block') or \
                   g.get('floor_no') != c.get('floor_no') or \
                   g.get('room_no') != c.get('room_no'):
                    continue
            
            if is_similar_issue(c.get('description', ''), g['representative_description'], c.get('room_no', '')):
                # Only group if the student is DIFFERENT
                existing_students = set([comp['student_id'] for comp in g['complaints']])
                if c['student_id'] in existing_students:
                    continue # Do not group same student's complaints together
                    
                g['complaints'].append(c)
                g['complaint_count'] += 1
                g['affected_students'] = len(existing_students) + 1
                found_group = True
                break
                
        if not found_group:
            new_group = {
                'group_id': c['complaint_id'],
                'category': c.get('category'),
                'block': c.get('block'),
                'floor_no': c.get('floor_no'),
                'room_no': c.get('room_no'),
                'bus_number': c.get('bus_number'),
                'route': c.get('route'),
                'pickup_drop_point': c.get('pickup_drop_point'),
                'transport_complaint_type': c.get('transport_complaint_type'),
                'representative_description': c.get('description', ''),
                'complaint_count': 1,
                'affected_students': 1,
                'complaints': [c]
            }
            groups.append(new_group)
            
    groups.sort(key=lambda x: max(comp['complaint_id'] for comp in x['complaints']), reverse=True)
    return groups


def get_related_complaints(complaint_id):
    conn = get_db_connection()
    
    # Get target complaint
    target_comp = conn.execute(
        """
        SELECT complaints.*
        FROM complaints 
        WHERE complaint_id = ?
        """, 
        (complaint_id,)
    ).fetchone()
    
    if not target_comp:
        conn.close()
        return None
        
    target = dict(target_comp)
    is_transport = target.get('category') == 'Transport Complaint'
    
    # Get all reporters for this complaint
    reporters = conn.execute(
        """
        SELECT complaint_reporters.*, students.name AS student_name, students.email AS student_email
        FROM complaint_reporters
        JOIN students ON complaint_reporters.student_id = students.student_id
        WHERE complaint_id = ?
        ORDER BY reported_at DESC
        """, (complaint_id,)
    ).fetchall()
    
    conn.close()
    
    related = []
    unique_students = set()
    
    # In the new merged paradigm, every reporter row is effectively a "complaint submission" mapped to this master ticket
    # To keep the UI compatible with the modal (which expects a ticket_id and student_name for each item),
    # we yield pseudo-records representing each reporter's submission, sharing the master ticket_id.
    
    for row in reporters:
        r = dict(row)
        c = {
            'complaint_id': complaint_id,
            'ticket_id': target.get('ticket_id') or format_ticket_id(complaint_id, target.get('date')),
            'student_name': r.get('student_name'),
            'student_id': r.get('student_id')
        }
        related.append(c)
        unique_students.add(r['student_id'])
            
    return {
        'related_complaints': related,
        'report_count': len(related),
        'affected_student_count': len(unique_students),
        'category': target.get('category', ''),
        'location': f"{target.get('block', '')} • {target.get('floor_no', '')} • {target.get('room_no', '')}" if not is_transport else f"Bus {target.get('bus_number', '')} • Route {target.get('route', '')}",
        'issue': target.get('description', '')
    }
