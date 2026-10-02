import re

with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update the stats grid
old_stats = """  <!-- Compact Action Stats Grid -->
  <div class="stats-grid">
    <!-- Pending / Action Required -->
    <div class="stat-card stat-pending">
      <div class="stat-header">
        <span class="stat-label" style="color: #fbbf24;">ACTION REQUIRED</span>
        <div class="stat-icon" style="color: #fbbf24; background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.3);">⚠️</div>
      </div>
      <div class="stat-value" style="color: #fbbf24;">{{ stats.pending }}</div>
      <div class="stat-subtext">Pending Complaints</div>
    </div>

    <!-- In Progress / Active Work -->
    <div class="stat-card stat-progress">
      <div class="stat-header">
        <span class="stat-label" style="color: #38bdf8;">ACTIVE WORK</span>
        <div class="stat-icon" style="color: #38bdf8; background: rgba(56, 189, 248, 0.12); border-color: rgba(56, 189, 248, 0.3);">⚡</div>
      </div>
      <div class="stat-value" style="color: #38bdf8;">{{ stats.in_progress }}</div>
      <div class="stat-subtext">In Progress Complaints</div>
    </div>

    <!-- Escalated / Overdue -->
    <div class="stat-card" style="border-top-color: #ef4444; background: linear-gradient(180deg, rgba(239, 68, 68, 0.05) 0%, rgba(15, 23, 42, 0.95) 100%);">
      <div class="stat-header">
        <span class="stat-label" style="color: #ef4444;">ESCALATED</span>
        <div class="stat-icon" style="color: #ef4444; background: rgba(239, 68, 68, 0.12); border-color: rgba(239, 68, 68, 0.3);">🚨</div>
      </div>
      <div class="stat-value" style="color: #ef4444;">{{ stats.escalated }}</div>
      <div class="stat-subtext">Over 48h / High Priority</div>
    </div>

    <!-- Total Handled -->
    <div class="stat-card stat-resolved">
      <div class="stat-header">
        <span class="stat-label" style="color: #4ade80;">RESOLUTION</span>
        <div class="stat-icon" style="color: #4ade80; background: rgba(34, 197, 94, 0.12); border-color: rgba(34, 197, 94, 0.3);">✓</div>
      </div>
      <div class="stat-value" style="color: #4ade80;">{{ stats.resolved }} <span style="font-size: 1rem; color: #64748b; font-weight: 500;">/ {{ stats.total }}</span></div>
      <div class="stat-subtext">Completed Tickets</div>
    </div>
  </div>"""

new_stats = """  <!-- Compact Action Stats Grid -->
  <div class="stats-grid" style="grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));">
    <div class="stat-card stat-pending">
      <div class="stat-header">
        <span class="stat-label" style="color: #fbbf24;">NEW/FWD</span>
        <div class="stat-icon" style="color: #fbbf24; background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.3);">⚠️</div>
      </div>
      <div class="stat-value" style="color: #fbbf24;">{{ stats.new + stats.forwarded }}</div>
      <div class="stat-subtext">Awaiting Action</div>
    </div>

    <div class="stat-card stat-progress">
      <div class="stat-header">
        <span class="stat-label" style="color: #38bdf8;">ACTIVE</span>
        <div class="stat-icon" style="color: #38bdf8; background: rgba(56, 189, 248, 0.12); border-color: rgba(56, 189, 248, 0.3);">⚡</div>
      </div>
      <div class="stat-value" style="color: #38bdf8;">{{ stats.in_progress }}</div>
      <div class="stat-subtext">In Progress</div>
    </div>

    <div class="stat-card" style="border-top-color: #ef4444; background: linear-gradient(180deg, rgba(239, 68, 68, 0.05) 0%, rgba(15, 23, 42, 0.95) 100%);">
      <div class="stat-header">
        <span class="stat-label" style="color: #ef4444;">ESCALATED</span>
        <div class="stat-icon" style="color: #ef4444; background: rgba(239, 68, 68, 0.12); border-color: rgba(239, 68, 68, 0.3);">🚨</div>
      </div>
      <div class="stat-value" style="color: #ef4444;">{{ stats.escalated }}</div>
      <div class="stat-subtext">High Priority</div>
    </div>
    
    <div class="stat-card" style="border-top-color: #a855f7; background: linear-gradient(180deg, rgba(168, 85, 247, 0.05) 0%, rgba(15, 23, 42, 0.95) 100%);">
      <div class="stat-header">
        <span class="stat-label" style="color: #c084fc;">AWAITING CONF</span>
        <div class="stat-icon" style="color: #c084fc; background: rgba(168, 85, 247, 0.12); border-color: rgba(168, 85, 247, 0.3);">⏳</div>
      </div>
      <div class="stat-value" style="color: #c084fc;">{{ stats.awaiting_student_confirmation }}</div>
      <div class="stat-subtext">Student Check</div>
    </div>
    
    <div class="stat-card" style="border-top-color: #f43f5e; background: linear-gradient(180deg, rgba(244, 63, 94, 0.05) 0%, rgba(15, 23, 42, 0.95) 100%);">
      <div class="stat-header">
        <span class="stat-label" style="color: #fb7185;">REGENERATED</span>
        <div class="stat-icon" style="color: #fb7185; background: rgba(244, 63, 94, 0.12); border-color: rgba(244, 63, 94, 0.3);">🔄</div>
      </div>
      <div class="stat-value" style="color: #fb7185;">{{ stats.regenerated }}</div>
      <div class="stat-subtext">Needs Fix</div>
    </div>

    <div class="stat-card stat-resolved">
      <div class="stat-header">
        <span class="stat-label" style="color: #4ade80;">RESOLVED</span>
        <div class="stat-icon" style="color: #4ade80; background: rgba(34, 197, 94, 0.12); border-color: rgba(34, 197, 94, 0.3);">✓</div>
      </div>
      <div class="stat-value" style="color: #4ade80;">{{ stats.resolved }} <span style="font-size: 1rem; color: #64748b; font-weight: 500;">/ {{ stats.total }}</span></div>
      <div class="stat-subtext">Final Resolved</div>
    </div>
  </div>"""

content = content.replace(old_stats, new_stats)

# Add SOC link and profile link in the top bar
old_top_bar = """    <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
      <a href="{{ url_for('landing') }}" class="btn btn-secondary" style="padding: 0.65rem 1.15rem; font-size: 0.95rem;">
        <span>🌐</span> Public Portal
      </a>
      <a href="{{ url_for('profile_view') }}" class="btn btn-secondary" style="padding: 0.65rem 1.15rem; font-size: 0.95rem;">
        <span>👤</span> Admin Profile
      </a>
    </div>"""

new_top_bar = """    <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
      <a href="{{ url_for('landing') }}" class="btn btn-secondary" style="padding: 0.65rem 1.15rem; font-size: 0.95rem;">
        <span>🌐</span> Public Portal
      </a>
      {% if session.get('admin_role') != 'HOD' %}
      <a href="{{ url_for('soc_dashboard') }}" class="btn btn-secondary" style="padding: 0.65rem 1.15rem; font-size: 0.95rem; border-color: #ef4444; color: #ef4444;">
        <span>🛡️</span> SOC Logs
      </a>
      {% endif %}
      <a href="{{ url_for('profile_view') }}" class="btn btn-secondary" style="padding: 0.65rem 1.15rem; font-size: 0.95rem;">
        <span>👤</span> Admin Profile
      </a>
    </div>"""
content = content.replace(old_top_bar, new_top_bar)

# Fix filter statuses
content = content.replace('<option value="Pending" {% if request.args.get("status") == "Pending" %}selected{% endif %}>Pending</option>',
                          '<option value="NEW" {% if request.args.get("status") == "NEW" %}selected{% endif %}>NEW</option>\n<option value="FORWARDED" {% if request.args.get("status") == "FORWARDED" %}selected{% endif %}>FORWARDED</option>\n<option value="REGENERATED" {% if request.args.get("status") == "REGENERATED" %}selected{% endif %}>REGENERATED</option>')
content = content.replace('<option value="In Progress" {% if request.args.get("status") == "In Progress" %}selected{% endif %}>In Progress</option>',
                          '<option value="IN_PROGRESS" {% if request.args.get("status") == "IN_PROGRESS" %}selected{% endif %}>IN_PROGRESS</option>\n<option value="AWAITING_STUDENT_CONFIRMATION" {% if request.args.get("status") == "AWAITING_STUDENT_CONFIRMATION" %}selected{% endif %}>AWAITING CONFIRMATION</option>')
content = content.replace('<option value="Resolved" {% if request.args.get("status") == "Resolved" %}selected{% endif %}>Resolved</option>',
                          '<option value="RESOLVED_BY_DEPARTMENT" {% if request.args.get("status") == "RESOLVED_BY_DEPARTMENT" %}selected{% endif %}>RESOLVED_BY_DEPARTMENT</option>\n<option value="FINAL_RESOLVED" {% if request.args.get("status") == "FINAL_RESOLVED" %}selected{% endif %}>FINAL_RESOLVED</option>')

with open('templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated admin_dashboard.html")
