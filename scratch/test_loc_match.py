import os
import sys
import re
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import database

def extract_canonical_room(room_str):
    if not room_str:
        return ""
    # Look for room/rm followed by room code or 2-4 digits with optional letters
    m = re.search(r"\b(?:room|rm)?[ -]?(?:[a-z]-?)?([0-9]{2,4}[a-z]?)\b", str(room_str), re.IGNORECASE)
    if m:
        return m.group(1).lower()
    # Fallback to cleaning alphanumeric tokens
    cleaned = re.sub(r"[^a-z0-9]+", " ", str(room_str).lower()).strip()
    return cleaned

def get_canonical_location_key(category, block="", room_no="", location="", bus_number="", route="", transport_type=""):
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

# Test with DB data
conn = database.get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT complaint_id, ticket_id, student_id, category, block, room_no, location FROM complaints")
for r in cursor.fetchall():
    loc_key = get_canonical_location_key(r["category"], block=r["block"], room_no=r["room_no"], location=r["location"])
    print(f"Complaint {r['complaint_id']} ({r['ticket_id']}): student={r['student_id']}, cat={r['category']}, loc_key='{loc_key}'")

# Test user example: Student 166 submits another Electrical complaint for Block E, Room E-329
sub_key = get_canonical_location_key("Electrical", block="Block E", room_no="Room E-329")
print(f"\nNew submission test key: '{sub_key}'")

# Check match
cursor.execute("""
    SELECT complaint_id, ticket_id, status FROM complaints
    WHERE student_id = 166
      AND LOWER(category) = LOWER('Electrical')
      AND status IN ('NEW', 'PENDING', 'IN_PROGRESS', 'REOPENED', 'FORWARDED')
    ORDER BY complaint_id DESC
""")
candidates = cursor.fetchall()
found = None
for c in candidates:
    # Fetch full row
    row = cursor.execute("SELECT * FROM complaints WHERE complaint_id = ?", (c["complaint_id"],)).fetchone()
    cand_key = get_canonical_location_key(row["category"], block=row["block"], room_no=row["room_no"], location=row["location"])
    if cand_key == sub_key:
        found = c
        break

if found:
    print(f"MATCH FOUND: Existing active ticket {found['ticket_id']} (status: {found['status']})")
else:
    print("NO MATCH FOUND")

conn.close()
