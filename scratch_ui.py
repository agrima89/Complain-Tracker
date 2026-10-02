import sys
import re

with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Restore the original table UI from earlier versions
original_table = '''<div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Ticket ID</th>
                <th>Students Affected</th>
                <th>Primary Reporter</th>
                <th>Category</th>
                <th>Block & Location</th>
                <th>Evidence</th>
                <th>Priority</th>
                <th>Date / Updated</th>
                <th>Status</th>
                <th>Quick Status Update</th>
                <th style="text-align: right;">Review</th>
              </tr>
            </thead>
            <tbody>
              {% for item in complaints %}
                <tr style="{% if item.is_escalated %}background: rgba(239, 68, 68, 0.05);{% endif %}">
                  <!-- Ticket ID & Escalation Badge -->
                  <td style="font-weight: 700; font-family: monospace; white-space: nowrap;">
                    <a href="{{ url_for('admin_complaint_detail_view', complaint_id=item.complaint_id) }}" style="color: #38bdf8; text-decoration: none;">
                      {{ item.ticket_id if item.ticket_id else ('CMP-2026-%04d'|format(item.complaint_id)) }}
                    </a>
                    {% if item.is_escalated %}
                      <div style="margin-top: 0.25rem;">
                        <span class="badge" style="background: rgba(239, 68, 68, 0.25); border: 1px solid rgba(239, 68, 68, 0.5); color: #fca5a5; font-size: 0.7rem; font-weight: 700;">
                          ⚠ Escalated
                        </span>
                      </div>
                    {% endif %}
                  </td>

                  <!-- Students Affected Badge -->
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
                  </td>

                  <!-- Student Details -->
                  <td>
                    <div style="font-weight: 600; color: #ffffff;">
                      {{ item.student_name }}
                      {% if item.affected_student_count and item.affected_student_count > 1 %}
                        <span style="font-size: 0.75rem; color: #38bdf8; font-weight: 500;">+ {{ item.affected_student_count - 1 }} more</span>
                      {% endif %}
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">
                      {{ item.student_email }}
                    </div>
                  </td>

                  <!-- Category -->
                  <td>
                    <span class="badge" style="background: rgba(255,255,255,0.05); color: #e2e8f0; font-weight: 500;">
                      {{ item.category }}
                    </span>
                  </td>

                  <!-- Location Details -->
                  <td>
                    <div style="font-size: 0.9rem; color: #ffffff; font-weight: 600;">
                      {% if item.category == 'Transport Complaint' %}
                        Bus {{ item.bus_number }}
                      {% else %}
                        Block {{ item.block }}
                      {% endif %}
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;">
                      {% if item.category == 'Transport Complaint' %}
                        {{ item.route }}
                      {% else %}
                        Rm {{ item.room_no }} • Fl {{ item.floor_no }}
                      {% endif %}
                    </div>
                  </td>

                  <!-- Evidence Snapshot -->
                  <td>
                    {% if item.photo_path %}
                      <a href="{{ url_for('static', filename=item.photo_path) }}" target="_blank" style="display: block; width: 45px; height: 45px; border-radius: 8px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); transition: all 0.2s;">
                        <img src="{{ url_for('static', filename=item.photo_path) }}" alt="Evidence" style="width: 100%; height: 100%; object-fit: cover;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                      </a>
                    {% else %}
                      <div style="width: 45px; height: 45px; border-radius: 8px; background: rgba(255,255,255,0.03); border: 1px dashed rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 0.7rem;">
                        N/A
                      </div>
                    {% endif %}
                  </td>

                  <!-- Priority Level -->
                  <td>
                    {% if item.priority == 'High' %}
                      <span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.3);">High</span>
                    {% elif item.priority == 'Medium' %}
                      <span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.3);">Medium</span>
                    {% else %}
                      <span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3);">Low</span>
                    {% endif %}
                  </td>

                  <!-- Dates -->
                  <td>
                    <div style="font-size: 0.85rem; color: #e2e8f0;">{{ item.date }}</div>
                    {% if item.last_updated %}
                      <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.2rem;">Upd: {{ item.last_updated[:10] }}</div>
                    {% endif %}
                  </td>

                  <!-- Status -->
                  <td>
                    <span class="badge status-{{ item.status|lower }}">{{ item.status }}</span>
                  </td>

                  <!-- Quick Status Update Actions -->
                  <td>
                    <div style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
                      {% if item.status == 'NEW' or item.status == 'FORWARDED' or item.status == 'REOPENED' %}
                        <form method="POST" action="{{ url_for('update_complaint_status_admin', complaint_id=item.complaint_id) }}" style="display: inline;">
                          <input type="hidden" name="new_status" value="IN_PROGRESS">
                          <button type="submit" class="btn btn-primary btn-sm" style="padding: 0.3rem 0.6rem; font-size: 0.75rem;">Start Work</button>
                        </form>
                      {% endif %}
                      
                      {% if item.status == 'IN_PROGRESS' %}
                        <form method="POST" action="{{ url_for('update_complaint_status_admin', complaint_id=item.complaint_id) }}" style="display: inline;">
                          <input type="hidden" name="new_status" value="RESOLUTION_SUBMITTED">
                          <button type="submit" class="btn btn-success btn-sm" style="padding: 0.3rem 0.6rem; font-size: 0.75rem; background: #10b981; color: white;">Resolve</button>
                        </form>
                      {% endif %}
                    </div>
                  </td>

                  <!-- Full Review Link -->
                  <td style="text-align: right;">
                    <a href="{{ url_for('admin_complaint_detail_view', complaint_id=item.complaint_id) }}" class="btn btn-secondary btn-sm" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">
                      Review &rarr;
                    </a>
                  </td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>'''

# 1. Replace the "card-body" that holds my grouped logic with the original table
start_marker = '<div class="card-body" style="display: flex; flex-direction: column; gap: 1rem; padding: 1.5rem;">'
end_marker = '</div>\n\n        <!-- Pagination Controls -->'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + original_table + content[end_idx:]


# 2. Add the collections UI above the complaints table
collections_ui = '''
<!-- Complaint Collections Section -->
  <div class="card" style="margin-bottom: 2rem;">
    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
      <div>
        <h2 style="font-size: 1.25rem; font-weight: 700; margin: 0; color: #ffffff;">COMPLAINT COLLECTIONS</h2>
        <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 0.25rem;">View and manage multiple student reports for the same campus issue.</div>
      </div>
    </div>
    
    <!-- Collections Summary -->
    <div style="display: flex; flex-wrap: wrap; gap: 1rem; padding: 1.5rem; background: rgba(3, 7, 18, 0.4); border-bottom: 1px solid rgba(255,255,255,0.05);">
      <div style="flex: 1; min-width: 120px; background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); text-align: center;">
        <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Total Issues</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #ffffff; margin-top: 0.25rem;">{{ col_summary.total_issues }}</div>
      </div>
      <div style="flex: 1; min-width: 120px; background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); text-align: center;">
        <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Affected Students</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #38bdf8; margin-top: 0.25rem;">{{ col_summary.affected_students }}</div>
      </div>
      <div style="flex: 1; min-width: 120px; background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); text-align: center;">
        <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Open Issues</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #f87171; margin-top: 0.25rem;">{{ col_summary.open_issues }}</div>
      </div>
      <div style="flex: 1; min-width: 120px; background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); text-align: center;">
        <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">In Progress</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #facc15; margin-top: 0.25rem;">{{ col_summary.in_progress }}</div>
      </div>
      <div style="flex: 1; min-width: 120px; background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); text-align: center;">
        <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Resolved</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #4ade80; margin-top: 0.25rem;">{{ col_summary.resolved }}</div>
      </div>
    </div>

    <!-- Collections List -->
    <div class="card-body" style="padding: 1.5rem;">
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem;">
        {% for col in collections %}
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; display: flex; flex-direction: column;">
          
          <div style="padding: 1.25rem; flex: 1;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
              <div style="font-weight: 700; color: #f87171; display: flex; align-items: center; gap: 0.5rem; text-transform: uppercase; font-size: 0.85rem;">
                ⚡ {{ col.category }}
              </div>
              
              <div style="display: flex; gap: 0.5rem;">
                <!-- Overall Priority Badge -->
                {% if col.priority == 'High' %}
                  <span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.3);">🔴 HIGH</span>
                {% elif col.priority == 'Medium' %}
                  <span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.3);">🟡 MEDIUM</span>
                {% else %}
                  <span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3);">🟢 LOW</span>
                {% endif %}
                
                <!-- Overall Status Badge -->
                <span class="badge" style="
                  {% if col.status == 'NEW' %} background: rgba(56, 189, 248, 0.2); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.3);
                  {% elif col.status == 'IN_PROGRESS' %} background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.3);
                  {% else %} background: rgba(74, 222, 128, 0.2); color: #86efac; border: 1px solid rgba(74, 222, 128, 0.3); {% endif %}
                ">{{ col.status }}</span>
              </div>
            </div>
            
            <div style="font-size: 1.1rem; color: #ffffff; font-weight: 600; margin-bottom: 0.5rem; line-height: 1.4;">
              {{ col.issue|truncate(60) }}
            </div>
            
            <div style="font-size: 0.85rem; color: #94a3b8; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 1rem;">
              📍 {{ col.location }}
            </div>
            
            <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
              <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; color: #e2e8f0;">
                👥 {{ col.student_count }} Student{% if col.student_count != 1 %}s{% endif %} Affected
              </div>
              <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; color: #e2e8f0;">
                🎫 {{ col.report_count }} Report{% if col.report_count != 1 %}s{% endif %}
              </div>
            </div>
          </div>
          
          <div style="padding: 1rem; border-top: 1px solid rgba(255,255,255,0.05); background: rgba(0,0,0,0.15);">
            <button onclick="document.getElementById('modal-{{ col.collection_id }}').style.display = 'flex'" class="btn btn-secondary" style="width: 100%; justify-content: center;">
              [ View Collection ]
            </button>
          </div>
          
        </div>
        
        <!-- Modal for this Collection -->
        <div id="modal-{{ col.collection_id }}" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center; padding: 2rem;">
          <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; width: 100%; max-width: 800px; max-height: 90vh; display: flex; flex-direction: column;">
            
            <!-- Modal Header -->
            <div style="padding: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: flex-start;">
              <div>
                <div style="font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-bottom: 0.5rem;">SAME COMPLAINT COLLECTION</div>
                <h3 style="font-size: 1.5rem; font-weight: 700; color: #ffffff; margin: 0 0 0.5rem 0;">{{ col.issue }}</h3>
                <div style="font-size: 0.95rem; color: #cbd5e1; display: flex; gap: 1rem; flex-wrap: wrap;">
                  <span><strong>Category:</strong> {{ col.category }}</span>
                  <span><strong>Location:</strong> {{ col.location }}</span>
                  <span><strong>Students Affected:</strong> {{ col.student_count }}</span>
                  <span><strong>Total Reports:</strong> {{ col.report_count }}</span>
                </div>
              </div>
              <button onclick="document.getElementById('modal-{{ col.collection_id }}').style.display = 'none'" style="background: none; border: none; color: #94a3b8; font-size: 1.5rem; cursor: pointer;">&times;</button>
            </div>
            
            <!-- Modal Summary -->
            <div style="padding: 1rem 1.5rem; background: rgba(255,255,255,0.02); display: flex; gap: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.05);">
              <div style="display: flex; gap: 0.5rem; color: #e2e8f0; font-weight: 600;">
                👥 {{ col.student_count }} Students Affected
              </div>
              <div style="display: flex; gap: 0.5rem; color: #e2e8f0; font-weight: 600;">
                🎫 {{ col.report_count }} Reports
              </div>
              <div style="margin-left: auto; display: flex; gap: 1rem; font-size: 0.85rem;">
                <span style="color: #7dd3fc;">NEW: {{ col.status_counts.NEW }}</span>
                <span style="color: #fcd34d;">IN PROGRESS: {{ col.status_counts.IN_PROGRESS }}</span>
                <span style="color: #86efac;">RESOLVED: {{ col.status_counts.RESOLVED }}</span>
              </div>
            </div>
            
            <!-- Modal Body (Individual Complaints) -->
            <div style="padding: 1.5rem; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 1rem;">
              {% for c in col.complaints %}
              <div style="padding: 1rem; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <div style="font-family: monospace; font-size: 1.1rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.25rem;">{{ c.ticket_id }}</div>
                  <div style="font-size: 0.95rem; color: #e2e8f0; margin-bottom: 0.25rem;">{{ c.student_name }}</div>
                  <div style="display: flex; gap: 0.5rem; font-size: 0.8rem;">
                    <span class="badge status-{{ c.status|lower }}">{{ c.status }}</span>
                    <span style="color: #94a3b8;">Priority: {{ c.priority|upper }}</span>
                  </div>
                </div>
                <a href="{{ url_for('admin_complaint_detail_view', complaint_id=c.complaint_id) }}" class="btn btn-primary btn-sm">
                  [ View Complaint ]
                </a>
              </div>
              {% endfor %}
            </div>
            
          </div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
'''

insertion_point = content.find('<!-- Filters & Actions -->')
if insertion_point != -1:
    content = content[:insertion_point] + collections_ui + content[insertion_point:]


with open('templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
