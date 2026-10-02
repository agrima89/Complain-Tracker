import sys

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update stem_map
start_idx = content.find('"airconditioner": "ac", "airconditioners": "ac"')
if start_idx != -1:
    content = content[:start_idx] + '"airconditioner": "ac", "airconditioners": "ac",\n        "cleaned": "clean", "cleaning": "clean", "cleans": "clean"' + content[start_idx + 49:]
else:
    print('Failed to find stem_map')

# 2. Update submit_or_attach_complaint
target_str = '''    if not date_str:
        date_str = str(date.today())'''

validation_block = '''

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
'''

content = content.replace(target_str, target_str + validation_block)

# 3. Add BEGIN EXCLUSIVE to submit_or_attach_complaint
target_str2 = '''    conn = get_db_connection()
    cursor = conn.cursor()'''
    
transaction_block = '''    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("BEGIN EXCLUSIVE")'''

content = content.replace(target_str2, transaction_block)

content = content.replace('print("ACTION = REJECT_DUPLICATE")\n            conn.close()', 'print("ACTION = REJECT_DUPLICATE")\n            conn.rollback()\n            conn.close()')

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched successfully!')
