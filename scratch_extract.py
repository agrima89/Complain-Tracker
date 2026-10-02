import ast

with open("database.py", "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "delete_student_complaint":
        lines = source.splitlines()[node.lineno - 1 : node.end_lineno]
        print("\n".join(lines))
