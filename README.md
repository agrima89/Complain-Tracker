# 🏫 Student Complaint & Solution Tracker (SCST)

A modern, full-stack, responsive web application designed for university and college campuses to manage, track, and resolve student grievances transparently and efficiently.

Built with **Python (Flask)**, **SQLite3**, **HTML5**, **Modular CSS3**, and **Vanilla JavaScript**.

---

## 🌟 Key Features

### 👨‍🎓 Student Portal
- **Student Registration & Authentication**: Secure sign-up and login with password visibility toggling and validation.
- **Interactive Dashboard**: Real-time personal statistics (Total, Pending, In Progress, Resolved) and quick-access cards.
- **Complaint Lodging**: Form supporting 8 categories (`Electrical`, `Cleaning`, `Classroom`, `Hostel`, `Wi-Fi/Internet`, `Library`, `Infrastructure`, `Other`), campus location hints, priority selection (`Low`, `Medium`, `High`), and live character count.
- **Instant Ticket Generation**: Interactive confirmation screen with unique ticket ID (`#00X`).
- **Live Complaint Tracking**: Searchable and filterable history table.
- **3-Stage Progress Timeline**: Visual lifecycle tracker (**Submitted** &rarr; **In Progress** &rarr; **Resolved**).
- **User Profile**: Account details and activity metrics.

### 🛡️ Administrator Management Portal
- **Secure Admin Gateway**: Dedicated login with role-based access control.
- **Analytics & Metric Cards**: Live counters dynamically computed from the SQLite database.
- **Multi-Parameter Search & Filter Toolbar**: Full-text search across student names, emails, categories, descriptions, locations, and ticket IDs with status and priority filters.
- **In-Place Status Updates (AJAX)**: One-click status updates directly from the table without full page reloads.
- **Detailed Grievance Inspection**: Complete report view with student contact details and lifecycle status controller.

---

## 🏗️ System Architecture & Technologies

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | **Flask (Python 3.x)** | Lightweight WSGI web framework, session management, and RESTful API endpoints. |
| **Database** | **SQLite3** | Embedded relational database with foreign key constraints and parameterized queries. |
| **Frontend Templates**| **Jinja2 (HTML5)** | Semantic server-rendered views with modular template inheritance (`base.html`). |
| **Styling & UI** | **Vanilla CSS3** | Custom design system (`Inter` typography, CSS variables, flexbox, CSS grid, micro-animations). |
| **Client Scripting** | **Vanilla JavaScript** | Asynchronous AJAX status updates, live validation, mobile navigation drawer, and toast alerts. |

---

## 📂 Project Structure

```
College_Complaint_Tracker/
├── app.py                      # Main Flask application with routes and API handlers
├── database.py                 # Centralized SQLite query layer & schema definitions
├── database.db                 # SQLite database storage (Students, Complaints, Admins)
├── run_app.py                  # One-click server launcher with browser auto-open
├── requirements.txt            # Python dependencies (Flask >= 3.0.0)
│
├── static/
│   ├── css/
│   │   ├── style.css           # Design tokens, CSS variables, typography, and base layout
│   │   ├── components.css      # Badges, buttons, cards, toasts, modals, 3-stage timeline
│   │   ├── forms.css           # Form controls, password visibility toggles, char counter
│   │   └── dashboard.css       # Responsive stats cards, quick action grids, tables, and filter bar
│   └── js/
│       ├── main.js             # Toast manager, mobile navigation drawer, modal controller
│       ├── student.js          # Live complaint form validation and character counter
│       └── admin.js            # AJAX in-place status updater & live dashboard metric sync
│
└── templates/
    ├── base.html               # Master layout with responsive navbar and institutional footer
    ├── landing.html            # Public welcome / landing page with 3-step grievance workflow
    ├── login.html              # Student login portal with split-screen branding panel
    ├── register.html           # Student registration page with inline validation
    ├── student_dashboard.html  # Student dashboard with live 4-stat grid, quick actions, and recent tickets
    ├── submit_complaint.html   # Complaint submission form & interactive success confirmation screen
    ├── my_complaints.html      # Student complaint history table with status filters and keyword search
    ├── complaint_detail.html   # Dedicated ticket inspection with authentic 3-stage progress timeline
    ├── admin_login.html        # Secure administrator login gateway
    ├── admin_dashboard.html    # Admin management center with live metrics, search bar, and AJAX status updater
    ├── admin_complaint_detail.html # Full administrator grievance review and lifecycle status updater
    └── profile.html            # Student and Administrator profile summary
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- Python 3.9+ installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
# Recommended: Launches server and opens browser automatically
python run_app.py

# Or run Flask directly:
python app.py
```

### 4. Open in Browser
Visit: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Default Credentials

| Portal | Role | Username / Email | Password |
| :--- | :--- | :--- | :--- |
| **Admin Portal** | Administrator | `admin` | `admin123` |
| **Student Portal** | Student | `agrima89@gmail.com` | `2304` |
| **Student Portal** | Student | `mayank1211@gmail.com` | `1211` |
| *New Student* | Student | *Click "Create Account"* | *User defined* |

---

## 🎓 Viva & Project Evaluation Highlights

When presenting this project for B.Tech CSE evaluation, emphasize the following engineering highlights:
1. **Separation of Concerns**: Clean modular architecture separating routing (`app.py`), data access (`database.py`), presentation (`templates/`), and client interactions (`static/`).
2. **Security & Data Integrity**:
   - Parameterized SQL queries preventing SQL Injection attacks.
   - Role-based session guards (`@student_required`, `@admin_required`) preventing privilege escalation.
   - Enforced database constraints (Unique emails, foreign keys).
3. **User Experience (UX)**:
   - Non-blocking toast notifications instead of disruptive browser alerts.
   - Seamless AJAX status updates keeping admin dashboard metrics in sync without full page refreshes.
   - Fully responsive design accommodating mobile, tablet, and desktop viewports.
