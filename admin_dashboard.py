import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import os
from PIL import Image, ImageTk
import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_statistics():
    stats = database.get_admin_statistics()
    return stats["total"], stats["pending"], stats["in_progress"], stats["resolved"]


def update_statistics():
    total, pending, in_progress, resolved = get_statistics()
    total_label.config(text=str(total))
    pending_label.config(text=str(pending))
    progress_label.config(text=str(in_progress))
    resolved_label.config(text=str(resolved))


def update_status(complaint_id, status, root):
    success, msg = database.update_complaint_status(complaint_id, status)
    if success:
        messagebox.showinfo(
            "Success",
            f"Complaint #{complaint_id:03d} status updated to '{status}'!"
        )
        root.destroy()
        open_admin_dashboard()
    else:
        messagebox.showerror("Error", msg)


def add_hover_effect(button, normal_bg, hover_bg):
    """Adds a smooth hover background color change to a button."""
    button.bind("<Enter>", lambda e: button.config(bg=hover_bg))
    button.bind("<Leave>", lambda e: button.config(bg=normal_bg))


def get_status_style(status):
    if status == "Pending":
        return {"bg": "#FEF3C7", "fg": "#D97706"}
    elif status == "In Progress":
        return {"bg": "#DBEAFE", "fg": "#2563EB"}
    elif status == "Resolved":
        return {"bg": "#D1FAE5", "fg": "#059669"}
    return {"bg": "#E2E8F0", "fg": "#475569"}


def get_priority_style(priority):
    if priority == "High":
        return {"bg": "#FEE2E2", "fg": "#DC2626"}
    elif priority == "Medium":
        return {"bg": "#FEF3C7", "fg": "#D97706"}
    elif priority == "Low":
        return {"bg": "#E0F2FE", "fg": "#0284C7"}
    return {"bg": "#F1F5F9", "fg": "#64748B"}


def open_admin_photo_viewer(parent, photo_rel_path, complaint_id):
    full_path = os.path.join(BASE_DIR, photo_rel_path)
    if not os.path.isfile(full_path):
        messagebox.showerror("Image Error", f"Evidence image file not found on disk:\n{photo_rel_path}")
        return

    viewer = tk.Toplevel(parent)
    viewer.title(f"Evidence Photo - Complaint #{complaint_id}")
    viewer.geometry("700x600")
    viewer.configure(bg="#0F172A")

    # Header
    header = tk.Frame(viewer, bg="#1E293B", padx=15, pady=10)
    header.pack(fill="x")

    tk.Label(
        header,
        text=f"📸 Admin Review: Evidence Photo for Complaint #{complaint_id:03d}",
        font=("Segoe UI", 11, "bold"),
        fg="#FFFFFF",
        bg="#1E293B"
    ).pack(side="left")

    tk.Label(
        header,
        text=os.path.basename(full_path),
        font=("Segoe UI", 9),
        fg="#94A3B8",
        bg="#1E293B"
    ).pack(side="right")

    # Image canvas/label
    img_container = tk.Frame(viewer, bg="#0F172A")
    img_container.pack(fill="both", expand=True, padx=15, pady=15)

    try:
        raw_img = Image.open(full_path)
        raw_img.thumbnail((660, 480))
        photo_img = ImageTk.PhotoImage(raw_img)

        lbl = tk.Label(img_container, image=photo_img, bg="#0F172A")
        lbl.image = photo_img
        lbl.pack(expand=True)
    except Exception as e:
        tk.Label(
            img_container,
            text=f"Failed to display image:\n{e}",
            fg="#F87171",
            bg="#0F172A",
            font=("Segoe UI", 11)
        ).pack(expand=True)


def load_complaints(
    root,
    status_filter,
    priority_filter,
    search_text
):
    # Remove old complaint frames
    for widget in root.winfo_children():
        widget.destroy()

    complaints = database.get_all_complaints_admin(
        status_filter=status_filter,
        priority_filter=priority_filter,
        search_text=search_text
    )

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

        tk.Label(
            no_data_frame,
            text="No complaints found matching your criteria.",
            font=("Segoe UI", 12, "italic"),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack()
        return

    top_window = root.winfo_toplevel()

    for item in complaints:
        complaint_id = item["complaint_id"]
        student_name = item["student_name"]
        student_email = item["student_email"]
        category = item["category"]
        description = item["description"]
        photo_path = item["photo_path"]
        block = item["block"] or "Campus"
        floor_no = item["floor_no"] or "-"
        room_no = item["room_no"] or "-"
        corridor_side = item["corridor_side"] or "-"
        nearby_area = item["nearby_area"] or "-"
        add_loc = item["additional_location"] or ""
        location_str = item["location"]
        priority = item["priority"]
        status = item["status"]
        date_str = item["date"]

        # Complaint Card Container
        card = tk.Frame(
            root,
            bg="#FFFFFF",
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground="#E2E8F0"
        )
        card.pack(fill="x", padx=20, pady=8)

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
            text=f"Complaint #{complaint_id:03d}",
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
            text=f"📅 {date_str}",
            font=("Segoe UI", 9),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack(side="left")

        # --- Student Details Row ---
        student_row = tk.Frame(inner, bg="#FFFFFF")
        student_row.pack(fill="x", pady=(0, 6))

        tk.Label(
            student_row,
            text="Submitting Student: ",
            font=("Segoe UI", 9, "bold"),
            fg="#1E293B",
            bg="#FFFFFF"
        ).pack(side="left")

        tk.Label(
            student_row,
            text=f"{student_name} ({student_email})",
            font=("Segoe UI", 9),
            fg="#2563EB",
            bg="#FFFFFF"
        ).pack(side="left")

        # --- Location Hierarchy Row ---
        loc_frame = tk.Frame(inner, bg="#F8FAFC", padx=12, pady=8, relief="solid", bd=1)
        loc_frame.pack(fill="x", pady=(0, 8))

        loc_text = f"📍 Block: {block}   |   Floor: {floor_no}   |   Room: {room_no}   |   Side: {corridor_side}"
        if nearby_area and nearby_area != "-":
            loc_text += f"   |   Near: {nearby_area}"
        if add_loc:
            loc_text += f"\n   Details: {add_loc}"

        tk.Label(
            loc_frame,
            text=loc_text,
            font=("Segoe UI", 9),
            fg="#1E293B",
            bg="#F8FAFC",
            justify="left",
            anchor="w"
        ).pack(fill="x")

        # --- Description Frame ---
        desc_frame = tk.Frame(
            inner,
            bg="#FFFFFF",
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground="#E2E8F0"
        )
        desc_frame.pack(fill="x", pady=(0, 8))

        tk.Label(
            desc_frame,
            text=description,
            font=("Segoe UI", 10),
            fg="#334155",
            bg="#FFFFFF",
            justify="left",
            anchor="w",
            wraplength=800,
            padx=10,
            pady=8
        ).pack(fill="x")

        # --- Evidence Photo Row ---
        evidence_row = tk.Frame(inner, bg="#FFFFFF")
        evidence_row.pack(fill="x", pady=(0, 10))

        if photo_path and os.path.isfile(os.path.join(BASE_DIR, photo_path)):
            tk.Label(
                evidence_row,
                text="📸 Evidence Photo:",
                font=("Segoe UI", 9, "bold"),
                fg="#059669",
                bg="#FFFFFF"
            ).pack(side="left", padx=(0, 8))

            view_btn = tk.Button(
                evidence_row,
                text="🔍 View Evidence Photo",
                font=("Segoe UI", 9, "bold"),
                bg="#0284C7",
                fg="#FFFFFF",
                activebackground="#0369A1",
                activeforeground="#FFFFFF",
                relief="flat",
                bd=0,
                padx=10,
                pady=3,
                cursor="hand2",
                command=lambda p=photo_path, c=complaint_id: open_admin_photo_viewer(top_window, p, c)
            )
            view_btn.pack(side="left")
        else:
            tk.Label(
                evidence_row,
                text="📸 Evidence: No image attached (Legacy record)",
                font=("Segoe UI", 9, "italic"),
                fg="#94A3B8",
                bg="#FFFFFF"
            ).pack(side="left")

        # --- Footer / Action Row (Status update) ---
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
        status_var = tk.StringVar(value=status)

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
        status_menu.pack(side="left", padx=(0, 10))

        # Update button
        update_button = tk.Button(
            footer_row,
            text="Save Status",
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
            command=lambda cid=complaint_id, var=status_var: update_status(cid, var.get(), top_window)
        )
        update_button.pack(side="left")
        add_hover_effect(update_button, "#2563EB", "#1D4ED8")

        def export_admin_pdf(c_id=complaint_id):
            from tkinter import filedialog
            import pdf_generator
            complaint_data = database.get_complaint_by_id(c_id)
            if not complaint_data:
                messagebox.showerror("Error", "Complaint not found.")
                return
            history_data = database.get_complaint_history(c_id)
            default_name = pdf_generator.get_pdf_filename(complaint_data["complaint_id"], complaint_data["student_name"])
            save_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Documents", "*.pdf")],
                initialfile=default_name
            )
            if save_path:
                try:
                    with open(save_path, "wb") as f:
                        pdf_generator.generate_complaint_pdf(complaint_data, history_data, f)
                    messagebox.showinfo("Success", f"Complaint PDF saved successfully:\n{os.path.basename(save_path)}")
                except Exception as e:
                    messagebox.showerror("Export Error", f"Failed to generate PDF:\n{e}")

        pdf_export_btn = tk.Button(
            footer_row,
            text="📄 Generate PDF",
            font=("Segoe UI", 9, "bold"),
            bg="#0284C7",
            fg="#FFFFFF",
            activebackground="#0369A1",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=export_admin_pdf
        )
        pdf_export_btn.pack(side="right")
        add_hover_effect(pdf_export_btn, "#0284C7", "#0369A1")


def open_admin_dashboard():
    global total_label
    global pending_label
    global progress_label
    global resolved_label

    root = tk.Tk()
    root.title("CampusCare - Administrator Grievance Command Center")
    root.geometry("1020x820")
    root.minsize(880, 680)
    root.configure(bg="#F8FAFC")

    # Configure ttk styles for Combobox
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "TCombobox",
        fieldbackground="#FFFFFF",
        background="#E2E8F0"
    )

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
        text="🛡️ Admin Management Dashboard",
        font=("Segoe UI", 20, "bold"),
        fg="#FFFFFF",
        bg="#1E3A8A"
    )
    title_label.pack(anchor="w")

    subtitle_label = tk.Label(
        header,
        text="Student Complaint & Solution Tracker — Campus Grievance Inspection & Status Redressal",
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

    total_label = create_stat_card(stats_container, 0, "TOTAL COMPLAINTS", "#2563EB")
    pending_label = create_stat_card(stats_container, 1, "PENDING", "#D97706")
    progress_label = create_stat_card(stats_container, 2, "IN PROGRESS", "#0284C7")
    resolved_label = create_stat_card(stats_container, 3, "RESOLVED", "#059669")

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

    status_filter = tk.StringVar(value="All")
    status_menu = ttk.Combobox(
        filter_inner,
        textvariable=status_filter,
        values=["All", "Pending", "In Progress", "Resolved"],
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

    priority_filter = tk.StringVar(value="All")
    priority_menu = ttk.Combobox(
        filter_inner,
        textvariable=priority_filter,
        values=["All", "Low", "Medium", "High"],
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
    reset_btn.pack(side="left", padx=(0, 8))
    add_hover_effect(reset_btn, "#64748B", "#475569")

    def export_summary_pdf():
        from tkinter import filedialog
        import pdf_generator
        stats_data = database.get_admin_statistics()
        analytics_data = database.get_analytics_data()
        complaints_data = database.get_all_complaints_for_report(
            status_filter=status_filter.get(),
            priority_filter=priority_filter.get(),
            search_text=search_entry.get().strip()
        )
        default_name = pdf_generator.get_summary_pdf_filename()
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
            initialfile=default_name
        )
        if save_path:
            try:
                with open(save_path, "wb") as f:
                    pdf_generator.generate_admin_summary_pdf(
                        stats=stats_data,
                        category_stats=analytics_data["by_category"],
                        priority_stats=analytics_data["by_priority"],
                        complaints_list=complaints_data,
                        admin_name="Administrator",
                        output_stream=f
                    )
                messagebox.showinfo("Success", f"Complaint Summary Report saved successfully:\n{os.path.basename(save_path)}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to generate Summary PDF:\n{e}")

    report_pdf_btn = tk.Button(
        btn_frame,
        text="📄 Generate Report PDF",
        font=("Segoe UI", 9, "bold"),
        bg="#059669",
        fg="#FFFFFF",
        activebackground="#047857",
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=12,
        pady=5,
        cursor="hand2",
        command=export_summary_pdf
    )
    report_pdf_btn.pack(side="left")
    add_hover_effect(report_pdf_btn, "#059669", "#047857")

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

    canvas = tk.Canvas(main_content_frame, bg="#F8FAFC", highlightthickness=0)
    scrollbar = ttk.Scrollbar(main_content_frame, orient="vertical", command=canvas.yview)
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