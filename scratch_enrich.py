import sys

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# I need to modify get_all_complaints_admin_paginated
# From:
#     return {
#         "items": [dict(r) for r in complaints_raw],
#         "total": total_count,
#
# To:
#     items = []
#     for r in complaints_raw:
#         c = dict(r)
#         related = get_related_complaints(c['complaint_id'])
#         if related:
#             c['affected_student_count'] = related['affected_student_count']
#             c['related_complaints_data'] = related
#         else:
#             c['affected_student_count'] = 1
#             c['related_complaints_data'] = None
#         items.append(c)
#     return {
#         "items": items,
#         "total": total_count,

import re
old_ret = '''    return {
        "items": [dict(r) for r in complaints_raw],
        "total": total_count,'''
new_ret = '''    items = []
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
        "total": total_count,'''

if old_ret in content:
    content = content.replace(old_ret, new_ret)
    with open('database.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully patched get_all_complaints_admin_paginated")
else:
    print("Could not find old return statement")
