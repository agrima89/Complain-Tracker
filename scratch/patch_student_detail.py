import re

with open('templates/complaint_detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_student_actions = """        </div>
      </div>
      
      {% if complaint.status == 'AWAITING_STUDENT_CONFIRMATION' %}
      <div style="background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 12px; padding: 1.5rem; margin-top: 1.5rem;">
        <h3 style="font-size: 1.05rem; font-weight: 600; color: #e2e8f0; margin-bottom: 1rem;">Confirm Resolution</h3>
        <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.5rem;">The department has marked this complaint as resolved. Please confirm if the issue is completely fixed, or regenerate the ticket if it still persists.</p>
        
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
            <form action="{{ url_for('api_confirm_resolution') }}" method="POST" style="flex: 1;">
              <input type="hidden" name="complaint_id" value="{{ complaint.complaint_id }}">
              <button type="submit" class="btn btn-primary" style="width: 100%; background: #22c55e; border-color: #22c55e; color: #000;">
                ✓ Confirm Resolved
              </button>
            </form>
            
            <button onclick="document.getElementById('regenerateForm').style.display='block'" class="btn btn-secondary" style="flex: 1; border-color: #f43f5e; color: #f43f5e;">
              🔄 No, It's Not Fixed
            </button>
        </div>
        
        <form id="regenerateForm" action="{{ url_for('api_regenerate_complaint') }}" method="POST" enctype="multipart/form-data" style="display: none; margin-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 1.5rem;">
            <h4 style="font-size: 1rem; font-weight: 600; color: #f43f5e; margin-bottom: 1rem;">Regenerate Ticket</h4>
            <input type="hidden" name="complaint_id" value="{{ complaint.complaint_id }}">
            <div class="form-group" style="margin-bottom: 1rem;">
                <label style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.4rem; display: block;">Reason it's not fixed</label>
                <textarea name="reason" class="form-control" rows="2" placeholder="Explain what is still wrong..." required style="width: 100%; padding: 0.6rem; border-radius: 6px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.2); color: #fff;"></textarea>
            </div>
            <div class="form-group" style="margin-bottom: 1rem;">
                <label style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.4rem; display: block;">Upload New Photo (Optional)</label>
                <input type="file" name="photo" class="form-control" accept="image/*" style="width: 100%; padding: 0.6rem; border-radius: 6px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.2); color: #fff;">
            </div>
            <button type="submit" class="btn btn-secondary" style="width: 100%; border-color: #f43f5e; color: #f43f5e;">Send Back to Department</button>
        </form>
      </div>
      {% endif %}"""

content = re.sub(r'\s*</div>\s*</div>\s*<!-- Main Content Area -->', new_student_actions + '\n\n    <!-- Main Content Area -->', content)

with open('templates/complaint_detail.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated complaint_detail.html")
