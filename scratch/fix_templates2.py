import os
import re

TEMPLATES_DIR = r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\templates"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We want to replace the hardcoded spans with dynamic text based on the variable in scope.
    # We must match the badge span. The text inside the span could be "⏳ NEW/FORWARDED", "⚡ IN PROGRESS", "✓ RESOLVED"
    # But wait, we need to know whether the variable is `item` or `complaint`.
    # Let's just use regex to find the context.

    # 1. For `item.status`
    # Replace: ⏳ NEW/FORWARDED -> ⏳ {{ item.status.replace('_', ' ')|title }}
    content = re.sub(
        r"{% if item\.status in \('NEW', 'FORWARDED'\) %}\s*<span class=\"badge badge-pending\">⏳ NEW/FORWARDED</span>",
        r"{% if item.status in ('NEW', 'FORWARDED') %}\n                      <span class=\"badge badge-pending\">⏳ {{ item.status.replace('_', ' ')|title }}</span>",
        content
    )
    content = re.sub(
        r"{% elif item\.status in \('IN_PROGRESS', 'REOPENED'\) %}\s*<span class=\"badge badge-progress\">⚡ IN PROGRESS</span>",
        r"{% elif item.status in ('IN_PROGRESS', 'REOPENED') %}\n                      <span class=\"badge badge-progress\">⚡ {{ item.status.replace('_', ' ')|title }}</span>",
        content
    )
    content = re.sub(
        r"{% elif item\.status in \('FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION'\) %}\s*<span class=\"badge badge-resolved\">✓ RESOLVED</span>",
        r"{% elif item.status in ('FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION') %}\n                      <span class=\"badge badge-resolved\">✓ {{ item.status.replace('_', ' ')|title }}</span>",
        content
    )

    # 2. For `complaint.status`
    content = re.sub(
        r"{% if complaint\.status in \('NEW', 'FORWARDED'\) %}\s*<span ([^>]*)class=\"badge badge-pending\">⏳ NEW/FORWARDED</span>",
        r"{% if complaint.status in ('NEW', 'FORWARDED') %}\n          <span \1class=\"badge badge-pending\">⏳ {{ complaint.status.replace('_', ' ')|title }}</span>",
        content
    )
    content = re.sub(
        r"{% elif complaint\.status in \('IN_PROGRESS', 'REOPENED'\) %}\s*<span ([^>]*)class=\"badge badge-progress\">⚡ IN PROGRESS</span>",
        r"{% elif complaint.status in ('IN_PROGRESS', 'REOPENED') %}\n          <span \1class=\"badge badge-progress\">⚡ {{ complaint.status.replace('_', ' ')|title }}</span>",
        content
    )
    content = re.sub(
        r"{% elif complaint\.status in \('FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION'\) %}\s*<span ([^>]*)class=\"badge badge-resolved\">✓ RESOLVED</span>",
        r"{% elif complaint.status in ('FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION') %}\n          <span \1class=\"badge badge-resolved\">✓ {{ complaint.status.replace('_', ' ')|title }}</span>",
        content
    )
    
    # 3. For any leftover direct text instances that weren't caught (except submit_complaint)
    if "submit_complaint" not in filepath:
        content = content.replace("⏳ NEW/FORWARDED", "⏳ {{ item.status.replace('_', ' ')|title if item else complaint.status.replace('_', ' ')|title }}")
        content = content.replace("⚡ IN PROGRESS", "⚡ {{ item.status.replace('_', ' ')|title if item else complaint.status.replace('_', ' ')|title }}")
        content = content.replace("✓ RESOLVED", "✓ {{ item.status.replace('_', ' ')|title if item else complaint.status.replace('_', ' ')|title }}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, dirs, files in os.walk(TEMPLATES_DIR):
    for file in files:
        if file.endswith('.html'):
            process_file(os.path.join(root, file))

print("Fixed UI displayed statuses.")
