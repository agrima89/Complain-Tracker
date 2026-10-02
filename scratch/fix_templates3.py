import os

TEMPLATES_DIR = r"c:\Users\LOQ\OneDrive\Desktop\College_Complaint_Tracker\templates"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove the backslashes before quotes
    content = content.replace(r'\"', '"')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, dirs, files in os.walk(TEMPLATES_DIR):
    for file in files:
        if file.endswith('.html'):
            process_file(os.path.join(root, file))

print("Fixed backslashes in UI templates.")
