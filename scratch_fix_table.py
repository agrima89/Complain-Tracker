import sys

with open('Complain-Tracker/templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    orig = f.read()

start_marker = '<div class="table-responsive">'
end_marker = '</div>\n\n        <!-- Pagination Controls -->'
s = orig.find(start_marker)
e = orig.find(end_marker, s)

if s != -1 and e != -1:
    actual_original_table = orig[s:e]
    
    with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
        curr = f.read()
        
    s2 = curr.find(start_marker)
    e2 = curr.find(end_marker, s2)
    
    if s2 != -1 and e2 != -1:
        new_curr = curr[:s2] + actual_original_table + curr[e2:]
        with open('templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(new_curr)
        print('Successfully replaced hallucinated table with the actual original table!')
    else:
        print('Could not find markers in current template.')
else:
    print('Could not find markers in original template.')
