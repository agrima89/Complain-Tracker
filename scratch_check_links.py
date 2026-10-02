import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()
import re
print(re.findall(r'<a.*?href=".*?status=.*?.*?</a', c, re.DOTALL)[:5])
