import os

ADMIN_JS = r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\static\js\admin.js"

with open(ADMIN_JS, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update filter status check
old_filter = "filtered = filtered.filter((c) => (c.status !== 'Resolved'));"
new_filter = "filtered = filtered.filter((c) => (!['FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION'].includes(c.status)));"
content = content.replace(old_filter, new_filter)

# 2. Add selectZone(currentZoneId) to initial load
old_poll = "  // Poll for live zone telemetry every 25 seconds"
new_poll = """  // Initial selection
  if (currentZoneId) {
    selectZone(currentZoneId);
  }

  // Poll for live zone telemetry every 25 seconds"""
content = content.replace(old_poll, new_poll)

with open(ADMIN_JS, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied patch_admin_js successfully.")
