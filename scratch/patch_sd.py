import re

with open('templates/student_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_stats_grid = """  <!-- 1. COMPACT SAAS STATISTICS GRID -->
  <div class="stats-grid" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));">
    
    <!-- Total Logged -->
    <div class="stat-card">
      <div class="stat-header">
        <span class="stat-label">TOTAL</span>
        <div class="stat-icon">📊</div>
      </div>
      <div class="stat-value">{{ stats.total }}</div>
      <div class="stat-subtext">Complaints</div>
    </div>

    <!-- Pending Review -->
    <div class="stat-card stat-pending">
      <div class="stat-header">
        <span class="stat-label" style="color: #fbbf24;">OPEN</span>
        <div class="stat-icon" style="color: #fbbf24; background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.3);">⏳</div>
      </div>
      <div class="stat-value" style="color: #fbbf24;">{{ stats.pending }}</div>
      <div class="stat-subtext">New/Forwarded</div>
    </div>

    <!-- In Progress -->
    <div class="stat-card stat-progress">
      <div class="stat-header">
        <span class="stat-label" style="color: #38bdf8;">IN PROGRESS</span>
        <div class="stat-icon" style="color: #38bdf8; background: rgba(56, 189, 248, 0.12); border-color: rgba(56, 189, 248, 0.3);">🔄</div>
      </div>
      <div class="stat-value" style="color: #38bdf8;">{{ stats.in_progress }}</div>
      <div class="stat-subtext">Working</div>
    </div>
    
    <!-- Awaiting Confirmation -->
    <div class="stat-card" style="border-top-color: #a855f7; background: linear-gradient(180deg, rgba(168, 85, 247, 0.05) 0%, rgba(15, 23, 42, 0.95) 100%);">
      <div class="stat-header">
        <span class="stat-label" style="color: #c084fc;">CONFIRM</span>
        <div class="stat-icon" style="color: #c084fc; background: rgba(168, 85, 247, 0.12); border-color: rgba(168, 85, 247, 0.3);">⚠️</div>
      </div>
      <div class="stat-value" style="color: #c084fc;">{{ stats.awaiting }}</div>
      <div class="stat-subtext">Needs Action</div>
    </div>

    <!-- Regenerated -->
    <div class="stat-card" style="border-top-color: #f43f5e; background: linear-gradient(180deg, rgba(244, 63, 94, 0.05) 0%, rgba(15, 23, 42, 0.95) 100%);">
      <div class="stat-header">
        <span class="stat-label" style="color: #fb7185;">REGENERATED</span>
        <div class="stat-icon" style="color: #fb7185; background: rgba(244, 63, 94, 0.12); border-color: rgba(244, 63, 94, 0.3);">🔄</div>
      </div>
      <div class="stat-value" style="color: #fb7185;">{{ stats.regenerated }}</div>
      <div class="stat-subtext">Sent Back</div>
    </div>

    <!-- Resolved -->
    <div class="stat-card stat-resolved">
      <div class="stat-header">
        <span class="stat-label" style="color: #4ade80;">RESOLVED</span>
        <div class="stat-icon" style="color: #4ade80; background: rgba(34, 197, 94, 0.12); border-color: rgba(34, 197, 94, 0.3);">✓</div>
      </div>
      <div class="stat-value" style="color: #4ade80;">{{ stats.resolved }}</div>
      <div class="stat-subtext">Closed</div>
    </div>

  </div>"""

content = re.sub(r'<!-- 1\. COMPACT SAAS STATISTICS GRID -->.*<!-- 2\. QUICK ACTIONS SECTION -->', new_stats_grid + '\n\n  <!-- 2. QUICK ACTIONS SECTION -->', content, flags=re.DOTALL)

with open('templates/student_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated student_dashboard.html")
