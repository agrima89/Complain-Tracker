import os
import sys
from datetime import date, datetime
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    send_from_directory,
    send_file
)
from flask_wtf.csrf import CSRFProtect, CSRFError
from dotenv import load_dotenv

# Load optional .env configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

import database
import pdf_generator

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# Configuration & Security
app.secret_key = os.environ.get("SECRET_KEY", "campuscare_secure_secret_key_2026_cse_project")
app.config["TEMPLATES_AUTO_RELOAD"] = True
max_mb = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 16))
app.config["MAX_CONTENT_LENGTH"] = max_mb * 1024 * 1024  # Default 16 MB
app.config["WTF_CSRF_TIME_LIMIT"] = 3600 * 6  # 6 hour CSRF token expiration

# Enable CSRF Protection across all forms & AJAX endpoints
csrf = CSRFProtect(app)

# Ensure database tables exist and migrations run on startup
database.create_database()


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """Gracefully handles CSRF token expiration with user-friendly error response."""
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "success": False,
            "message": "Security token expired or invalid. Please refresh the page and try again."
        }), 400

    flash("Your security token expired. Please try submitting the form again.", "warning")
    referrer = request.referrer or url_for("landing")
    return redirect(referrer)


# ---------------- STATIC UPLOAD ROUTE ----------------

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serves uploaded complaint evidence files securely."""
    uploads_root = os.path.join(database.BASE_DIR, "uploads")
    return send_from_directory(uploads_root, filename)


# ---------------- AUTHENTICATION DECORATORS ----------------

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("student_id"):
            flash("Please sign in with your Chandigarh University email to access this page.", "warning")
            next_target = request.full_path if request.query_string else request.path
            return redirect(url_for("student_login_view", next=next_target))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_id"):
            if session.get("student_id"):
                database.log_soc_event("UNAUTHORIZED_ACCESS", session.get("student_email"), "", "", "HIGH", "Student attempted admin access")
            flash("Please sign in as an administrator to access the admin portal.", "warning")
            return redirect(url_for("admin_login_view"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------- PUBLIC & AUTH ROUTES ----------------

@app.route("/home")
@app.route("/")
def landing():
    stats = database.get_public_statistics()
    return render_template("landing.html", stats=stats)


@app.route("/api/public-stats")
@app.route("/api/stats")
def api_public_stats():
    """Returns live database statistics for public homepage cards."""
    return jsonify({
        "success": True,
        "stats": database.get_public_statistics()
    })


@app.route("/login", methods=["GET", "POST"])
def student_login_view():
    stats = database.get_public_statistics()
    if session.get("student_id"):
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both your Chandigarh University email and password.", "error")
            return render_template("login.html", email=email, stats=stats)

        # Enforce Chandigarh University email validation
        is_valid, err_msg = database.is_valid_college_email(email)
        if not is_valid:
            flash(err_msg, "error")
            return render_template("login.html", email=email, stats=stats)

        student, auth_err = database.authenticate_student(email, password)
        if student:
            session.clear()
            session["student_id"] = student["student_id"]
            session["student_name"] = student["name"]
            session["student_email"] = student["email"]
            database.log_soc_event("LOGIN_SUCCESS", student["email"], "", "", "LOW")
            flash(f"Welcome back, {student['name']}!", "success")
            next_url = request.args.get("next") or request.form.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("student_dashboard"))
        else:
            database.log_soc_event("LOGIN_FAILED", email, "", "", "MEDIUM")
            flash(auth_err or "Invalid email or password. Please check your credentials.", "error")
            return render_template("login.html", email=email, stats=stats)

    return render_template("login.html", stats=stats)


@app.route("/register", methods=["GET", "POST"])
def student_register_view():
    if session.get("student_id"):
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html", name=name, email=email)

        if len(name) < 2 or len(name) > 100:
            flash("Full Name must be between 2 and 100 characters.", "error")
            return render_template("register.html", name=name, email=email)

        if len(password) < 4:
            flash("Password must be at least 4 characters long.", "error")
            return render_template("register.html", name=name, email=email)

        # Enforce Chandigarh University email validation
        is_valid, err_msg = database.is_valid_college_email(email)
        if not is_valid:
            flash(err_msg, "error")
            return render_template("register.html", name=name, email=email)

        success, result = database.register_new_student(name, email, password)
        if success:
            flash("Registration successful! You can now sign in with your Chandigarh University email.", "success")
            return redirect(url_for("student_login_view"))
        else:
            flash(result, "error")
            return render_template("register.html", name=name, email=email)

    return render_template("register.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login_view():
    if session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template("admin_login.html", username=username)

        admin = database.authenticate_admin(username, password)
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
            return render_template("admin_login.html", username=username)

    return render_template("admin_login.html")


@app.route("/logout")
def logout():
    user = session.get("student_email") or session.get("admin_username") or "Unknown"
    database.log_soc_event("LOGOUT", user, "", "", "LOW")
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("landing"))


# ---------------- STUDENT ROUTES ----------------

@app.route("/student/dashboard")
@student_required
def student_dashboard():
    student_id = session["student_id"]
    stats = database.get_student_statistics(student_id)
    recent_res = database.get_student_complaints_paginated(student_id, page=1, per_page=5)
    return render_template(
        "student_dashboard.html",
        stats=stats,
        recent_complaints=recent_res["items"]
    )


@app.route("/student/submit", methods=["GET", "POST"])
@app.route("/submit-complaint", methods=["GET", "POST"])
@app.route("/submit_complaint", methods=["GET", "POST"])
@student_required
def submit_complaint_view():
    student_id = session["student_id"]
    categories = database.VALID_CATEGORIES
    blocks = database.VALID_BLOCKS
    floors = ["Ground Floor", "1st Floor", "2nd Floor", "3rd Floor", "4th Floor", "5th Floor", "Basement", "Terrace / Rooftop", "Other"]
    priorities = database.VALID_PRIORITIES

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        block = request.form.get("block", "").strip() or request.form.get("location", "").strip()
        floor_no = request.form.get("floor_no", "").strip()
        room_no = request.form.get("room_no", "").strip()
        corridor_side = request.form.get("corridor_side", "").strip()
        nearby_area = request.form.get("nearby_area", "").strip()
        additional_location = request.form.get("additional_location", "").strip()
        priority = request.form.get("priority", "Medium").strip()

        # Transport Fields
        transport_type = request.form.get("transport_type", "").strip()
        bus_number = request.form.get("bus_number", "").strip()
        route = request.form.get("route", "").strip()
        pickup_drop_point = request.form.get("pickup_drop_point", "").strip()
        transport_complaint_type = request.form.get("transport_complaint_type", "").strip()

        # 1. Category validation
        if not category or category not in categories:
            flash("Please select a valid complaint category.", "error")
            return render_template("submit_complaint.html", categories=categories, blocks=blocks, floors=floors, priorities=priorities, form_data=request.form)

        # 2. Priority validation
        if priority not in priorities:
            priority = "Medium"

        # 3. Description validation
        if not description or len(description) < 5 or len(description) > 2000:
            flash("Please provide a detailed description (5 to 2000 characters).", "error")
            return render_template("submit_complaint.html", categories=categories, blocks=blocks, floors=floors, priorities=priorities, form_data=request.form)

        # 4. Mandatory Photo / Evidence Validation
        photo_file = request.files.get("photo")
        if not photo_file or not photo_file.filename:
            flash("Photo evidence is required to submit this complaint.", "error")
            return render_template("submit_complaint.html", categories=categories, blocks=blocks, floors=floors, priorities=priorities, form_data=request.form)

        # 5. Location / Transport Validation
        if category == "Transport Complaint":
            if not bus_number or not route or not pickup_drop_point or not transport_complaint_type:
                flash("Bus Number, Route, Pickup/Drop Point, and Complaint Type are required for Transport Complaints.", "error")
                return render_template("submit_complaint.html", categories=categories, blocks=blocks, floors=floors, priorities=priorities, form_data=request.form)
        else:
            if not block or block not in blocks:
                flash("Please select the campus location/block where the issue is located.", "error")
                return render_template("submit_complaint.html", categories=categories, blocks=blocks, floors=floors, priorities=priorities, form_data=request.form)

        # Save photo securely to uploads/complaints/
        photo_rel_path = database.save_complaint_image(photo_file)
        if not photo_rel_path:
            flash("Invalid file format. Please upload a genuine JPG, PNG, WEBP, or PDF file (max 16MB).", "error")
            return render_template("submit_complaint.html", categories=categories, blocks=blocks, floors=floors, priorities=priorities, form_data=request.form)

        today_str = str(date.today())
        complaint_id, ticket_id = database.create_complaint(
            student_id=student_id,
            category=category,
            description=description,
            photo_path=photo_rel_path,
            block=block,
            floor_no=floor_no,
            room_no=room_no,
            corridor_side=corridor_side,
            nearby_area=nearby_area,
            additional_location=additional_location,
            priority=priority,
            date_str=today_str,
            transport_type=transport_type,
            bus_number=bus_number,
            route=route,
            pickup_drop_point=pickup_drop_point,
            transport_complaint_type=transport_complaint_type
        )

        return render_template(
            "submit_complaint.html",
            categories=categories,
            blocks=blocks,
            floors=floors,
            priorities=priorities,
            submitted_id=complaint_id,
            ticket_id=ticket_id,
            submitted_date=today_str
        )

    # Handle pre-selected category and location from URL params
    preselected_category = request.args.get("category", "").strip()
    preselected_location = request.args.get("location", "").strip() or request.args.get("block", "").strip()
    form_data = {}

    if preselected_category in categories:
        form_data["category"] = preselected_category
    elif preselected_category:
        for cat in categories:
            if preselected_category.lower() in cat.lower():
                form_data["category"] = cat
                break

    if preselected_location:
        norm_loc = preselected_location.replace("-", " ").replace("_", " ").strip().lower()
        matched_block = None
        for b in blocks:
            if norm_loc == b.lower():
                matched_block = b
                break
        if not matched_block:
            for b in blocks:
                if norm_loc in b.lower() or b.lower() in norm_loc:
                    matched_block = b
                    break
        if matched_block:
            form_data["block"] = matched_block
        else:
            form_data["block"] = preselected_location

    return render_template(
        "submit_complaint.html",
        categories=categories,
        blocks=blocks,
        floors=floors,
        priorities=priorities,
        form_data=form_data if form_data else None
    )


@app.route("/student/complaints")
@app.route("/student/my-complaints")
@app.route("/my-complaints")
@app.route("/my_complaints")
@student_required
def my_complaints_view():
    student_id = session["student_id"]
    status_filter = request.args.get("status", "All")
    search_query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    pagination = database.get_student_complaints_paginated(
        student_id=student_id,
        status_filter=status_filter,
        search_query=search_query if search_query else None,
        page=page,
        per_page=10
    )

    return render_template(
        "my_complaints.html",
        complaints=pagination["items"],
        pagination=pagination,
        status_filter=status_filter,
        search_query=search_query
    )


@app.route("/student/complaint/<int:complaint_id>")
@student_required
def complaint_detail_view(complaint_id):
    complaint = database.get_complaint_by_id(complaint_id)
    if not complaint or complaint["student_id"] != session["student_id"]:
        flash("Complaint not found or you do not have permission to view it.", "error")
        return redirect(url_for("my_complaints_view"))

    history = database.get_complaint_history(complaint_id)
    return render_template(
        "complaint_detail.html",
        complaint=complaint,
        history=history
    )


@app.route("/student/complaint/<int:complaint_id>/download-pdf")
@app.route("/student/complaint/<int:complaint_id>/pdf")
@student_required
def student_complaint_pdf(complaint_id):
    """Generates and downloads a formal PDF dossier for the student's complaint."""
    complaint = database.get_complaint_by_id(complaint_id)
    if not complaint or complaint["student_id"] != session["student_id"]:
        flash("Complaint not found or you do not have permission to access it.", "error")
        return redirect(url_for("my_complaints_view"))

    history = database.get_complaint_history(complaint_id)
    pdf_buffer = pdf_generator.generate_complaint_pdf(complaint, history)
    filename = pdf_generator.get_pdf_filename(complaint["complaint_id"], complaint["student_name"])

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


# ---------------- ADMIN ROUTES ----------------

@app.route("/admin/dashboard")
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
    transport_stats = database.get_transport_statistics()

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        analytics=analytics,
        heatmap_data=heatmap_data,
        pulse_data=pulse_data,
        transport_stats=transport_stats,
        complaints=pagination["items"],
        pagination=pagination,
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_text=search_text,
        escalated_only=escalated_only
    )


@app.route("/admin/complaint/<int:complaint_id>")
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

    history = database.get_complaint_history(complaint_id)
    notes = database.get_admin_notes(complaint_id)
    is_escalated = database.check_is_escalated(complaint)

    return render_template(
        "admin_complaint_detail.html",
        complaint=complaint,
        history=history,
        notes=notes,
        is_escalated=is_escalated
    )


@app.route("/admin/complaint/<int:complaint_id>/note", methods=["POST"])
@admin_required
def admin_add_note_view(complaint_id):
    note_text = request.form.get("note", "").strip()
    if not note_text:
        flash("Please enter internal remarks text.", "warning")
        return redirect(url_for("admin_complaint_detail_view", complaint_id=complaint_id))

    admin_id = session.get("admin_id", 1)
    admin_name = session.get("admin_username", "Administrator")

    success, result = database.add_admin_note(complaint_id, admin_id, admin_name, note_text)
    if success:
        flash("Internal remark added successfully.", "success")
    else:
        flash(result, "error")

    return redirect(url_for("admin_complaint_detail_view", complaint_id=complaint_id))


@app.route("/admin/api/update-status", methods=["POST"])
@admin_required
def api_update_status():
    if request.is_json:
        data = request.get_json()
        complaint_id = data.get("complaint_id")
        new_status = data.get("status")
        remarks = data.get("remarks", "")
    else:
        complaint_id = request.form.get("complaint_id")
        new_status = request.form.get("status")
        remarks = request.form.get("remarks", "")

    if not complaint_id or not new_status:
        if request.is_json:
            return jsonify({"success": False, "message": "Missing required fields."}), 400
        flash("Missing required fields.", "error")
        return redirect(url_for("admin_dashboard"))

    admin_id = session.get("admin_id", 1)
    admin_name = session.get("admin_username", "Administrator")

    success, message = database.update_complaint_status(
        int(complaint_id),
        new_status,
        admin_id=admin_id,
        admin_name=admin_name,
        remarks=remarks
    )
    stats = database.get_admin_statistics()

    if request.is_json:
        return jsonify({
            "success": success,
            "message": message,
            "stats": stats
        })

    if success:
        flash(f"Complaint #{complaint_id} status updated to {new_status}.", "success")
    else:
        flash(message, "error")

    referrer = request.referrer or url_for("admin_dashboard")
    return redirect(referrer)


@app.route("/admin/api/analytics")
@admin_required
def api_analytics():
    """API endpoint providing real-time data for Chart.js dashboards."""
    return jsonify(database.get_analytics_data())


@app.route("/admin/complaint/<int:complaint_id>/download-pdf")
@app.route("/admin/complaint/<int:complaint_id>/pdf")
@admin_required
def admin_complaint_pdf(complaint_id):
    """Generates and downloads a formal individual complaint PDF for administrators."""
    complaint = database.get_complaint_by_id(complaint_id)
    if not complaint:
        flash("Complaint not found.", "error")
        return redirect(url_for("admin_dashboard"))

    history = database.get_complaint_history(complaint_id)
    pdf_buffer = pdf_generator.generate_complaint_pdf(complaint, history)
    filename = pdf_generator.get_pdf_filename(complaint["complaint_id"], complaint["student_name"])

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


@app.route("/admin/report/download-pdf")
@app.route("/admin/report/pdf")
@admin_required
def admin_summary_report_pdf():
    """Generates and downloads comprehensive admin grievance summary report PDF with analytics."""
    status_filter = request.args.get("status", "All")
    priority_filter = request.args.get("priority", "All")
    search_text = request.args.get("q", "").strip()

    stats = database.get_admin_statistics()
    analytics = database.get_analytics_data()
    complaints = database.get_all_complaints_for_report(
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_text=search_text
    )

    admin_name = session.get("admin_username", "Administrator")
    pdf_buffer = pdf_generator.generate_admin_summary_pdf(
        stats=stats,
        category_stats=analytics["by_category"],
        priority_stats=analytics["by_priority"],
        complaints_list=complaints,
        admin_name=admin_name
    )
    filename = pdf_generator.get_summary_pdf_filename()

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


# ---------------- SMART INTELLIGENCE & HEATMAP APIS ----------------

@app.route("/api/smart-detect", methods=["POST"])
@csrf.exempt
def api_smart_detect():
    """
    Analyzes student complaint description in real-time and provides
    intelligent suggestions for Category, Priority, Location, and Reason.
    """
    if request.is_json:
        data = request.get_json() or {}
        text = data.get("text", "").strip()
    else:
        text = request.form.get("text", "").strip()

    if not text or len(text) < 4:
        return jsonify({
            "success": False,
            "message": "Text too short for analysis"
        })

    analysis = smart_complaint.analyze_complaint(text)
    return jsonify(analysis)


@app.route("/api/check-similar", methods=["POST"])
@csrf.exempt
def api_check_similar():
    """
    Checks if a complaint is similar or duplicate to existing unresolved complaints.
    """
    if request.is_json:
        data = request.get_json() or {}
        description = data.get("description", "").strip()
        category = data.get("category", "")
        block = data.get("block", "")
    else:
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        block = request.form.get("block", "")

    result = smart_complaint.find_similar_complaints(
        description=description,
        category=category,
        block=block
    )
    return jsonify(result)


@app.route("/api/admin/heatmap")
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
    })


@app.route("/api/admin/zone/<zone_id>")
@app.route("/api/admin/zone-complaints/<zone_id>")
@admin_required
def api_admin_zone_detail(zone_id):
    """Returns real-time complaints and telemetry for a specific campus zone."""
    zones = database.get_campus_heatmap_data()
    target_zone = None
    for z in zones:
        if z["id"] == zone_id or z["zone_key"].lower() == zone_id.lower() or z["name"].lower() == zone_id.lower():
            target_zone = z
            break
    if not target_zone:
        return jsonify({"success": False, "message": f"Zone '{zone_id}' not found."}), 404
    return jsonify({
        "success": True,
        "zone": target_zone
    })


@app.route("/api/admin/pulse")
@admin_required
def api_admin_pulse():
    """Returns real-time Campus Pulse executive telemetry."""
    return jsonify({
        "success": True,
        "pulse": database.get_campus_pulse_data()
    })


# ---------------- PROFILE VIEW ----------------

@app.route("/student/profile")
@app.route("/profile")
def profile_view():
    if session.get("student_id"):
        student_id = session["student_id"]
        stats = database.get_student_statistics(student_id)
        return render_template("profile.html", role="student", stats=stats)
    elif session.get("admin_id"):
        stats = database.get_admin_statistics()
        return render_template("profile.html", role="admin", stats=stats)
    else:
        return redirect(url_for("student_login_view"))




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

if __name__ == "__main__":
    app.run(debug=True, port=5000)
