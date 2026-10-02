import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove import
content = content.replace('import smart_complaint\n', '')

# Remove api_analyze_complaint route
route_pattern1 = r'@app\.route\("/student/api/analyze-complaint", methods=\["POST"\]\).*?return jsonify\(analysis\)\n'
content = re.sub(route_pattern1, '', content, flags=re.DOTALL)

# Remove api_find_similar route
route_pattern2 = r'@app\.route\("/student/api/find-similar", methods=\["POST"\]\).*?return jsonify\(result\)\n'
content = re.sub(route_pattern2, '', content, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Cleaned app.py")
