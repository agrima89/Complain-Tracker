import os
import re

TEMPLATES_DIR = r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\templates"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Jinja if item.status
    content = re.sub(r"{%\s*if\s+(item|complaint)\.status\s*==\s*'Pending'\s*%}", r"{% if \1.status in ('NEW', 'FORWARDED') %}", content)
    content = re.sub(r"{%\s*elif\s+(item|complaint)\.status\s*==\s*'Pending'\s*%}", r"{% elif \1.status in ('NEW', 'FORWARDED') %}", content)

    content = re.sub(r"{%\s*if\s+(item|complaint)\.status\s*==\s*'In Progress'\s*%}", r"{% if \1.status in ('IN_PROGRESS', 'REOPENED') %}", content)
    content = re.sub(r"{%\s*elif\s+(item|complaint)\.status\s*==\s*'In Progress'\s*%}", r"{% elif \1.status in ('IN_PROGRESS', 'REOPENED') %}", content)

    content = re.sub(r"{%\s*if\s+(item|complaint)\.status\s*==\s*'Resolved'\s*%}", r"{% if \1.status in ('FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION') %}", content)
    content = re.sub(r"{%\s*elif\s+(item|complaint)\.status\s*==\s*'Resolved'\s*%}", r"{% elif \1.status in ('FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION') %}", content)

    # For inline ternaries
    content = re.sub(r"item\.status\s*==\s*'Pending'", r"item.status in ('NEW', 'FORWARDED')", content)
    content = re.sub(r"item\.status\s*==\s*'In Progress'", r"item.status in ('IN_PROGRESS', 'REOPENED')", content)
    content = re.sub(r"item\.status\s*==\s*'Resolved'", r"item.status in ('FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION')", content)
    
    content = re.sub(r"complaint\.status\s*==\s*'Pending'", r"complaint.status in ('NEW', 'FORWARDED')", content)
    content = re.sub(r"complaint\.status\s*==\s*'In Progress'", r"complaint.status in ('IN_PROGRESS', 'REOPENED')", content)
    content = re.sub(r"complaint\.status\s*==\s*'Resolved'", r"complaint.status in ('FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION')", content)

    # For literal text badges
    content = content.replace("⏳ Pending Review", "⏳ NEW/FORWARDED")
    content = content.replace("⏳ Pending", "⏳ NEW/FORWARDED")
    content = content.replace("⚡ In Progress", "⚡ IN PROGRESS")
    content = content.replace("✓ Resolved", "✓ RESOLVED")

    # Fix ticket_id fallbacks
    content = content.replace("item.ticket_id or '#' ~ \"%03d\"|format(item.complaint_id)", "item.ticket_id")
    content = content.replace("complaint.ticket_id if complaint.ticket_id else ('CMP-2026-%04d'|format(complaint.complaint_id))", "complaint.ticket_id")
    
    # Fix dropdown options in HTML forms manually for standard values
    content = content.replace(
        '<option value="Pending" {% if status_filter == \'Pending\' %}selected{% endif %}>Pending</option>',
        '<option value="NEW" {% if status_filter == \'NEW\' %}selected{% endif %}>NEW</option>\n<option value="FORWARDED" {% if status_filter == \'FORWARDED\' %}selected{% endif %}>FORWARDED</option>'
    )
    content = content.replace(
        '<option value="In Progress" {% if status_filter == \'In Progress\' %}selected{% endif %}>In Progress</option>',
        '<option value="IN_PROGRESS" {% if status_filter == \'IN_PROGRESS\' %}selected{% endif %}>IN PROGRESS</option>\n<option value="REOPENED" {% if status_filter == \'REOPENED\' %}selected{% endif %}>REOPENED</option>'
    )
    content = content.replace(
        '<option value="Resolved" {% if status_filter == \'Resolved\' %}selected{% endif %}>Resolved</option>',
        '<option value="RESOLUTION_SUBMITTED" {% if status_filter == \'RESOLUTION_SUBMITTED\' %}selected{% endif %}>RESOLUTION SUBMITTED</option>\n<option value="AWAITING_STUDENT_CONFIRMATION" {% if status_filter == \'AWAITING_STUDENT_CONFIRMATION\' %}selected{% endif %}>AWAITING CONFIRMATION</option>\n<option value="FINAL_RESOLVED" {% if status_filter == \'FINAL_RESOLVED\' %}selected{% endif %}>FINAL RESOLVED</option>'
    )

    # Admin Quick Status Update dropdown
    content = content.replace(
        '<option value="Pending" {% if item.status == \'Pending\' %}selected{% endif %}>Pending</option>',
        '<option value="NEW" {% if item.status == \'NEW\' %}selected{% endif %}>NEW</option>\n<option value="FORWARDED" {% if item.status == \'FORWARDED\' %}selected{% endif %}>FORWARDED</option>'
    )
    content = content.replace(
        '<option value="In Progress" {% if item.status == \'In Progress\' %}selected{% endif %}>In Progress</option>',
        '<option value="IN_PROGRESS" {% if item.status == \'IN_PROGRESS\' %}selected{% endif %}>IN PROGRESS</option>'
    )
    content = content.replace(
        '<option value="Resolved" {% if item.status == \'Resolved\' %}selected{% endif %}>Resolved</option>',
        '<option value="RESOLUTION_SUBMITTED" {% if item.status == \'RESOLUTION_SUBMITTED\' %}selected{% endif %}>RESOLUTION SUBMITTED</option>\n<option value="FINAL_RESOLVED" {% if item.status == \'FINAL_RESOLVED\' %}selected{% endif %}>FINAL RESOLVED</option>'
    )
    
    # Detail Status Update dropdown
    content = content.replace(
        '<option value="Pending" {% if complaint.status == \'Pending\' %}selected{% endif %}>Pending</option>',
        '<option value="NEW" {% if complaint.status == \'NEW\' %}selected{% endif %}>NEW</option>\n<option value="FORWARDED" {% if complaint.status == \'FORWARDED\' %}selected{% endif %}>FORWARDED</option>'
    )
    content = content.replace(
        '<option value="In Progress" {% if complaint.status == \'In Progress\' %}selected{% endif %}>In Progress</option>',
        '<option value="IN_PROGRESS" {% if complaint.status == \'IN_PROGRESS\' %}selected{% endif %}>IN PROGRESS</option>'
    )
    content = content.replace(
        '<option value="Resolved" {% if complaint.status == \'Resolved\' %}selected{% endif %}>Resolved</option>',
        '<option value="RESOLUTION_SUBMITTED" {% if complaint.status == \'RESOLUTION_SUBMITTED\' %}selected{% endif %}>RESOLUTION SUBMITTED</option>\n<option value="FINAL_RESOLVED" {% if complaint.status == \'FINAL_RESOLVED\' %}selected{% endif %}>FINAL RESOLVED</option>'
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, dirs, files in os.walk(TEMPLATES_DIR):
    for file in files:
        if file.endswith('.html'):
            process_file(os.path.join(root, file))

print("Templates processed for jinja conditions.")
