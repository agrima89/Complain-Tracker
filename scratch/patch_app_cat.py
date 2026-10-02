import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'return render_template("submit_complaint.html", categories=categories, blocks=blocks, floors=floors, priorities=priorities)',
    'return render_template("submit_complaint.html", categories=categories, blocks=blocks, floors=floors, priorities=priorities, selected_category=request.args.get("category", ""))'
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated app.py")
