import sys
import re

with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Header
header_old = '<th>Student</th>'
header_new = '<th>Students Affected</th>\n                <th>Student</th>'
content = content.replace(header_old, header_new)

# 2. Find the <td> for Student to insert the new <td> before it
student_td_pattern = r'(<td>\s*<div style="font-weight: 600; color: #ffffff;">\s*\{\{\s*item\.student_name\s*\}\})'

new_td = '''                  <!-- Students Affected Badge -->
                  <td>
                    {% if item.affected_student_count and item.affected_student_count > 1 %}
                      <button type="button" onclick="document.getElementById('modal-rel-{{ item.complaint_id }}').style.display='flex'" style="background: rgba(56, 189, 248, 0.2); border: 1px solid rgba(56, 189, 248, 0.45); color: #38bdf8; font-weight: 700; font-size: 0.85rem; padding: 0.4rem 0.75rem; border-radius: 8px; display: inline-flex; align-items: center; gap: 0.4rem; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(56, 189, 248, 0.3)'" onmouseout="this.style.background='rgba(56, 189, 248, 0.2)'" title="View all students who reported this">
                        👥 {{ item.affected_student_count }} Students
                      </button>
                    {% else %}
                      <span class="badge" style="background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.12); color: #94a3b8; font-size: 0.8rem; padding: 0.35rem 0.65rem; border-radius: 8px; display: inline-flex; align-items: center; gap: 0.35rem;">
                        👤 1 Reporter
                      </span>
                    {% endif %}
                  </td>
'''

content, count = re.subn(student_td_pattern, new_td + r'\1', content)
print(f"Replaced {count} instances.")

with open('templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched HTML!')
