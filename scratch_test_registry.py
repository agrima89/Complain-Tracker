import database

conn = database.get_db_connection()
conn.row_factory = __import__('sqlite3').Row

# 1. Total records
c = conn.execute('SELECT complaint_id, ticket_id, department, status, is_primary, group_id FROM complaints').fetchall()
print('Total database complaints:', len(c))
for r in c:
    print(f'  {r["ticket_id"]} | Dept: {r["department"]} | Status: {r["status"]} | Primary: {r["is_primary"]}')

# 2. Stats
stats = database.get_admin_statistics('Electrical')
print('\nStatistics for Electrical:', stats['total'])

stats2 = database.get_admin_statistics()
print('Statistics (All):', stats2['total'])

# 3. Registry
reg = database.get_all_complaints_admin_paginated(department='Electrical')
print('\nRegistry for Electrical:', len(reg['items']))

reg2 = database.get_all_complaints_admin_paginated()
print('Registry (All):', len(reg2['items']))

conn.close()
