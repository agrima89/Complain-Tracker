import re

with open('templates/admin_complaint_detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the Update Status form with the Workflow Forms (Forward, Mark Resolved)
old_form_match = re.search(r'<!-- Update Status Form -->.*?</div>\s+</div>', content, re.DOTALL)
if old_form_match:
    old_form = old_form_match.group(0)
    
    new_forms = """<!-- Admin Workflow Actions -->
          <div style="background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
            <h3 style="font-size: 1.05rem; font-weight: 600; color: #e2e8f0; margin-bottom: 1.25rem;">Actions</h3>
            
            {% if session.get('admin_role') != 'HOD' and complaint.status in ['NEW', 'FORWARDED', 'REGENERATED'] %}
            <!-- Forwarding Form (Admin only) -->
            <form action="{{ url_for('api_forward_complaint') }}" method="POST" style="margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
              <input type="hidden" name="complaint_id" value="{{ complaint.complaint_id }}">
              <div class="form-group" style="margin-bottom: 1rem;">
                <label style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.4rem; display: block;">Forward to Department</label>
                <select name="department" class="form-control" required style="width: 100%; padding: 0.6rem; border-radius: 6px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.2); color: #fff;">
                  <option value="">-- Select Department --</option>
                  <option value="Electrical">Electrical</option>
                  <option value="Civil/Maintenance">Civil/Maintenance</option>
                  <option value="Housekeeping">Housekeeping</option>
                  <option value="Transport">Transport</option>
                  <option value="IT">IT</option>
                  <option value="Security">Security</option>
                  <option value="Academic">Academic</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div class="form-group" style="margin-bottom: 1rem;">
                <label style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.4rem; display: block;">Reason / Remarks</label>
                <input type="text" name="reason" class="form-control" placeholder="Optional remarks" style="width: 100%; padding: 0.6rem; border-radius: 6px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.2); color: #fff;">
              </div>
              <button type="submit" class="btn btn-secondary" style="width: 100%;">Forward Complaint</button>
            </form>
            {% endif %}
            
            {% if complaint.status in ['NEW', 'FORWARDED', 'IN_PROGRESS', 'REGENERATED'] %}
            <!-- Update Status (Generic) Form -->
            <form action="{{ url_for('update_status') }}" method="POST" style="margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
              <input type="hidden" name="complaint_id" value="{{ complaint.complaint_id }}">
              <div class="form-group" style="margin-bottom: 1rem;">
                <label style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.4rem; display: block;">Update Status</label>
                <select name="status" class="form-control" style="width: 100%; padding: 0.6rem; border-radius: 6px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.2); color: #fff;">
                  <option value="IN_PROGRESS" {% if complaint.status == 'IN_PROGRESS' %}selected{% endif %}>In Progress</option>
                </select>
              </div>
              <button type="submit" class="btn btn-primary" style="width: 100%;">Mark In Progress</button>
            </form>

            <!-- Mark Resolved by Department Form -->
            <form action="{{ url_for('api_mark_resolved') }}" method="POST">
              <input type="hidden" name="complaint_id" value="{{ complaint.complaint_id }}">
              <div class="form-group" style="margin-bottom: 1rem;">
                <label style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.4rem; display: block;">Resolution Remarks</label>
                <textarea name="remarks" class="form-control" rows="2" placeholder="Required explanation of how it was resolved..." required style="width: 100%; padding: 0.6rem; border-radius: 6px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.2); color: #fff;"></textarea>
              </div>
              <button type="submit" class="btn btn-secondary" style="width: 100%; border-color: #4ade80; color: #4ade80;">Mark Resolved (Send to Student)</button>
            </form>
            {% else %}
              <div style="color: #94a3b8; font-size: 0.9rem; text-align: center; padding: 1rem 0;">
                No actions available for current status ({{ complaint.status }}).
              </div>
            {% endif %}
          </div>"""
    
    content = content.replace(old_form, new_forms)

with open('templates/admin_complaint_detail.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated admin_complaint_detail.html")
