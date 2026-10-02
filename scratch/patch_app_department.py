import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_FILE = os.path.join(BASE_DIR, "app.py")

with open(APP_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update admin_dashboard
old_admin_dashboard = '''@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    department = session.get("admin_department") if session.get("admin_role") == "HOD" else None
    stats = database.get_admin_statistics(department)
    analytics = database.get_analytics_data()
    status_filter = request.args.get("status", "All")
    priority_filter = request.args.get("priority", "All")
    search_text = request.args.get("q", "").strip()
    escalated_only = request.args.get("escalated", "false").lower() == "true"
    page = request.args.get("page", 1, type=int)

    pagination = database.get_all_complaints_admin_paginated(
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_text=search_text,
        escalated_only=escalated_only,
        page=page,
        per_page=10,
        department=department
    )

    # Attach is_escalated indicator to complaint rows
    complaints_list = []
    for c in pagination["items"]:
        c_dict = dict(c)
        c_dict["is_escalated"] = database.check_is_escalated(c)
        complaints_list.append(c_dict)

    pagination["items"] = complaints_list
    heatmap_data = database.get_campus_heatmap_data()
    pulse_data = database.get_campus_pulse_data()
    transport_stats = database.get_transport_statistics()'''

new_admin_dashboard = '''@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    department = session.get("admin_department") if session.get("admin_role") != "Super Admin" and session.get("admin_department") else None
    stats = database.get_admin_statistics(department)
    analytics = database.get_analytics_data(department)
    status_filter = request.args.get("status", "All")
    priority_filter = request.args.get("priority", "All")
    search_text = request.args.get("q", "").strip()
    escalated_only = request.args.get("escalated", "false").lower() == "true"
    page = request.args.get("page", 1, type=int)

    pagination = database.get_all_complaints_admin_paginated(
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_text=search_text,
        escalated_only=escalated_only,
        page=page,
        per_page=10,
        department=department
    )

    # Attach is_escalated indicator to complaint rows
    complaints_list = []
    for c in pagination["items"]:
        c_dict = dict(c)
        c_dict["is_escalated"] = database.check_is_escalated(c)
        complaints_list.append(c_dict)

    pagination["items"] = complaints_list
    heatmap_data = database.get_campus_heatmap_data(department)
    pulse_data = database.get_campus_pulse_data(department)
    transport_stats = database.get_transport_statistics() if (not department or department == "Transport") else {"total": 0, "active": 0, "resolved": 0, "by_type": {}, "by_route": {}}'''

if old_admin_dashboard in content:
    content = content.replace(old_admin_dashboard, new_admin_dashboard, 1)
    print("1. Updated admin_dashboard scoping")
else:
    print("WARNING: Could not find old_admin_dashboard")

# 2. Update admin_complaint_detail_view
old_detail_check = '''    if session.get("admin_role") == "HOD" and complaint["department"] != session.get("admin_department"):
        database.log_soc_event("UNAUTHORIZED_ACCESS", session.get("admin_username"), complaint_id, session.get("admin_department"), "HIGH", f"HOD attempted to access complaint in {complaint['department']}")
        flash("Access Denied: You can only view complaints assigned to your department.", "error")
        return redirect(url_for("admin_dashboard"))'''

new_detail_check = '''    if session.get("admin_role") != "Super Admin" and session.get("admin_department") and complaint["department"] != session.get("admin_department"):
        database.log_soc_event("UNAUTHORIZED_ACCESS", session.get("admin_username"), complaint_id, session.get("admin_department"), "HIGH", f"Department {session.get('admin_department')} admin attempted to access complaint in {complaint['department']}")
        flash("Access Denied: You can only view complaints assigned to your department.", "error")
        return redirect(url_for("admin_dashboard"))'''

if old_detail_check in content:
    content = content.replace(old_detail_check, new_detail_check, 1)
    print("2. Updated admin_complaint_detail_view access check")
else:
    print("WARNING: Could not find old_detail_check")

# 3. Update admin_add_note_view
old_note = '''    admin_id = session.get("admin_id", 1)
    admin_name = session.get("admin_username", "Administrator")

    success, result = database.add_admin_note(complaint_id, admin_id, admin_name, note_text)'''

new_note = '''    comp = database.get_complaint_by_id(complaint_id)
    if not comp:
        flash("Complaint not found.", "error")
        return redirect(url_for("admin_dashboard"))

    if session.get("admin_role") != "Super Admin" and session.get("admin_department") and comp["department"] != session.get("admin_department"):
        database.log_soc_event("UNAUTHORIZED_ACCESS", session.get("admin_username"), complaint_id, session.get("admin_department"), "HIGH", "Attempted to add note on unauthorized complaint")
        flash("Access Denied: You can only add remarks to complaints assigned to your department.", "error")
        return redirect(url_for("admin_dashboard"))

    admin_id = session.get("admin_id", 1)
    admin_name = session.get("admin_username", "Administrator")

    success, result = database.add_admin_note(complaint_id, admin_id, admin_name, note_text)'''

if old_note in content:
    content = content.replace(old_note, new_note, 1)
    print("3. Updated admin_add_note_view with authorization check")
else:
    print("WARNING: Could not find old_note")

# 4. Update api_update_status authorization check & stats scoping
old_status_check = '''    old_status = comp["status"]
    allowed_transitions = {'''

new_status_check = '''    if session.get("admin_role") != "Super Admin" and session.get("admin_department") and comp["department"] != session.get("admin_department"):
        database.log_soc_event("UNAUTHORIZED_ACCESS", session.get("admin_username"), complaint_id, session.get("admin_department"), "HIGH", "Attempted status update on unauthorized complaint")
        msg = "Access Denied: You can only update complaints assigned to your department."
        if request.is_json:
            return jsonify({"success": False, "message": msg}), 403
        flash(msg, "error")
        return redirect(url_for("admin_dashboard"))

    old_status = comp["status"]
    allowed_transitions = {'''

if old_status_check in content:
    content = content.replace(old_status_check, new_status_check, 1)
    print("4a. Updated api_update_status authorization check")
else:
    print("WARNING: Could not find old_status_check")

old_status_stats = '''    success, message = database.update_complaint_status(
        int(complaint_id),
        new_status,
        admin_id=admin_id,
        admin_name=admin_name,
        remarks=remarks
    )
    stats = database.get_admin_statistics()'''

new_status_stats = '''    success, message = database.update_complaint_status(
        int(complaint_id),
        new_status,
        admin_id=admin_id,
        admin_name=admin_name,
        remarks=remarks
    )
    dept = session.get("admin_department") if session.get("admin_role") != "Super Admin" and session.get("admin_department") else None
    stats = database.get_admin_statistics(dept)'''

if old_status_stats in content:
    content = content.replace(old_status_stats, new_status_stats, 1)
    print("4b. Updated api_update_status scoped stats return")
else:
    print("WARNING: Could not find old_status_stats")

# 5. Update api_analytics
old_api_analytics = '''@app.route("/admin/api/analytics")
@admin_required
def api_analytics():
    """API endpoint providing real-time data for Chart.js dashboards."""
    return jsonify(database.get_analytics_data())'''

new_api_analytics = '''@app.route("/admin/api/analytics")
@admin_required
def api_analytics():
    """API endpoint providing real-time data for Chart.js dashboards."""
    dept = session.get("admin_department") if session.get("admin_role") != "Super Admin" and session.get("admin_department") else None
    return jsonify(database.get_analytics_data(department=dept))'''

if old_api_analytics in content:
    content = content.replace(old_api_analytics, new_api_analytics, 1)
    print("5. Updated api_analytics endpoint scoping")
else:
    print("WARNING: Could not find old_api_analytics")

# 6. Update admin_complaint_pdf
old_comp_pdf = '''@app.route("/admin/complaint/<int:complaint_id>/download-pdf")
@app.route("/admin/complaint/<int:complaint_id>/pdf")
@admin_required
def admin_complaint_pdf(complaint_id):
    """Generates and downloads a formal individual complaint PDF for administrators."""
    complaint = database.get_complaint_by_id(complaint_id)
    if not complaint:
        flash("Complaint not found.", "error")
        return redirect(url_for("admin_dashboard"))

    history = database.get_complaint_history(complaint_id)'''

new_comp_pdf = '''@app.route("/admin/complaint/<int:complaint_id>/download-pdf")
@app.route("/admin/complaint/<int:complaint_id>/pdf")
@admin_required
def admin_complaint_pdf(complaint_id):
    """Generates and downloads a formal individual complaint PDF for administrators."""
    complaint = database.get_complaint_by_id(complaint_id)
    if not complaint:
        flash("Complaint not found.", "error")
        return redirect(url_for("admin_dashboard"))

    if session.get("admin_role") != "Super Admin" and session.get("admin_department") and complaint["department"] != session.get("admin_department"):
        database.log_soc_event("UNAUTHORIZED_ACCESS", session.get("admin_username"), complaint_id, session.get("admin_department"), "HIGH", "Attempted PDF download on unauthorized complaint")
        flash("Access Denied: You can only access complaints assigned to your department.", "error")
        return redirect(url_for("admin_dashboard"))

    history = database.get_complaint_history(complaint_id)'''

if old_comp_pdf in content:
    content = content.replace(old_comp_pdf, new_comp_pdf, 1)
    print("6. Updated admin_complaint_pdf with authorization check")
else:
    print("WARNING: Could not find old_comp_pdf")

# 7. Update admin_summary_report_pdf
old_sum_pdf = '''    stats = database.get_admin_statistics()
    analytics = database.get_analytics_data()
    complaints = database.get_all_complaints_for_report(
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_text=search_text
    )'''

new_sum_pdf = '''    dept = session.get("admin_department") if session.get("admin_role") != "Super Admin" and session.get("admin_department") else None
    stats = database.get_admin_statistics(dept)
    analytics = database.get_analytics_data(dept)
    complaints = database.get_all_complaints_for_report(
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_text=search_text,
        department=dept
    )'''

if old_sum_pdf in content:
    content = content.replace(old_sum_pdf, new_sum_pdf, 1)
    print("7. Updated admin_summary_report_pdf with department scoping")
else:
    print("WARNING: Could not find old_sum_pdf")

# 8. Update heatmap and pulse endpoints
old_api_heatmap = '''@app.route("/api/admin/heatmap")
@app.route("/api/admin/zone-telemetry")
@app.route("/admin/api/zone-telemetry")
@admin_required
def api_admin_heatmap():
    """Returns real-time campus problem heatmap zone telemetry."""
    zones = database.get_campus_heatmap_data()
    return jsonify({
        "success": True,
        "zones": zones,
        "total_zones": len(zones)
    })'''

new_api_heatmap = '''@app.route("/api/admin/heatmap")
@app.route("/api/admin/zone-telemetry")
@app.route("/admin/api/zone-telemetry")
@admin_required
def api_admin_heatmap():
    """Returns real-time campus problem heatmap zone telemetry."""
    dept = session.get("admin_department") if session.get("admin_role") != "Super Admin" and session.get("admin_department") else None
    zones = database.get_campus_heatmap_data(department=dept)
    return jsonify({
        "success": True,
        "zones": zones,
        "total_zones": len(zones)
    })'''

if old_api_heatmap in content:
    content = content.replace(old_api_heatmap, new_api_heatmap, 1)
    print("8a. Updated api_admin_heatmap scoping")
else:
    print("WARNING: Could not find old_api_heatmap")

old_api_pulse = '''@app.route("/api/admin/pulse")
@admin_required
def api_admin_pulse():
    """Returns real-time Campus Pulse executive telemetry."""
    return jsonify({
        "success": True,
        "pulse": database.get_campus_pulse_data()
    })'''

new_api_pulse = '''@app.route("/api/admin/pulse")
@admin_required
def api_admin_pulse():
    """Returns real-time Campus Pulse executive telemetry."""
    dept = session.get("admin_department") if session.get("admin_role") != "Super Admin" and session.get("admin_department") else None
    return jsonify({
        "success": True,
        "pulse": database.get_campus_pulse_data(department=dept)
    })'''

if old_api_pulse in content:
    content = content.replace(old_api_pulse, new_api_pulse, 1)
    print("8b. Updated api_admin_pulse scoping")
else:
    print("WARNING: Could not find old_api_pulse")

# 9. Update forward and mark resolved checks
old_fwd_check = '''    if session.get("admin_role") == "HOD" and comp["department"] != session.get("admin_department"):'''
new_fwd_check = '''    if session.get("admin_role") != "Super Admin" and session.get("admin_department") and comp["department"] != session.get("admin_department"):'''

if old_fwd_check in content:
    content = content.replace(old_fwd_check, new_fwd_check)
    print("9. Updated forward and mark resolved authorization checks")
else:
    print("WARNING: Could not find old_fwd_check")

with open(APP_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("app.py successfully patched!")
