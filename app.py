import os
from datetime import date
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)
import database

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "campuscare_secure_secret_key_2026_cse_project")
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure database tables exist on startup
database.create_database()


# ---------------- AUTHENTICATION DECORATORS ----------------

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("student_id"):
            flash("Please sign in as a student to access this page.", "warning")
            return redirect(url_for("student_login_view"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please sign in as an administrator to access the admin portal.", "warning")
            return redirect(url_for("admin_login_view"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------- PUBLIC & AUTH ROUTES ----------------

@app.route("/")
def landing():
    # If already logged in, redirect to respective dashboard
    if session.get("student_id"):
        return redirect(url_for("student_dashboard"))
    elif session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))
    return render_template("landing.html")


@app.route("/login", methods=["GET", "POST"])
def student_login_view():
    if session.get("student_id"):
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html", email=email)

        student = database.authenticate_student(email, password)
        if student:
            session.clear()
            session["student_id"] = student["student_id"]
            session["student_name"] = student["name"]
            session["student_email"] = student["email"]
            flash(f"Welcome back, {student['name']}!", "success")
            return redirect(url_for("student_dashboard"))
        else:
            flash("Invalid email or password. Please check your credentials.", "error")
            return render_template("login.html", email=email)

    return render_template("login.html")


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

        if len(password) < 4:
            flash("Password must be at least 4 characters long.", "error")
            return render_template("register.html", name=name, email=email)

        success, result = database.register_new_student(name, email, password)
        if success:
            flash("Registration successful! You can now log in.", "success")
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
            flash("Logged in successfully as Administrator.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin username or password.", "error")
            return render_template("admin_login.html", username=username)

    return render_template("admin_login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("landing"))


# ---------------- STUDENT ROUTES ----------------

@app.route("/student/dashboard")
@student_required
def student_dashboard():
    student_id = session["student_id"]
    stats = database.get_student_statistics(student_id)
    recent_complaints = database.get_student_complaints(student_id)[:5]
    return render_template(
        "student_dashboard.html",
        stats=stats,
        recent_complaints=recent_complaints
    )


@app.route("/student/submit", methods=["GET", "POST"])
@student_required
def submit_complaint_view():
    student_id = session["student_id"]
    categories = [
        "Electrical", "Cleaning", "Classroom", "Hostel",
        "Wi-Fi/Internet", "Library", "Infrastructure", "Other"
    ]
    priorities = ["Low", "Medium", "High"]

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        priority = request.form.get("priority", "Medium").strip()

        if not category or category not in categories:
            flash("Please select a valid complaint category.", "error")
            return render_template("submit_complaint.html", categories=categories, priorities=priorities, form_data=request.form)

        if not description:
            flash("Please provide a detailed description of the issue.", "error")
            return render_template("submit_complaint.html", categories=categories, priorities=priorities, form_data=request.form)

        if not location:
            flash("Please enter the specific location on campus.", "error")
            return render_template("submit_complaint.html", categories=categories, priorities=priorities, form_data=request.form)

        today_str = str(date.today())
        complaint_id = database.create_complaint(
            student_id=student_id,
            category=category,
            description=description,
            location=location,
            priority=priority,
            date_str=today_str
        )

        return render_template(
            "submit_complaint.html",
            categories=categories,
            priorities=priorities,
            submitted_id=complaint_id,
            submitted_date=today_str
        )

    # Handle pre-selected category from URL param (e.g. /student/submit?category=Wi-Fi/Internet)
    preselected_category = request.args.get("category", "").strip()
    form_data = {}
    if preselected_category in categories:
        form_data["category"] = preselected_category
    elif preselected_category:
        # Check for fuzzy match
        for cat in categories:
            if preselected_category.lower() in cat.lower():
                form_data["category"] = cat
                break

    return render_template("submit_complaint.html", categories=categories, priorities=priorities, form_data=form_data if form_data else None)


@app.route("/student/complaints")
@student_required
def my_complaints_view():
    student_id = session["student_id"]
    status_filter = request.args.get("status", "All")
    search_query = request.args.get("q", "").strip()

    complaints = database.get_student_complaints(
        student_id=student_id,
        status_filter=status_filter,
        search_query=search_query if search_query else None
    )
    return render_template(
        "my_complaints.html",
        complaints=complaints,
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

    return render_template("complaint_detail.html", complaint=complaint)


# ---------------- ADMIN ROUTES ----------------

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    stats = database.get_admin_statistics()
    status_filter = request.args.get("status", "All")
    priority_filter = request.args.get("priority", "All")
    search_text = request.args.get("q", "").strip()

    complaints = database.get_all_complaints_admin(
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_text=search_text
    )

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        complaints=complaints,
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_text=search_text
    )


@app.route("/admin/complaint/<int:complaint_id>")
@admin_required
def admin_complaint_detail_view(complaint_id):
    complaint = database.get_complaint_by_id(complaint_id)
    if not complaint:
        flash("Complaint not found.", "error")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_complaint_detail.html", complaint=complaint)


@app.route("/admin/api/update-status", methods=["POST"])
@admin_required
def api_update_status():
    if request.is_json:
        data = request.get_json()
        complaint_id = data.get("complaint_id")
        new_status = data.get("status")
    else:
        complaint_id = request.form.get("complaint_id")
        new_status = request.form.get("status")

    if not complaint_id or not new_status:
        if request.is_json:
            return jsonify({"success": False, "message": "Missing required fields."}), 400
        flash("Missing required fields.", "error")
        return redirect(url_for("admin_dashboard"))

    success, message = database.update_complaint_status(int(complaint_id), new_status)
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

    return redirect(url_for("admin_dashboard"))


# ---------------- PROFILE VIEW ----------------

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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
