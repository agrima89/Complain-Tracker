import sys
with open('database.py', 'r', encoding='utf-8') as f:
    c = f.read()

start = c.find('query_sql = f"""')
end = c.find('return', start)
print(c[start:end+200])
