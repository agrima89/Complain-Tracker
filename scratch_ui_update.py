import sys

with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove Complaint Collections section
start_col = '<!-- Complaint Collections Section -->'
end_col = '<div class="table-responsive">'
s1 = content.find(start_col)
e1 = content.find(end_col, s1)
if s1 != -1 and e1 != -1:
    content = content[:s1] + content[e1:]
    
# 2. Update Students Affected column
old_col = '''                  <!-- Students Affected Badge -->
                  <td>
                    {% if item.affected_student_count and item.affected_student_count > 1 %}
                      <span class="badge" style="background: rgba(56, 189, 248, 0.2); border: 1px solid rgba(56, 189, 248, 0.45); color: #38bdf8; font-weight: 700; font-size: 0.8rem; padding: 0.35rem 0.65rem; border-radius: 8px; display: inline-flex; align-items: center; gap: 0.35rem;" title="{{ item.affected_student_count }} students reported this issue">
                        👥 {{ item.affected_student_count }} Affected
                      </span>
                    {% else %}
                      <span class="badge" style="background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.12); color: #94a3b8; font-size: 0.8rem; padding: 0.35rem 0.65rem; border-radius: 8px; display: inline-flex; align-items: center; gap: 0.35rem;">
                        👤 1 Reporter
                      </span>
                    {% endif %}
                  </td>'''

new_col = '''                  <!-- Students Affected Badge -->
                  <td>
                    {% if item.affected_student_count and item.affected_student_count > 1 %}
                      <button type="button" onclick="document.getElementById('modal-rel-{{ item.complaint_id }}').style.display='flex'" style="background: rgba(56, 189, 248, 0.2); border: 1px solid rgba(56, 189, 248, 0.45); color: #38bdf8; font-weight: 700; font-size: 0.85rem; padding: 0.4rem 0.75rem; border-radius: 8px; display: inline-flex; align-items: center; gap: 0.4rem; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(56, 189, 248, 0.3)'" onmouseout="this.style.background='rgba(56, 189, 248, 0.2)'" title="View all students who reported this">
                        👥 {{ item.affected_student_count }} Students
                      </button>
                    {% else %}
                      <span class="badge" style="background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.12); color: #94a3b8; font-size: 0.8rem; padding: 0.35rem 0.65rem; border-radius: 8px; display: inline-flex; align-items: center; gap: 0.35rem;">
                        👤 1 Reporter
                      </span>
                    {% endif %}
                  </td>'''

if old_col in content:
    content = content.replace(old_col, new_col)
else:
    print("Warning: old column format not found")

# 3. Add modals for each item with >1 affected students
modals = '''
<!-- Related Complaints Modals -->
{% for item in complaints %}
  {% if item.related_complaints_data and item.affected_student_count > 1 %}
  <div id="modal-rel-{{ item.complaint_id }}" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 1050; align-items: center; justify-content: center; padding: 2rem;">
    <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; width: 100%; max-width: 600px; max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);">
      
      <!-- Modal Header -->
      <div style="padding: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: flex-start; background: rgba(255,255,255,0.02);">
        <div>
          <h3 style="font-size: 1.25rem; font-weight: 700; color: #ffffff; margin: 0 0 0.5rem 0;">Same Complaint Reports</h3>
          <div style="font-size: 0.95rem; color: #38bdf8; font-weight: 600; margin-bottom: 0.75rem;">
            {{ item.affected_student_count }} students reported this issue
          </div>
          <div style="font-size: 0.85rem; color: #cbd5e1; display: flex; flex-direction: column; gap: 0.35rem;">
            <div><strong style="color: #94a3b8;">Category:</strong> {{ item.related_complaints_data.category }}</div>
            <div><strong style="color: #94a3b8;">Location:</strong> {{ item.related_complaints_data.location }}</div>
            <div><strong style="color: #94a3b8;">Issue:</strong> {{ item.related_complaints_data.issue }}</div>
          </div>
        </div>
        <button onclick="document.getElementById('modal-rel-{{ item.complaint_id }}').style.display = 'none'" style="background: none; border: none; color: #94a3b8; font-size: 1.75rem; cursor: pointer; line-height: 1; padding: 0;">&times;</button>
      </div>
      
      <!-- Modal Body (Individual Complaints) -->
      <div style="padding: 1.5rem; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 0.75rem;">
        {% for c in item.related_complaints_data.related_complaints %}
        <a href="{{ url_for('admin_complaint_detail_view', complaint_id=c.complaint_id) }}" style="text-decoration: none;">
          <div style="padding: 1rem; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.06)'; this.style.borderColor='rgba(56,189,248,0.3)';" onmouseout="this.style.background='rgba(255,255,255,0.03)'; this.style.borderColor='rgba(255,255,255,0.05)';">
            <div>
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                <span style="font-size: 1.1rem;">👤</span>
                <span style="font-size: 1rem; color: #ffffff; font-weight: 600;">{{ c.student_name }}</span>
              </div>
              <div style="font-family: monospace; font-size: 0.9rem; font-weight: 700; color: #94a3b8; margin-left: 1.6rem;">{{ c.ticket_id }}</div>
            </div>
            <div style="font-size: 1.25rem; color: #38bdf8; opacity: 0.5;">&rarr;</div>
          </div>
        </a>
        {% endfor %}
      </div>
      
    </div>
  </div>
  {% endif %}
{% endfor %}
'''

if '<!-- Related Complaints Modals -->' not in content:
    e2 = content.rfind('{% endblock %}')
    if e2 != -1:
        content = content[:e2] + modals + '\n' + content[e2:]
        print("Modals added")

with open('templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

