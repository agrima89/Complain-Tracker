import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()
import re
for m in re.finditer(r'<div class="stat-label">(.*?)</div>\s*<div class="stat-value">(.*?)</div>', c):
    print(m.group(1).strip(), m.group(2).strip())
