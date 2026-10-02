import sys
with open('database.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace location with master['location'] in the insert query
c = c.replace(
    'transport_complaint_type,\n                master["department"], date_str, location, fingerprint,',
    'transport_complaint_type,\n                master["department"], date_str, master["location"], fingerprint,'
)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Patched successfully!')
