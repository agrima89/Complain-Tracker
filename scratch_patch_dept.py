import sys
with open('database.py', 'r', encoding='utf-8') as f:
    c = f.read()

# I will replace "department, date_str, location" with "master['department'], date_str, location"
c = c.replace(
    'transport_complaint_type,\n                department, date_str, location, fingerprint,',
    'transport_complaint_type,\n                master["department"], date_str, location, fingerprint,'
)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Patched successfully!')
