import database
res = database.get_all_complaints_admin_paginated()
print('Total Groups:', len(res['items']))
for g in res['items'][:3]:
    print(f"Issue: {g.get('category')} - {g.get('representative_description')[:30]} | Affected: {g.get('affected_student_count')} | Reports: {g.get('complaint_count')}")
