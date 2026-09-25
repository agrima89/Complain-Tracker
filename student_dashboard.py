import tkinter as tk
import sqlite3
from datetime import datetime
import subprocess
import sys

from submit_complaint import open_complaint_form
from view_complaints import view_complaints


# ---------------- DATABASE ----------------

def get_statistics(student_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Total complaints
    cursor.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE student_id = ?
    """, (student_id,))

    total = cursor.fetchone()[0]

    # Pending complaints
    cursor.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE student_id = ?
        AND status IN ('NEW', 'FORWARDED')
    """, (student_id,))

    pending = cursor.fetchone()[0]

    # In Progress complaints
    cursor.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE student_id = ?
        AND status IN ('IN_PROGRESS', 'REOPENED')
    """, (student_id,))

    in_progress = cursor.fetchone()[0]

    # Resolved complaints
    cursor.execute("""
        SELECT COUNT(*)
        FROM complaints
        WHERE student_id = ?
        AND status IN ('FINAL_RESOLVED', 'RESOLUTION_SUBMITTED', 'AWAITING_STUDENT_CONFIRMATION')
    """, (student_id,))

    resolved = cursor.fetchone()[0]

    conn.close()

    return total, pending, in_progress, resolved


# ---------------- DASHBOARD ----------------

def open_dashboard(student_id, student_name):

    global root

    root = tk.Tk()

    root.title("CampusCare - Student Dashboard")
    root.geometry("1100x700")
    root.minsize(950, 600)
    root.configure(bg="#F5F7FB")

    # ================= COLORS =================

    SIDEBAR = "#172554"
    SIDEBAR_HOVER = "#1E3A8A"

    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#1D4ED8"

    WHITE = "#FFFFFF"
    BACKGROUND = "#F5F7FB"

    TEXT = "#111827"
    SECONDARY_TEXT = "#6B7280"

    GREEN = "#16A34A"
    ORANGE = "#EA580C"
    PURPLE = "#7C3AED"

    # ================= FUNCTIONS =================

    def logout():

        root.destroy()

        # Open Student Login again
        subprocess.Popen([
            sys.executable,
            "student_login.py"
        ])

    # ================= SIDEBAR =================

    sidebar = tk.Frame(
        root,
        bg=SIDEBAR,
        width=230
    )

    sidebar.pack(
        side="left",
        fill="y"
    )

    sidebar.pack_propagate(False)

    # Logo / App Name

    logo_frame = tk.Frame(
        sidebar,
        bg=SIDEBAR
    )

    logo_frame.pack(
        fill="x",
        pady=(30, 35)
    )

    logo = tk.Label(
        logo_frame,
        text="🏫",
        bg=SIDEBAR,
        fg=WHITE,
        font=("Arial", 25)
    )

    logo.pack()

    app_name = tk.Label(
        logo_frame,
        text="CampusCare",
        bg=SIDEBAR,
        fg=WHITE,
        font=("Arial", 19, "bold")
    )

    app_name.pack(
        pady=(5, 0)
    )

    tagline = tk.Label(
        logo_frame,
        text="Student Complaint Portal",
        bg=SIDEBAR,
        fg="#CBD5E1",
        font=("Arial", 9)
    )

    tagline.pack()

    # ================= SIDEBAR BUTTON FUNCTION =================

    def create_sidebar_button(
        text,
        command,
        active=False
    ):

        color = SIDEBAR_HOVER if active else SIDEBAR

        button = tk.Button(
            sidebar,
            text=text,
            command=command,
            anchor="w",
            padx=25,
            bg=color,
            fg=WHITE,
            activebackground=SIDEBAR_HOVER,
            activeforeground=WHITE,
            relief="flat",
            borderwidth=0,
            font=("Arial", 11, "bold"),
            cursor="hand2"
        )

        button.pack(
            fill="x",
            padx=12,
            pady=5,
            ipady=12
        )

        return button

    # Dashboard button

    dashboard_button = create_sidebar_button(
        "  🏠   Dashboard",
        lambda: None,
        True
    )

    # Submit Complaint

    complaint_button = create_sidebar_button(
        "  📝   Submit Complaint",
        lambda: open_complaint_form(student_id)
    )

    # My Complaints

    my_complaints_button = create_sidebar_button(
        "  📋   My Complaints",
        lambda: view_complaints(student_id)
    )

    # ================= SPACER =================

    spacer = tk.Frame(
        sidebar,
        bg=SIDEBAR
    )

    spacer.pack(
        expand=True,
        fill="both"
    )

    # ================= LOGOUT =================

    logout_button = tk.Button(
        sidebar,
        text="  🚪   Logout",
        command=logout,
        anchor="w",
        padx=25,
        bg=SIDEBAR,
        fg="#FCA5A5",
        activebackground="#991B1B",
        activeforeground=WHITE,
        relief="flat",
        borderwidth=0,
        font=("Arial", 11, "bold"),
        cursor="hand2"
    )

    logout_button.pack(
        fill="x",
        padx=12,
        pady=(5, 25),
        ipady=12
    )

    # ================= MAIN AREA =================

    main = tk.Frame(
        root,
        bg=BACKGROUND
    )

    main.pack(
        side="left",
        fill="both",
        expand=True
    )

    # ================= TOP HEADER =================

    header = tk.Frame(
        main,
        bg=WHITE,
        height=75
    )

    header.pack(
        fill="x"
    )

    header.pack_propagate(False)

    header_title = tk.Label(
        header,
        text="Student Dashboard",
        bg=WHITE,
        fg=TEXT,
        font=("Arial", 18, "bold")
    )

    header_title.pack(
        side="left",
        padx=30
    )

    # ================= STUDENT PROFILE =================

    profile_frame = tk.Frame(
        header,
        bg=WHITE
    )

    profile_frame.pack(
        side="right",
        padx=30
    )

    profile_icon = tk.Label(
        profile_frame,
        text="👤",
        bg=WHITE,
        font=("Arial", 20)
    )

    profile_icon.pack(
        side="left",
        padx=(0, 8)
    )

    profile_name = tk.Label(
        profile_frame,
        text=student_name,
        bg=WHITE,
        fg=TEXT,
        font=("Arial", 11, "bold")
    )

    profile_name.pack(
        side="left"
    )

    # ================= CONTENT =================

    content = tk.Frame(
        main,
        bg=BACKGROUND
    )

    content.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=25
    )

    # ================= WELCOME SECTION =================

    welcome_frame = tk.Frame(
        content,
        bg=BACKGROUND
    )

    welcome_frame.pack(
        fill="x",
        pady=(0, 20)
    )

    welcome_title = tk.Label(
        welcome_frame,
        text=f"Welcome, {student_name} 👋",
        bg=BACKGROUND,
        fg=TEXT,
        font=("Arial", 24, "bold")
    )

    welcome_title.pack(
        anchor="w"
    )

    welcome_subtitle = tk.Label(
        welcome_frame,
        text="Manage your campus complaints and track their progress.",
        bg=BACKGROUND,
        fg=SECONDARY_TEXT,
        font=("Arial", 11)
    )

    welcome_subtitle.pack(
        anchor="w",
        pady=(5, 0)
    )

    # ================= STATISTICS =================

    total, pending, in_progress, resolved = get_statistics(
        student_id
    )

    stats_frame = tk.Frame(
        content,
        bg=BACKGROUND
    )

    stats_frame.pack(
        fill="x",
        pady=(0, 25)
    )

    def create_stat_card(
        parent,
        title,
        value,
        icon,
        color
    ):

        card = tk.Frame(
            parent,
            bg=WHITE,
            height=120,
            relief="flat",
            borderwidth=0
        )

        card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=6
        )

        card.pack_propagate(False)

        # Top section

        top = tk.Frame(
            card,
            bg=WHITE
        )

        top.pack(
            fill="x",
            padx=18,
            pady=(15, 5)
        )

        title_label = tk.Label(
            top,
            text=title,
            bg=WHITE,
            fg=SECONDARY_TEXT,
            font=("Arial", 10, "bold")
        )

        title_label.pack(
            side="left"
        )

        icon_label = tk.Label(
            top,
            text=icon,
            bg=WHITE,
            fg=color,
            font=("Arial", 16)
        )

        icon_label.pack(
            side="right"
        )

        value_label = tk.Label(
            card,
            text=str(value),
            bg=WHITE,
            fg=TEXT,
            font=("Arial", 24, "bold")
        )

        value_label.pack(
            anchor="w",
            padx=18
        )

        # Bottom colored line

        line = tk.Frame(
            card,
            bg=color,
            height=4
        )

        line.pack(
            fill="x",
            side="bottom"
        )

    # Total

    create_stat_card(
        stats_frame,
        "Total Complaints",
        total,
        "📊",
        PRIMARY
    )

    # Pending

    create_stat_card(
        stats_frame,
        "Pending",
        pending,
        "⏳",
        ORANGE
    )

    # In Progress

    create_stat_card(
        stats_frame,
        "In Progress",
        in_progress,
        "🔄",
        PURPLE
    )

    # Resolved

    create_stat_card(
        stats_frame,
        "Resolved",
        resolved,
        "✓",
        GREEN
    )

    # ================= ACTION SECTION =================

    action_frame = tk.Frame(
        content,
        bg=WHITE
    )

    action_frame.pack(
        fill="x",
        pady=(0, 20)
    )

    action_frame.configure(
        height=180
    )

    action_frame.pack_propagate(False)

    # Left side

    action_text = tk.Frame(
        action_frame,
        bg=WHITE
    )

    action_text.pack(
        side="left",
        fill="both",
        expand=True,
        padx=30,
        pady=25
    )

    action_title = tk.Label(
        action_text,
        text="Have an issue on campus?",
        bg=WHITE,
        fg=TEXT,
        font=("Arial", 18, "bold")
    )

    action_title.pack(
        anchor="w"
    )

    action_subtitle = tk.Label(
        action_text,
        text="Report a problem and help make your campus better.",
        bg=WHITE,
        fg=SECONDARY_TEXT,
        font=("Arial", 10)
    )

    action_subtitle.pack(
        anchor="w",
        pady=(7, 0)
    )

    # Submit button

    submit_button = tk.Button(
        action_frame,
        text="+  Submit Complaint",
        command=lambda: open_complaint_form(student_id),
        bg=PRIMARY,
        fg=WHITE,
        activebackground=PRIMARY_HOVER,
        activeforeground=WHITE,
        relief="flat",
        borderwidth=0,
        font=("Arial", 11, "bold"),
        cursor="hand2",
        padx=20,
        pady=12
    )

    submit_button.pack(
        side="right",
        padx=30
    )

    # ================= MY COMPLAINTS =================

    bottom_frame = tk.Frame(
        content,
        bg=BACKGROUND
    )

    bottom_frame.pack(
        fill="x"
    )

    complaints_title = tk.Label(
        bottom_frame,
        text="Quick Access",
        bg=BACKGROUND,
        fg=TEXT,
        font=("Arial", 15, "bold")
    )

    complaints_title.pack(
        anchor="w",
        pady=(0, 10)
    )

    complaints_card = tk.Frame(
        bottom_frame,
        bg=WHITE,
        height=75
    )

    complaints_card.pack(
        fill="x"
    )

    complaints_card.pack_propagate(False)

    complaints_text = tk.Label(
        complaints_card,
        text="📋   View and track all your submitted complaints",
        bg=WHITE,
        fg=TEXT,
        font=("Arial", 11)
    )

    complaints_text.pack(
        side="left",
        padx=20
    )

    view_button = tk.Button(
        complaints_card,
        text="View Complaints  →",
        command=lambda: view_complaints(student_id),
        bg=WHITE,
        fg=PRIMARY,
        activebackground="#EFF6FF",
        activeforeground=PRIMARY_HOVER,
        relief="flat",
        borderwidth=0,
        font=("Arial", 10, "bold"),
        cursor="hand2"
    )

    view_button.pack(
        side="right",
        padx=20
    )

    # ================= START =================

    root.mainloop()