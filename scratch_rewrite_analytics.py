import sys

with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = 'def get_analytics_data(department=None):'
end_marker = '# Backwards compatibility alias'
start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print('Failed to find markers')
    sys.exit(1)

new_func = '''def get_analytics_data(department=None):
    """
    Aggregates statistical insights for the admin dashboard:
    Category breakdown, Priority breakdown, Status distribution, and 6-Month trends.
    Optionally scoped to a specific department.
    """
    conn = get_db_connection()
    where = "WHERE department = ?" if department else "WHERE 1=1"
    params = (department,) if department else ()

    # 1. By Category
    cat_rows = conn.execute(f"SELECT category, COUNT(*) as count FROM complaints {where} GROUP BY category ORDER BY count DESC", params).fetchall()
    by_category = {row["category"]: row["count"] for row in cat_rows}
    categories_list = [{"category": row["category"], "count": row["count"]} for row in cat_rows]

    # 2. By Priority
    prio_rows = conn.execute(f"SELECT priority, COUNT(*) as count FROM complaints {where} GROUP BY priority", params).fetchall()
    by_priority = {"Low": 0, "Medium": 0, "High": 0}
    for row in prio_rows:
        by_priority[row["priority"]] = row["count"]
    priorities_list = [{"priority": p, "count": by_priority[p]} for p in ["High", "Medium", "Low"]]

    # 3. By Status
    status_rows = conn.execute(f"SELECT status, COUNT(*) as count FROM complaints {where} GROUP BY status", params).fetchall()
    by_status = {"Pending": 0, "In Progress": 0, "Resolved": 0}
    for row in status_rows:
        s = row["status"]
        if s in ("NEW", "FORWARDED", "RESOLUTION_SUBMITTED", "AWAITING_STUDENT_CONFIRMATION"):
            by_status["Pending"] += row["count"]
        elif s in ("IN_PROGRESS", "REOPENED"):
            by_status["In Progress"] += row["count"]
        elif s == "FINAL_RESOLVED":
            by_status["Resolved"] += row["count"]
    statuses_list = [{"status": s, "count": by_status[s]} for s in ["Pending", "In Progress", "Resolved"]]

    # 4. Monthly Trend (Past 6 Months)
    monthly_trend = []
    from datetime import datetime, timedelta
    now = datetime.now()
    for i in range(5, -1, -1):
        m_date = now - timedelta(days=i * 30)
        m_str = m_date.strftime("%Y-%m")
        m_label = m_date.strftime("%b %Y")
        m_count = conn.execute(f"SELECT COUNT(*) FROM complaints {where} AND date LIKE ?", params + (f"{m_str}%",)).fetchone()[0]
        monthly_trend.append({"month": m_label, "count": m_count})

    total = sum(by_status.values())
    resolved_pct = round((by_status["Resolved"] / total * 100), 1) if total > 0 else 0.0

    conn.close()
    return {
        "by_category": by_category,
        "categories": categories_list,
        "by_priority": by_priority,
        "priorities": priorities_list,
        "by_status": by_status,
        "statuses": statuses_list,
        "monthly_trend": monthly_trend,
        "monthly_trends": monthly_trend,
        "total_complaints": total,
        "resolved_percentage": resolved_pct
    }

'''

content = content[:start_idx] + new_func + '\n' + content[end_idx:]

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched get_analytics_data!')
