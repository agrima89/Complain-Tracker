import database
collections, col_summary = database.get_complaint_collections()
print("Total issues:", col_summary['total_issues'])
for col in collections[:3]:
    print(f"Col: {col['issue'][:30]} | {col['student_count']} Students | {col['report_count']} Reports")
