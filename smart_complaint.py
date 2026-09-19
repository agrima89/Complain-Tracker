"""
CampusCare - Smart Complaint & Resolution Intelligence Module
Provides lightweight, local heuristic analysis for:
1. Smart Complaint Detection (Category, Priority, Location, Reason)
2. Similar / Duplicate Complaint Detection (Keyword TF-IDF / Jaccard similarity)
"""

import re
import math
from datetime import datetime
import database

# ---------------- DOMAIN KEYWORD DICTIONARIES ----------------

CATEGORY_KEYWORDS = {
    "Electrical": {
        "spark": 4, "sparking": 4, "shock": 5, "short circuit": 5, "wire": 3, "wiring": 3,
        "power": 2, "electricity": 3, "blackout": 4, "light": 2, "bulb": 2, "tube": 2,
        "tubelight": 3, "fan": 2, "ac": 2, "air conditioner": 3, "heater": 2, "geyser": 3,
        "socket": 3, "switch": 2, "switchboard": 3, "mcb": 4, "breaker": 3, "plug": 2,
        "generator": 3, "voltage": 3, "fluctuation": 3, "dark": 2, "fuse": 3, "tripped": 3
    },
    "Cleaning": {
        "water": 2, "leak": 3, "leakage": 4, "leaking": 4, "pipe": 3, "tap": 3, "faucet": 3,
        "sink": 3, "washroom": 3, "toilet": 4, "restroom": 3, "flush": 3, "dirty": 3,
        "clean": 2, "cleaning": 3, "garbage": 3, "trash": 3, "dustbin": 2, "waste": 2,
        "smell": 3, "stench": 3, "odor": 3, "foul": 3, "cockroach": 3, "insect": 2,
        "pest": 3, "mosquito": 2, "mop": 2, "slippery": 4, "puddle": 3, "overflow": 4,
        "stain": 2, "dust": 2, "sanitation": 3, "drain": 4, "drainage": 4, "choked": 4,
        "clogged": 4, "blocked": 3
    },
    "Hostel": {
        "hostel": 5, "room": 2, "warden": 4, "mess": 4, "food": 3, "bed": 3, "mattress": 3,
        "cupboard": 3, "almirah": 3, "roommate": 3, "curfew": 3, "balcony": 2, "cooler": 2,
        "laundry": 3, "washing machine": 3, "water cooler": 3, "canteen": 2, "wing": 2,
        "corridor": 2, "iron": 2, "hot water": 3, "hostel gate": 3, "guards": 2, "curtain": 2
    },
    "Wi-Fi/Internet": {
        "wifi": 5, "wi-fi": 5, "internet": 5, "network": 4, "lan": 4, "ethernet": 4,
        "router": 4, "speed": 3, "slow": 3, "offline": 4, "disconnect": 4, "disconnected": 4,
        "portal": 3, "login": 2, "signal": 3, "bandwidth": 3, "connection": 3, "connecting": 3,
        "ping": 2, "dns": 3, "server down": 4, "cable": 2
    },
    "Classroom": {
        "projector": 5, "screen": 3, "podium": 3, "mic": 4, "microphone": 4, "speaker": 3,
        "sound": 2, "audio": 2, "bench": 3, "desk": 3, "chair": 2, "board": 3, "whiteboard": 3,
        "blackboard": 3, "marker": 2, "duster": 2, "classroom": 4, "lecture": 3, "hall": 2,
        "smart board": 4, "hdmi": 3, "display": 2
    },
    "Library": {
        "book": 4, "books": 4, "library": 5, "librarian": 4, "issue": 3, "return": 3,
        "barcode": 3, "reading room": 4, "reference": 3, "journal": 3, "magazine": 2,
        "study hall": 4, "quiet": 2, "noise": 3, "digital library": 4, "catalog": 3, "fine": 2
    },
    "Infrastructure": {
        "door": 3, "window": 3, "glass": 4, "broken glass": 5, "lock": 3, "handle": 2,
        "wall": 3, "ceiling": 3, "roof": 3, "tiles": 3, "plaster": 3, "crack": 4,
        "paint": 2, "lift": 4, "elevator": 4, "stuck lift": 5, "stairs": 3, "staircase": 3,
        "railing": 4, "road": 3, "pothole": 4, "parking": 3, "gate": 3, "boundary": 2,
        "furniture": 3, "table": 2, "structural": 4, "collapse": 5, "damage": 3
    }
}

PRIORITY_URGENT_KEYWORDS = {
    # High Priority triggers (Emergency, Safety Hazard, Fire, Shock, Structural)
    "emergency": 6, "dangerous": 5, "danger": 5, "shock": 6, "electric shock": 7,
    "spark": 5, "sparking": 6, "fire": 7, "smoke": 6, "burning": 6, "short circuit": 6,
    "flood": 5, "flooding": 5, "slippery": 4, "broken glass": 5, "lift stuck": 6,
    "trapped": 6, "hazard": 5, "hazardous": 5, "unsafe": 5, "injury": 6, "hurt": 5,
    "accident": 5, "urgent": 4, "urgently": 4, "immediate": 4, "collapse": 6, "falling": 5,
    "choked drain": 4, "blackout": 4, "gas leak": 7, "snake": 6, "medical": 5
}

PRIORITY_MEDIUM_KEYWORDS = {
    "broken": 3, "not working": 3, "malfunction": 3, "stopped": 3, "leak": 3, "leakage": 3,
    "slow": 2, "damaged": 3, "faulty": 3, "smell": 2, "dirty": 2, "choked": 3, "clogged": 3,
    "noise": 2, "flickering": 2, "offline": 2, "error": 2, "issue": 1, "problem": 1
}

PRIORITY_LOW_KEYWORDS = {
    "minor": 3, "request": 3, "suggestion": 3, "replace": 2, "dust": 2, "cosmetic": 3,
    "paint": 2, "update": 2, "inquiry": 3, "query": 3, "routine": 2, "slowly": 1
}

LOCATION_KEYWORD_MAP = [
    (r"\bgirls?\s*hostel\b|\bgh\b|\bgirls?\s*wing\b", "Hostel", "Girls Hostel"),
    (r"\bboys?\s*hostel\b|\bbh\b|\bboys?\s*wing\b", "Hostel", "Boys Hostel"),
    (r"\bhostel\b|\bmess\b|\bwarden\b", "Hostel", "Hostel"),
    (r"\blibrary\b|\breading\s*room\b", "Library", "Central Library"),
    (r"\bsports?\b|\bgym\b|\bground\b|\bcourt\b|\bstadium\b", "Sports", "Sports Complex"),
    (r"\bacademic\s*block\b|\bacademic\b", "Academic Block", "Academic Block"),
    (r"\bblock\s*a\b|\bblock-a\b|\bsector\s*a\b", "Block A", "Block A"),
    (r"\bblock\s*b\b|\bblock-b\b|\bsector\s*b\b", "Block B", "Block B"),
    (r"\bblock\s*c\b|\bblock-c\b|\bsector\s*c\b", "Block C", "Block C"),
    (r"\bblock\s*d\b|\bblock-d\b|\bsector\s*d\b", "Block D", "Block D"),
    (r"\bblock\s*e\b|\bblock-e\b|\bsector\s*e\b", "Block E", "Block E"),
    (r"\bblock\s*f\b|\bblock-f\b|\bsector\s*f\b", "Block F", "Block F"),
    (r"\bcafeteria\b|\bcanteen\b|\bfood\s*court\b", "Campus", "Cafeteria / Food Court"),
    (r"\bparking\b|\bvehicle\b|\bbike\s*stand\b", "Campus", "Parking Area"),
    (r"\blab\b|\blaboratory\b|\bcomputer\s*lab\b", "Academic Block", "Computer / Science Labs"),
    (r"\bauditorium\b|\baudi\b|\bseminar\s*hall\b", "Campus", "Auditorium / Seminar Hall"),
    (r"\bwashroom\b|\btoilet\b|\brestroom\b", "Academic Block", "Restroom / Washroom Area"),
]

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "did", "do", "does", "doing", "don", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "with", "you", "your", "yours", "yourself", "yourselves", "please", "kindly", "sir", "madam"
}


# ---------------- 1. SMART COMPLAINT DETECTION ----------------

def tokenize_text(text):
    """Clean and extract alphanumeric tokens from text."""
    if not text:
        return []
    cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
    words = [w.strip() for w in cleaned.split() if len(w.strip()) > 1]
    return words


def detect_category(text):
    """
    Scores each complaint category based on keyword matches and returns
    (best_category, confidence_score, matched_keywords).
    """
    text_lower = text.lower()
    scores = {cat: 0 for cat in database.VALID_CATEGORIES}
    matched_words = {cat: [] for cat in database.VALID_CATEGORIES}

    for cat, kw_dict in CATEGORY_KEYWORDS.items():
        if cat not in scores:
            continue
        for kw, weight in kw_dict.items():
            if " " in kw:
                if kw in text_lower:
                    scores[cat] += weight * 2
                    matched_words[cat].append(kw)
            else:
                # Word boundary match
                pattern = r"\b" + re.escape(kw) + r"\b"
                matches = len(re.findall(pattern, text_lower))
                if matches > 0:
                    scores[cat] += weight * matches
                    matched_words[cat].append(kw)

    best_cat = "Other"
    max_score = 0
    for cat, score in scores.items():
        if score > max_score:
            max_score = score
            best_cat = cat

    # Default fallback
    if max_score == 0:
        best_cat = "Infrastructure"

    return best_cat, max_score, matched_words.get(best_cat, [])


def detect_priority(text, category="Other"):
    """
    Detects priority level (High, Medium, Low) based on safety hazards,
    urgency expressions, and complaint severity.
    """
    text_lower = text.lower()
    high_score = 0
    med_score = 0
    low_score = 0
    urgency_reasons = []

    for kw, weight in PRIORITY_URGENT_KEYWORDS.items():
        if " " in kw:
            if kw in text_lower:
                high_score += weight * 2
                urgency_reasons.append(kw)
        else:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                high_score += weight
                urgency_reasons.append(kw)

    for kw, weight in PRIORITY_MEDIUM_KEYWORDS.items():
        if " " in kw:
            if kw in text_lower:
                med_score += weight
        else:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                med_score += weight

    for kw, weight in PRIORITY_LOW_KEYWORDS.items():
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            low_score += weight

    # Priority decision logic
    if high_score >= 4 or (high_score > 0 and category in ["Electrical", "Cleaning"]):
        priority = "High"
    elif med_score >= 2 or high_score > 0:
        priority = "Medium"
    elif low_score > med_score and low_score > 0:
        priority = "Low"
    else:
        priority = "Medium"

    return priority, urgency_reasons


def detect_location(text):
    """
    Detects campus block and specific area from text descriptions.
    Returns (block, specific_label).
    """
    text_lower = text.lower()
    for pattern, block, label in LOCATION_KEYWORD_MAP:
        if re.search(pattern, text_lower):
            return block, label

    # Check for room patterns (e.g., F-204, B-302, Room 402)
    room_match = re.search(r"\b([a-f])[- ]?([1-9][0-9]{2})\b", text_lower)
    if room_match:
        block_letter = room_match.group(1).upper()
        block_name = f"Block {block_letter}"
        if block_name in database.VALID_BLOCKS:
            return block_name, f"{block_name}, Room {room_match.group(2)}"

    return "", ""


def generate_reason(category, priority, location_label, matched_keywords, urgency_reasons):
    """Generates an intuitive, user-friendly reason explaining the suggestions."""
    parts = []

    if urgency_reasons:
        parts.append(f"{', '.join(urgency_reasons[:2])} safety factor detected")
    elif matched_keywords:
        parts.append(f"{', '.join(matched_keywords[:2])} domain detected")

    if location_label:
        parts.append(f"located at {location_label}")

    if priority == "High":
        if "safety" not in " ".join(parts):
            parts.append("elevated urgency assigned")

    if not parts:
        return "Automatic contextual campus analysis"

    return " + ".join(parts).capitalize()


def analyze_complaint(text):
    """
    Main Smart Assist entrypoint: analyzes raw description text and returns
    comprehensive structured suggestions.
    """
    if not text or len(text.strip()) < 5:
        return {
            "success": False,
            "message": "Text too short for analysis"
        }

    category, cat_score, matched_kws = detect_category(text)
    priority, urgency_reasons = detect_priority(text, category)
    block, location_label = detect_location(text)
    reason = generate_reason(category, priority, location_label, matched_kws, urgency_reasons)

    # Calculate overall confidence
    confidence = min(0.95, round(0.45 + (cat_score * 0.05) + (len(urgency_reasons) * 0.1), 2))

    return {
        "success": True,
        "category": category,
        "priority": priority,
        "location": block or location_label or "Campus",
        "block": block,
        "location_block": block,
        "location_label": location_label or block or "Campus Premises",
        "reason": reason,
        "confidence": confidence,
        "keywords": matched_kws + urgency_reasons
    }


# ---------------- 2. SIMILAR / DUPLICATE COMPLAINT DETECTION ----------------

def get_clean_keywords(text):
    """Filters stop words and returns a set of meaningful lowercase keyword tokens."""
    tokens = tokenize_text(text)
    return {w for w in tokens if w not in STOP_WORDS and len(w) > 2}


def compute_similarity_score(desc1, desc2, cat1=None, cat2=None, block1=None, block2=None):
    """
    Computes a hybrid similarity score (0.0 to 1.0) combining:
    1. Jaccard Keyword Token Overlap (weight 0.60)
    2. Category Match (weight 0.20)
    3. Location/Block Match (weight 0.20)
    """
    kw1 = get_clean_keywords(desc1)
    kw2 = get_clean_keywords(desc2)

    if not kw1 or not kw2:
        return 0.0

    # Jaccard Token Overlap
    intersection = len(kw1 & kw2)
    union = len(kw1 | kw2)
    jaccard = intersection / union if union > 0 else 0.0

    # Boost score if multiple key specific nouns match (e.g. "leakage", "sparking", "wifi")
    bonus = 0.0
    common_kws = kw1 & kw2
    for kw in common_kws:
        if len(kw) >= 5:
            bonus += 0.05
    bonus = min(0.15, bonus)

    token_score = min(1.0, jaccard + bonus)

    # Category matching bonus
    cat_match_score = 0.0
    if cat1 and cat2 and cat1 == cat2:
        cat_match_score = 1.0

    # Location/Block matching bonus
    block_match_score = 0.0
    if block1 and block2 and block1.lower() == block2.lower() and block1.lower() not in ["", "other", "campus"]:
        block_match_score = 1.0

    # Weighted aggregate
    total_score = (token_score * 0.60) + (cat_match_score * 0.20) + (block_match_score * 0.20)
    return round(total_score, 3)


def find_similar_complaints(description, category=None, block=None, threshold=0.28, limit=4):
    """
    Inspects existing unresolved complaints (Pending & In Progress) in the database
    and returns matches exceeding the similarity threshold.
    """
    if not description or len(description.strip()) < 8:
        return {
            "found": False,
            "count": 0,
            "similar": []
        }

    # Fetch active unresolved complaints from database
    active_complaints = database.get_unresolved_complaints_for_similarity()

    matches = []
    for c in active_complaints:
        c_desc = c["description"]
        c_cat = c["category"]
        c_block = c["block"] or c["location"]

        score = compute_similarity_score(
            desc1=description,
            desc2=c_desc,
            cat1=category,
            cat2=c_cat,
            block1=block,
            block2=c_block
        )

        if score >= threshold:
            # Build match summary snippet
            tid = c["ticket_id"] or f"CMP-2026-{c['complaint_id']:04d}"
            loc_label = c["block"] or c["location"] or "Campus"
            if c["room_no"]:
                loc_label += f" ({c['room_no']})"

            # Calculate human-friendly date note
            date_note = c["date"]
            try:
                c_date = datetime.strptime(c["date"][:10], "%Y-%m-%d").date()
                today = datetime.now().date()
                days_diff = (today - c_date).days
                if days_diff == 0:
                    date_note = "Today"
                elif days_diff == 1:
                    date_note = "Yesterday"
                elif days_diff > 1:
                    date_note = f"{days_diff} days ago"
            except Exception:
                pass

            matches.append({
                "complaint_id": c["complaint_id"],
                "ticket_id": tid,
                "category": c_cat,
                "location": loc_label,
                "priority": c["priority"],
                "status": c["status"],
                "date": c["date"],
                "date_note": date_note,
                "similarity": round(score * 100),
                "snippet": c_desc[:140] + ("..." if len(c_desc) > 140 else "")
            })

    # Sort descending by similarity
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    top_matches = matches[:limit]
    has_matches = len(top_matches) > 0

    return {
        "success": True,
        "found": has_matches,
        "has_similar": has_matches,
        "count": len(top_matches),
        "similar": top_matches,
        "similar_complaints": top_matches
    }
