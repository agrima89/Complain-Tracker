import re

with open('templates/landing.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the glass-journey-panel with a dynamic one, but since the landing page is public without login, it's just a generic stats panel.
# Wait, let's keep the journey panel structure but remove the static timeline, or maybe just remove journey panel and sensor network card and replace them with Live Complaint Overview and Department Activity.
new_right_column = """
      <!-- ================= RIGHT COLUMN: LIVE DATA DASHBOARD ================= -->
      <div class="hero-right-column">
        
        <!-- Top Stat Card -->
        <div class="floating-stat-card">
          <div class="stat-card-icon">⚡</div>
          <div class="stat-card-content">
            <div class="stat-card-number">{{ stats.resolved_complaints if stats else 0 }} Complaints Resolved</div>
            <div class="stat-card-label">Out of {{ stats.total_complaints if stats else 0 }} Total Complaints</div>
          </div>
        </div>

        <!-- Live Complaint Overview -->
        <div class="glass-journey-panel" style="padding: 1.5rem;">
          <div class="journey-panel-header" style="margin-bottom: 1rem;">
            <div class="window-controls-group">
              <span class="win-dot win-dot--red"></span>
              <span class="win-dot win-dot--yellow"></span>
              <span class="win-dot win-dot--green"></span>
              <span class="journey-panel-title">Live Complaint Overview</span>
            </div>
          </div>
          
          <div class="stats-list" style="display: flex; flex-direction: column; gap: 0.8rem; color: #fff;">
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem;">
                <span>Total Complaints</span> <strong>{{ stats.total_complaints if stats else 0 }}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem;">
                <span>Open Complaints</span> <strong>{{ stats.open_complaints if stats else 0 }}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem;">
                <span>In Progress</span> <strong>{{ stats.in_progress if stats else 0 }}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem;">
                <span>Awaiting Confirmation</span> <strong>{{ stats.awaiting if stats else 0 }}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem;">
                <span>Regenerated</span> <strong>{{ stats.regenerated if stats else 0 }}</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span>Final Resolved</span> <strong style="color: #4ade80;">{{ stats.resolved_complaints if stats else 0 }}</strong>
            </div>
          </div>
        </div>

        <!-- Department Activity -->
        <div class="sensor-network-card" style="margin-top: 1.5rem; padding: 1.5rem;">
          <div class="sensor-card-header" style="margin-bottom: 1rem;">
            <div class="sensor-title">
              <span class="sensor-bolt">🏢</span>
              <span>DEPARTMENT ACTIVITY</span>
            </div>
          </div>
          
          <div style="color: #fff; font-size: 0.9rem;">
            {% if stats and stats.department_activity %}
                {% for dept, count in stats.department_activity.items() %}
                <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <span>{{ dept }}</span>
                    <span style="background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">{{ count }}</span>
                </div>
                {% endendfor %}
            {% else %}
                <div style="padding: 1rem 0; text-align: center; color: rgba(255,255,255,0.6);">
                    No complaints recorded yet
                </div>
            {% endif %}
          </div>
        </div>

      </div>
"""

content = re.sub(r'<!-- ================= RIGHT COLUMN: FLOATING GLASS DASHBOARD ================= -->.*?</div>\s+</div>\s+</section>', new_right_column + '\n\n    </div>\n  </section>', content, flags=re.DOTALL)

# Replace the static tracking showcase with nothing or something else, but since it's just a design showcase let's just hide it or remove the static ticket.
# The tracking showcase has `<section class="tracking-showcase-section" id="trackingShowcaseSection">`
# Let's remove this section entirely since the user said "Replace with useful database-driven information" or just remove fake claims.
content = re.sub(r'<!-- ==========================================================================\s*5\. TRACKING SHOWCASE.*?</section>', '', content, flags=re.DOTALL)

with open('templates/landing.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated landing.html")
