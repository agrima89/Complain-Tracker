import re

with open('templates/profile.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Admin Username section to include Role and Department
old_admin = """        {% else %}
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 0.85rem;">
            <span style="color: #94a3b8; font-size: 0.9rem;">Admin Username</span>
            <span style="font-weight: 600; color: #ffffff;">{{ session.get('admin_username') }}</span>
          </div>
        {% endif %}"""

new_admin = """        {% else %}
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 0.85rem;">
            <span style="color: #94a3b8; font-size: 0.9rem;">Admin Username</span>
            <span style="font-weight: 600; color: #ffffff;">{{ session.get('admin_username') }}</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 0.85rem;">
            <span style="color: #94a3b8; font-size: 0.9rem;">Admin Role</span>
            <span style="font-weight: 600; color: #ffffff;">{{ session.get('admin_role') }}</span>
          </div>
          {% if session.get('admin_department') %}
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 0.85rem;">
            <span style="color: #94a3b8; font-size: 0.9rem;">Department</span>
            <span style="font-weight: 600; color: #ffffff;">{{ session.get('admin_department') }}</span>
          </div>
          {% endif %}
        {% endif %}"""

content = content.replace(old_admin, new_admin)

with open('templates/profile.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated profile.html")
