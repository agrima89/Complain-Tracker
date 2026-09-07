import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3


def get_statistics():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE status = 'Pending'
    """)
    pending = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE status = 'In Progress'
    """)
    in_progress = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE status = 'Resolved'
    """)
    resolved = cursor.fetchone()[0]

    conn.close()

    return total, pending, in_progress, resolved


def update_statistics():
    total, pending, in_progress, resolved = get_statistics()

    total_label.config(text=str(total))
    pending_label.config(text=str(pending))
    progress_label.config(text=str(in_progress))
    resolved_label.config(text=str(resolved))


def update_status(complaint_id, status, root):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE complaints
        SET status = ?
        WHERE complaint_id = ?
    """, (status, complaint_id))

    conn.commit()
    conn.close()

    messagebox.showinfo(
        "Success",
        "Complaint status updated successfully!"
    )

    root.destroy()
    open_admin_dashboard()


def add_hover_effect(button, normal_bg, hover_bg):
    """Adds a smooth hover background color change to a button."""
    button.bind("<Enter>", lambda e: button.config(bg=hover_bg))
    button.bind("<Leave>", lambda e: button.config(bg=normal_bg))


def get_status_style(status):
    """Returns color schemes for different complaint statuses."""
    if status == "Pending":
        return {"bg": "#FEF3C7", "fg": "#D97706"}
    elif status == "In Progress":
        return {"bg": "#DBEAFE", "fg": "#2563EB"}
    elif status == "Resolved":
        return {"bg": "#D1FAE5", "fg": "#059669"}
    return {"bg": "#E2E8F0", "fg": "#475569"}


def get_priority_style(priority):
    """Returns color schemes for complaint priority levels."""
    if priority == "High":
        return {"bg": "#FEE2E2", "fg": "#DC2626"}
    elif priority == "Medium":
        return {"bg": "#FEF3C7", "fg": "#D97706"}
    elif priority == "Low":
        return {"bg": "#E0F2FE", "fg": "#0284C7"}
    return {"bg": "#F1F5F9", "fg": "#64748B"}


def load_complaints(
    root,
    status_filter,
    priority_filter,
    search_text
):

    # Remove old complaint frames
    for widget in root.winfo_children():
        if getattr(widget, "is_complaint_frame", False):
            widget.destroy()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    query = """
        SELECT
            complaints.complaint_id,
            students.name,
            complaints.category,
            complaints.description,
            complaints.location,
            complaints.priority,
            complaints.status,
            complaints.date
        FROM complaints
        JOIN students
        ON complaints.student_id = students.student_id
        WHERE 1=1
    """

    parameters = []

    # Status filter
    if status_filter != "All":
        query += " AND complaints.status = ?"
        parameters.append(status_filter)

    # Priority filter
    if priority_filter != "All":
        query += " AND complaints.priority = ?"
        parameters.append(priority_filter)

    # Search
    if search_text != "":
        query += """
            AND (
                students.name LIKE ?
                OR complaints.category LIKE ?
                OR complaints.description LIKE ?
                OR complaints.location LIKE ?
            )
        """

        search_value = "%" + search_text + "%"

        parameters.extend([
            search_value,
            search_value,
            search_value,
            search_value
        ])

    cursor.execute(query, parameters)

    complaints = cursor.fetchall()

    conn.close()

    if not complaints:
        no_data_frame = tk.Frame(
            root,
            bg="#FFFFFF",
            bd=1,
            relief="solid",
            padx=20,
            pady=30
        )
        no_data_frame.pack(fill="x", padx=20, pady=20)
        no_data_frame.is_complaint_frame = True

        tk.Label(
            no_data_frame,
            text="No complaints found matching your criteria.",
            font=("Segoe UI", 12, "italic"),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack()

        return

    # Find top-level window for update_status parameter
    top_window = root.winfo_toplevel()

    # Display complaints
    for complaint in complaints:

        complaint_id = complaint[0]
        student_name = complaint[1]
        category = complaint[2]
        description = complaint[3]
        location = complaint[4]
        priority = complaint[5]
        status = complaint[6]
        date_str = complaint[7]

        # Complaint Card Container
        card = tk.Frame(
            root,
            bg="#FFFFFF",
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground="#E2E8F0"
        )

        card.pack(
            fill="x",
            padx=20,
            pady=8
        )

        card.is_complaint_frame = True

        # Inner Container for clean padding
        inner = tk.Frame(card, bg="#FFFFFF", padx=16, pady=14)
        inner.pack(fill="x")

        # --- Header Row ---
        header_row = tk.Frame(inner, bg="#FFFFFF")
        header_row.pack(fill="x", pady=(0, 8))

        # Left side: ID & Category
        left_header = tk.Frame(header_row, bg="#FFFFFF")
        left_header.pack(side="left")

        tk.Label(
            left_header,
            text=f"Complaint #{complaint_id}",
            font=("Segoe UI", 12, "bold"),
            fg="#1E3A8A",
            bg="#FFFFFF"
        ).pack(side="left", padx=(0, 10))

        tk.Label(
            left_header,
            text=category,
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#F1F5F9",
            padx=8,
            pady=2
        ).pack(side="left")

        # Right side: Priority, Status Badges & Date
        right_header = tk.Frame(header_row, bg="#FFFFFF")
        right_header.pack(side="right")

        # Priority Tag
        p_style = get_priority_style(priority)
        tk.Label(
            right_header,
            text=f"Priority: {priority}",
            font=("Segoe UI", 9, "bold"),
            fg=p_style["fg"],
            bg=p_style["bg"],
            padx=8,
            pady=2
        ).pack(side="left", padx=(0, 8))

        # Status Badge
        s_style = get_status_style(status)
        tk.Label(
            right_header,
            text=status,
            font=("Segoe UI", 9, "bold"),
            fg=s_style["fg"],
            bg=s_style["bg"],
            padx=10,
            pady=2
        ).pack(side="left", padx=(0, 12))

        # Date Label
        tk.Label(
            right_header,
            text=f"Date: {date_str}",
            font=("Segoe UI", 9),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack(side="left")

        # --- Details Row ---
        details_row = tk.Frame(inner, bg="#FFFFFF")
        details_row.pack(fill="x", pady=(0, 8))

        tk.Label(
            details_row,
            text="Student: ",
            font=("Segoe UI", 10, "bold"),
            fg="#1E293B",
            bg="#FFFFFF"
        ).pack(side="left")

        tk.Label(
            details_row,
            text=f"{student_name}   |   ",
            font=("Segoe UI", 10),
            fg="#334155",
            bg="#FFFFFF"
        ).pack(side="left")

        tk.Label(
            details_row,
            text="Location: ",
            font=("Segoe UI", 10, "bold"),
            fg="#1E293B",
            bg="#FFFFFF"
        ).pack(side="left")

        tk.Label(
            details_row,
            text=location,
            font=("Segoe UI", 10),
            fg="#334155",
            bg="#FFFFFF"
        ).pack(side="left")

        # --- Description Frame ---
        desc_frame = tk.Frame(
            inner,
            bg="#F8FAFC",
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground="#E2E8F0"
        )
        desc_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            desc_frame,
            text=description,
            font=("Segoe UI", 10),
            fg="#334155",
            bg="#F8FAFC",
            justify="left",
            anchor="w",
            wraplength=800,
            padx=10,
            pady=8
        ).pack(fill="x")

        # --- Footer / Action Row ---
        footer_row = tk.Frame(inner, bg="#FFFFFF")
        footer_row.pack(fill="x", pady=(4, 0))

        tk.Label(
            footer_row,
            text="Update Status:",
            font=("Segoe UI", 10, "bold"),
            fg="#475569",
            bg="#FFFFFF"
        ).pack(side="left", padx=(0, 8))

        # Status dropdown
        status_var = tk.StringVar()
        status_var.set(status)

        status_menu = ttk.Combobox(
            footer_row,
            textvariable=status_var,
            values=[
                "Pending",
                "In Progress",
                "Resolved"
            ],
            state="readonly",
            width=15
        )

        status_menu.pack(
            side="left",
            padx=(0, 10)
        )

        # Update button
        update_button = tk.Button(
            footer_row,
            text="Update Status",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=lambda cid=complaint_id,
            var=status_var:
            update_status(
                cid,
                var.get(),
                top_window
            )
        )

        update_button.pack(side="left")
        add_hover_effect(update_button, "#2563EB", "#1D4ED8")


def open_admin_dashboard():

    global total_label
    global pending_label
    global progress_label
    global resolved_label

    root = tk.Tk()

    root.title("Student Complaint & Solution Tracker - Admin Dashboard")
    root.geometry("980x780")
    root.minsize(850, 650)
    root.configure(bg="#F8FAFC")

    # Configure ttk styles for Combobox
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "TCombobox",
        fieldbackground="#FFFFFF",
        background="#E2E8F0"
    )

    # Grid configuration for responsive layout
    root.rowconfigure(3, weight=1)
    root.columnconfigure(0, weight=1)

    # 1. Top Header Area
    header = tk.Frame(
        root,
        bg="#1E3A8A",
        pady=15,
        padx=25
    )
    header.grid(row=0, column=0, sticky="ew")

    title_label = tk.Label(
        header,
        text="Admin Dashboard",
        font=("Segoe UI", 20, "bold"),
        fg="#FFFFFF",
        bg="#1E3A8A"
    )
    title_label.pack(anchor="w")

    subtitle_label = tk.Label(
        header,
        text="Student Complaint & Solution Tracker — Overview & Management",
        font=("Segoe UI", 10),
        fg="#93C5FD",
        bg="#1E3A8A"
    )
    subtitle_label.pack(anchor="w", pady=(2, 0))

    # 2. Statistics Section
    stats_container = tk.Frame(
        root,
        bg="#F8FAFC",
        padx=20,
        pady=15
    )
    stats_container.grid(row=1, column=0, sticky="ew")

    for i in range(4):
        stats_container.columnconfigure(i, weight=1)

    def create_stat_card(parent, col, title, accent_color):
        card = tk.Frame(
            parent,
            bg="#FFFFFF",
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground="#E2E8F0"
        )
        card.grid(row=0, column=col, padx=8, sticky="ew")

        # Top accent color bar
        accent_bar = tk.Frame(card, bg=accent_color, height=4)
        accent_bar.pack(fill="x", side="top")

        content = tk.Frame(card, bg="#FFFFFF", padx=15, pady=12)
        content.pack(fill="both", expand=True)

        tk.Label(
            content,
            text=title,
            font=("Segoe UI", 9, "bold"),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack(anchor="w")

        count_lbl = tk.Label(
            content,
            text="0",
            font=("Segoe UI", 22, "bold"),
            fg="#1E293B",
            bg="#FFFFFF"
        )
        count_lbl.pack(anchor="w", pady=(4, 0))
        return count_lbl

    total_label = create_stat_card(
        stats_container, 0, "TOTAL COMPLAINTS", "#2563EB"
    )
    pending_label = create_stat_card(
        stats_container, 1, "PENDING", "#D97706"
    )
    progress_label = create_stat_card(
        stats_container, 2, "IN PROGRESS", "#0284C7"
    )
    resolved_label = create_stat_card(
        stats_container, 3, "RESOLVED", "#059669"
    )

    # Update statistics
    update_statistics()

    # 3. Filter and Search Bar Container
    filter_bar = tk.Frame(
        root,
        bg="#FFFFFF",
        bd=1,
        relief="solid",
        highlightthickness=1,
        highlightbackground="#E2E8F0"
    )
    filter_bar.grid(row=2, column=0, padx=28, pady=(0, 15), sticky="ew")

    filter_inner = tk.Frame(filter_bar, bg="#FFFFFF", padx=15, pady=12)
    filter_inner.pack(fill="x")

    # Search Box
    tk.Label(
        filter_inner,
        text="Search:",
        font=("Segoe UI", 10, "bold"),
        fg="#334155",
        bg="#FFFFFF"
    ).pack(side="left", padx=(0, 6))

    search_entry = tk.Entry(
        filter_inner,
        font=("Segoe UI", 10),
        width=25,
        bd=1,
        relief="solid"
    )
    search_entry.pack(side="left", padx=(0, 15), ipady=3)

    # Status Filter
    tk.Label(
        filter_inner,
        text="Status:",
        font=("Segoe UI", 10, "bold"),
        fg="#334155",
        bg="#FFFFFF"
    ).pack(side="left", padx=(0, 6))

    status_filter = tk.StringVar()
    status_filter.set("All")

    status_menu = ttk.Combobox(
        filter_inner,
        textvariable=status_filter,
        values=[
            "All",
            "Pending",
            "In Progress",
            "Resolved"
        ],
        state="readonly",
        width=12
    )
    status_menu.pack(side="left", padx=(0, 15))

    # Priority Filter
    tk.Label(
        filter_inner,
        text="Priority:",
        font=("Segoe UI", 10, "bold"),
        fg="#334155",
        bg="#FFFFFF"
    ).pack(side="left", padx=(0, 6))

    priority_filter = tk.StringVar()
    priority_filter.set("All")

    priority_menu = ttk.Combobox(
        filter_inner,
        textvariable=priority_filter,
        values=[
            "All",
            "Low",
            "Medium",
            "High"
        ],
        state="readonly",
        width=10
    )
    priority_menu.pack(side="left", padx=(0, 15))

    # Action Buttons
    btn_frame = tk.Frame(filter_inner, bg="#FFFFFF")
    btn_frame.pack(side="right")

    def trigger_search():
        load_complaints(
            scrollable_frame,
            status_filter.get(),
            priority_filter.get(),
            search_entry.get().strip()
        )

    search_btn = tk.Button(
        btn_frame,
        text="Search / Filter",
        font=("Segoe UI", 9, "bold"),
        bg="#2563EB",
        fg="#FFFFFF",
        activebackground="#1D4ED8",
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=12,
        pady=5,
        cursor="hand2",
        command=trigger_search
    )
    search_btn.pack(side="left", padx=(0, 8))
    add_hover_effect(search_btn, "#2563EB", "#1D4ED8")

    def reset_filters():
        search_entry.delete(0, tk.END)
        status_filter.set("All")
        priority_filter.set("All")
        trigger_search()

    reset_btn = tk.Button(
        btn_frame,
        text="Reset",
        font=("Segoe UI", 9, "bold"),
        bg="#64748B",
        fg="#FFFFFF",
        activebackground="#475569",
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=10,
        pady=5,
        cursor="hand2",
        command=reset_filters
    )
    reset_btn.pack(side="left")
    add_hover_effect(reset_btn, "#64748B", "#475569")

    # Bind Enter key to search
    search_entry.bind("<Return>", lambda e: trigger_search())

    # 4. Scrollable Complaints Area
    main_content_frame = tk.Frame(root, bg="#F8FAFC")
    main_content_frame.grid(
        row=3,
        column=0,
        sticky="nsew",
        padx=8,
        pady=(0, 15)
    )
    main_content_frame.rowconfigure(0, weight=1)
    main_content_frame.columnconfigure(0, weight=1)

    canvas = tk.Canvas(
        main_content_frame,
        bg="#F8FAFC",
        highlightthickness=0
    )
    scrollbar = ttk.Scrollbar(
        main_content_frame,
        orient="vertical",
        command=canvas.yview
    )
    scrollable_frame = tk.Frame(canvas, bg="#F8FAFC")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas_window = canvas.create_window(
        (0, 0),
        window=scrollable_frame,
        anchor="nw"
    )

    def _on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind("<Configure>", _on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    # Mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Initial load of complaints
    load_complaints(
        scrollable_frame,
        "All",
        "All",
        ""
    )

    root.mainloop()


if __name__ == "__main__":
    open_admin_dashboard()