import re

def extract_canonical_room(room_str):
    if not room_str:
        return ""
    m = re.search(r"\b(?:room|rm)?[ -]?(?:[a-z]-?)?([0-9]{2,4}[a-z]?)\b", str(room_str), re.IGNORECASE)
    if m:
        return m.group(1).lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", str(room_str).lower()).strip()
    return cleaned

def check_floor(room_no, floor_no):
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
            return False, implied_floor, canon_room
    return True, None, canon_room

print(check_floor('323', '3rd Floor'))
print(check_floor('323', '2nd Floor'))
print(check_floor('E-323', '3rd Floor'))
print(check_floor('E-323', '2nd Floor'))
print(check_floor('001', 'Ground Floor'))
