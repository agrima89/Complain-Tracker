import sys
with open('database.py', 'r', encoding='utf-8') as f:
    c = f.read()

start = c.find('query_sql = f"""')
end = c.find('"""', start + 16)
print(c[start:end+3])
