import re

with open('templates/submit_complaint.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_select = r'{%\s*for cat in categories\s*%}.*?</option>'
new_select = '{% for cat in categories %}\n                <option value="{{ cat }}" {% if selected_category == cat %}selected{% endif %}>{{ cat }}</option>'

if 'selected_category' not in content:
    content = re.sub(old_select, new_select, content, flags=re.DOTALL)
    with open('templates/submit_complaint.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated submit_complaint.html')

with open('templates/landing.html', 'r', encoding='utf-8') as f:
    landing = f.read()

if 'Transport' not in landing or 'category=Transport' not in landing:
    # Add transport to category buttons
    # Assuming there's a div containing these links. We will inject it after Classroom.
    classroom_link = r'<a href="\{\{\s*url_for\(\'submit_complaint_view\',\s*category=\'Classroom\'\).*?</a>'
    
    match = re.search(classroom_link, landing, re.DOTALL)
    if match:
        transport_link = '\n        <a href="{{ url_for(\'submit_complaint_view\', category=\'Transport\') if session.get(\'student_id\') else url_for(\'student_login_view\') }}" class="glass-category-chip">\n          <span class="chip-icon">🚌</span> Transport\n        </a>'
        landing = landing[:match.end()] + transport_link + landing[match.end():]
        
        with open('templates/landing.html', 'w', encoding='utf-8') as f:
            f.write(landing)
        print('Updated landing.html with Transport button')
