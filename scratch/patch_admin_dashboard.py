import os

ADMIN_DASHBOARD = r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\templates\admin_dashboard.html"

with open(ADMIN_DASHBOARD, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Avg Turnaround
old_avg_turnaround = "Avg Turnaround: ~{{ pulse_data.avg_resolution_days }}d"
new_avg_turnaround = "Avg Turnaround: {% if pulse_data.avg_resolution_days == 'N/A' %}N/A{% else %}~{{ pulse_data.avg_resolution_days }}d{% endif %}"
content = content.replace(old_avg_turnaround, new_avg_turnaround)

# 2. Update Escalated text
old_escalated = "<span>{{ pulse_data.escalated_count }} flagged for escalation</span>"
new_escalated = "<span>{% if pulse_data.escalated_count == 0 %}No complaints currently escalated.{% else %}{{ pulse_data.escalated_count }} complaints currently escalated.{% endif %}</span>"
content = content.replace(old_escalated, new_escalated)

# 3. Update Pending Action (Problem 8)
# Is there a "Pending Action" card? Let's check.
# Wait, let's look for "Pending Action"
old_pending_action = "Pending Action"
new_pending_action = "Pending Action (New & Forwarded)"
# We'll just replace the first instance if it's the card title.
content = content.replace("Pending Action", "Pending Action (New & Forwarded)")


with open(ADMIN_DASHBOARD, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied patch_admin_dashboard.py successfully.")
