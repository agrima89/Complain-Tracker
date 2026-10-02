import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update admin_required
old_admin_required = """def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please sign in as an administrator to access the admin portal.", "warning")
            return redirect(url_for("admin_login_view"))
        return f(*args, **kwargs)
    return decorated_function"""
new_admin_required = """def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_id"):
            if session.get("student_id"):
                database.log_soc_event("UNAUTHORIZED_ACCESS", session.get("student_email"), "", "", "HIGH", "Student attempted admin access")
            flash("Please sign in as an administrator to access the admin portal.", "warning")
            return redirect(url_for("admin_login_view"))
        return f(*args, **kwargs)
    return decorated_function"""
content = content.replace(old_admin_required, new_admin_required)

# 2. Update admin login
old_admin_login = """        admin = database.authenticate_admin(username, password)
        if admin:
            session.clear()
            session["admin_id"] = admin["admin_id"]
            session["admin_username"] = admin["username"]
            flash("Logged in successfully as Administrator.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin username or password.", "error")
            return render_template("admin_login.html", username=username)"""
new_admin_login = """        admin = database.authenticate_admin(username, password)
        if admin:
            session.clear()
            session["admin_id"] = admin["admin_id"]
            session["admin_username"] = admin["username"]
            session["admin_role"] = admin["role"]
            session["admin_department"] = admin["department"]
            database.log_soc_event("LOGIN_SUCCESS", admin["username"], "", admin["department"], "LOW")
            flash("Logged in successfully as Administrator.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            database.log_soc_event("LOGIN_FAILED", username, "", "", "MEDIUM")
            flash("Invalid admin username or password.", "error")
            return render_template("admin_login.html", username=username)"""
content = content.replace(old_admin_login, new_admin_login)

# 3. Update student login success (just to log)
old_student_login = """        student, auth_err = database.authenticate_student(email, password)
        if student:
            session.clear()
            session["student_id"] = student["student_id"]
            session["student_name"] = student["name"]
            session["student_email"] = student["email"]
            flash(f"Welcome back, {student['name']}!", "success")"""
new_student_login = """        student, auth_err = database.authenticate_student(email, password)
        if student:
            session.clear()
            session["student_id"] = student["student_id"]
            session["student_name"] = student["name"]
            session["student_email"] = student["email"]
            database.log_soc_event("LOGIN_SUCCESS", student["email"], "", "", "LOW")
            flash(f"Welcome back, {student['name']}!", "success")"""
content = content.replace(old_student_login, new_student_login)

# 4. Update student login fail
old_student_login_fail = """        else:
            flash(auth_err or "Invalid email or password. Please check your credentials.", "error")
            return render_template("login.html", email=email, stats=stats)"""
new_student_login_fail = """        else:
            database.log_soc_event("LOGIN_FAILED", email, "", "", "MEDIUM")
            flash(auth_err or "Invalid email or password. Please check your credentials.", "error")
            return render_template("login.html", email=email, stats=stats)"""
content = content.replace(old_student_login_fail, new_student_login_fail)

# 5. Update logout to log
old_logout = """@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("landing"))"""
new_logout = """@app.route("/logout")
def logout():
    user = session.get("student_email") or session.get("admin_username") or "Unknown"
    database.log_soc_event("LOGOUT", user, "", "", "LOW")
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("landing"))"""
content = content.replace(old_logout, new_logout)


# 6. Update admin_dashboard route to filter by department
old_admin_dashboard = """@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    stats = database.get_admin_statistics()
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
        per_page=10
    )"""
new_admin_dashboard = """@app.route("/admin/dashboard")
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
    )"""
content = content.replace(old_admin_dashboard, new_admin_dashboard)


# 7. Update admin_complaint_detail_view for HOD authorization
old_admin_detail = """@app.route("/admin/complaint/<int:complaint_id>")
@admin_required
def admin_complaint_detail_view(complaint_id):
    complaint = database.get_complaint_by_id(complaint_id)
    if not complaint:
        flash("Complaint not found.", "error")
        return redirect(url_for("admin_dashboard"))

    history = database.get_complaint_history(complaint_id)"""
new_admin_detail = """@app.route("/admin/complaint/<int:complaint_id>")
@admin_required
def admin_complaint_detail_view(complaint_id):
    complaint = database.get_complaint_by_id(complaint_id)
    if not complaint:
        flash("Complaint not found.", "error")
        return redirect(url_for("admin_dashboard"))
        
    if session.get("admin_role") == "HOD" and complaint["department"] != session.get("admin_department"):
        database.log_soc_event("UNAUTHORIZED_ACCESS", session.get("admin_username"), complaint_id, session.get("admin_department"), "HIGH", f"HOD attempted to access complaint in {complaint['department']}")
        flash("Access Denied: You can only view complaints assigned to your department.", "error")
        return redirect(url_for("admin_dashboard"))

    history = database.get_complaint_history(complaint_id)"""
content = content.replace(old_admin_detail, new_admin_detail)


# Add new endpoints at the end of the file
new_endpoints = """

# --- NEW API ENDPOINTS FOR COMPLAINT WORKFLOW ---
@app.route("/admin/api/forward-complaint", methods=["POST"])
@admin_required
def api_forward_complaint():
    complaint_id = request.form.get("complaint_id")
    department = request.form.get("department")
    reason = request.form.get("reason", "")
    
    if not complaint_id or not department:
        flash("Missing required fields.", "error")
        return redirect(url_for("admin_dashboard"))
        
    # Check authorization
    comp = database.get_complaint_by_id(complaint_id)
    if session.get("admin_role") == "HOD" and comp["department"] != session.get("admin_department"):
        database.log_soc_event("UNAUTHORIZED_ACCESS", session.get("admin_username"), complaint_id, session.get("admin_department"), "HIGH")
        flash("Access Denied.", "error")
        return redirect(url_for("admin_dashboard"))

    admin_id = session.get("admin_id")
    admin_name = session.get("admin_username")
    
    success, msg = database.forward_complaint(complaint_id, department, admin_name, admin_id, reason)
    database.log_soc_event("COMPLAINT_FORWARDED", admin_name, complaint_id, department, "LOW", reason)
    flash(msg, "success" if success else "error")
    return redirect(url_for("admin_complaint_detail_view", complaint_id=complaint_id))


@app.route("/admin/api/mark-resolved", methods=["POST"])
@admin_required
def api_mark_resolved():
    complaint_id = request.form.get("complaint_id")
    remarks = request.form.get("remarks", "")
    
    comp = database.get_complaint_by_id(complaint_id)
    if session.get("admin_role") == "HOD" and comp["department"] != session.get("admin_department"):
        database.log_soc_event("UNAUTHORIZED_ACCESS", session.get("admin_username"), complaint_id, session.get("admin_department"), "HIGH")
        flash("Access Denied.", "error")
        return redirect(url_for("admin_dashboard"))

    admin_id = session.get("admin_id")
    admin_name = session.get("admin_username")
    
    success, msg = database.mark_resolved_by_department(complaint_id, admin_name, admin_id, remarks)
    database.log_soc_event("COMPLAINT_STATUS_CHANGED", admin_name, complaint_id, comp["department"], "LOW", "Resolved by Department")
    flash(msg, "success" if success else "error")
    return redirect(url_for("admin_complaint_detail_view", complaint_id=complaint_id))


@app.route("/student/api/confirm-resolution", methods=["POST"])
@student_required
def api_confirm_resolution():
    complaint_id = request.form.get("complaint_id")
    student_id = session.get("student_id")
    
    success, msg = database.confirm_resolution(complaint_id, student_id)
    database.log_soc_event("COMPLAINT_STATUS_CHANGED", session.get("student_email"), complaint_id, "", "LOW", "FINAL_RESOLVED")
    flash("Resolution confirmed successfully.", "success" if success else "error")
    return redirect(url_for("complaint_detail_view", complaint_id=complaint_id))


@app.route("/student/api/regenerate", methods=["POST"])
@student_required
def api_regenerate_complaint():
    complaint_id = request.form.get("complaint_id")
    reason = request.form.get("reason", "")
    student_id = session.get("student_id")
    
    # Process optional new photo
    photo_file = request.files.get("photo")
    photo_rel_path = ""
    if photo_file and photo_file.filename:
        photo_rel_path = database.save_complaint_image(photo_file)
        
    success, msg = database.regenerate_complaint(complaint_id, student_id, reason, photo_rel_path)
    database.log_soc_event("COMPLAINT_REGENERATED", session.get("student_email"), complaint_id, "", "MEDIUM", reason)
    flash("Complaint regenerated and sent back to department.", "success" if success else "error")
    return redirect(url_for("complaint_detail_view", complaint_id=complaint_id))

@app.route("/admin/soc")
@admin_required
def soc_dashboard():
    if session.get("admin_role") == "HOD":
        database.log_soc_event("UNAUTHORIZED_ACCESS", session.get("admin_username"), "", session.get("admin_department"), "HIGH", "HOD attempted SOC access")
        flash("Access Denied: SOC Dashboard is restricted to Super Admins.", "error")
        return redirect(url_for("admin_dashboard"))
        
    conn = database.get_db_connection()
    logs = conn.execute("SELECT * FROM soc_audit_logs ORDER BY timestamp DESC LIMIT 100").fetchall()
    
    total = conn.execute("SELECT COUNT(*) FROM soc_audit_logs").fetchone()[0]
    failed_logins = conn.execute("SELECT COUNT(*) FROM soc_audit_logs WHERE event_type = 'LOGIN_FAILED'").fetchone()[0]
    unauthorized = conn.execute("SELECT COUNT(*) FROM soc_audit_logs WHERE event_type = 'UNAUTHORIZED_ACCESS'").fetchone()[0]
    high_severity = conn.execute("SELECT COUNT(*) FROM soc_audit_logs WHERE severity = 'HIGH'").fetchone()[0]
    conn.close()
    
    return render_template("soc_dashboard.html", logs=logs, total=total, failed_logins=failed_logins, unauthorized=unauthorized, high_severity=high_severity)
"""
if 'api_forward_complaint' not in content:
    content = content.replace('if __name__ == "__main__":', new_endpoints + '\nif __name__ == "__main__":')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py successfully.")
