import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk
import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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


def open_photo_viewer(parent, photo_rel_path, complaint_id):
    full_path = os.path.join(BASE_DIR, photo_rel_path)
    if not os.path.isfile(full_path):
        messagebox.showerror("Image Error", f"Evidence image file not found on disk:\n{photo_rel_path}")
        return

    viewer = tk.Toplevel(parent)
    viewer.title(f"Evidence Photo - Complaint #{complaint_id}")
    viewer.geometry("640x540")
    viewer.configure(bg="#0F172A")

    # Header
    header = tk.Frame(viewer, bg="#1E293B", padx=15, pady=10)
    header.pack(fill="x")

    tk.Label(
        header,
        text=f"📸 Evidence Photo for Complaint #{complaint_id}",
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
        raw_img.thumbnail((600, 420))
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


def load_complaints(scroll_frame, student_id, status_filter):
    for widget in scroll_frame.winfo_children():
        widget.destroy()

    complaints = database.get_student_complaints(student_id, status_filter=status_filter)

    if not complaints:
        no_data_frame = tk.Frame(
            scroll_frame,
            bg="#FFFFFF",
            bd=1,
            relief="solid",
            padx=30,
            pady=35
        )
        no_data_frame.pack(fill="x", padx=10, pady=15)

        tk.Label(
            no_data_frame,
            text="🔍 No complaints found.",
            font=("Segoe UI", 13, "bold"),
            fg="#334155",
            bg="#FFFFFF"
        ).pack(pady=(0, 5))

        tk.Label(
            no_data_frame,
            text="You have not submitted any complaints matching this filter.",
            font=("Segoe UI", 10),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack()
        return

    top_window = scroll_frame.winfo_toplevel()

    for item in complaints:
        cid = item["complaint_id"]
        ticket_id = item["ticket_id"] if "ticket_id" in item.keys() and item["ticket_id"] else f"#{cid:03d}"
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

        card = tk.Frame(
            scroll_frame,
            bg="#FFFFFF",
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground="#E2E8F0"
        )
        card.pack(fill="x", padx=10, pady=8)

        inner = tk.Frame(card, bg="#FFFFFF", padx=16, pady=14)
        inner.pack(fill="x")

        # 1. Header Row: ID, Category, Priority, Status, Date
        hdr = tk.Frame(inner, bg="#FFFFFF")
        hdr.pack(fill="x", pady=(0, 8))

        left_hdr = tk.Frame(hdr, bg="#FFFFFF")
        left_hdr.pack(side="left")

        tk.Label(
            left_hdr,
            text=f"Ticket {ticket_id}",
            font=("Segoe UI", 12, "bold"),
            fg="#1E3A8A",
            bg="#FFFFFF"
        ).pack(side="left", padx=(0, 10))

        tk.Label(
            left_hdr,
            text=category,
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#F1F5F9",
            padx=8,
            pady=2
        ).pack(side="left")

        right_hdr = tk.Frame(hdr, bg="#FFFFFF")
        right_hdr.pack(side="right")

        # Priority
        p_style = get_priority_style(priority)
        tk.Label(
            right_hdr,
            text=f"Priority: {priority}",
            font=("Segoe UI", 9, "bold"),
            fg=p_style["fg"],
            bg=p_style["bg"],
            padx=8,
            pady=2
        ).pack(side="left", padx=(0, 8))

        # Status
        s_style = get_status_style(status)
        tk.Label(
            right_hdr,
            text=status,
            font=("Segoe UI", 9, "bold"),
            fg=s_style["fg"],
            bg=s_style["bg"],
            padx=10,
            pady=2
        ).pack(side="left", padx=(0, 10))

        # Date
        tk.Label(
            right_hdr,
            text=f"📅 {date_str}",
            font=("Segoe UI", 9),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack(side="left")

        # 2. Location Hierarchy Row
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

        # 3. Description Box
        desc_box = tk.Frame(inner, bg="#FFFFFF")
        desc_box.pack(fill="x", pady=(0, 10))

        tk.Label(
            desc_box,
            text="Issue Description:",
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#FFFFFF"
        ).pack(anchor="w")

        tk.Label(
            desc_box,
            text=description,
            font=("Segoe UI", 9),
            fg="#334155",
            bg="#FFFFFF",
            justify="left",
            anchor="w",
            wraplength=640
        ).pack(fill="x", pady=(2, 0))

        # 4. Evidence Photo Row
        evidence_row = tk.Frame(inner, bg="#FFFFFF")
        evidence_row.pack(fill="x")

        if photo_path and os.path.isfile(os.path.join(BASE_DIR, photo_path)):
            tk.Label(
                evidence_row,
                text="📸 Evidence Attached:",
                font=("Segoe UI", 9, "bold"),
                fg="#059669",
                bg="#FFFFFF"
            ).pack(side="left", padx=(0, 8))

            view_photo_btn = tk.Button(
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
                command=lambda p=photo_path, c=cid: open_photo_viewer(top_window, p, c)
            )
            view_photo_btn.pack(side="left", padx=(0, 8))
        else:
            tk.Label(
                evidence_row,
                text="📸 Evidence: No image attached (Legacy record)",
                font=("Segoe UI", 9, "italic"),
                fg="#94A3B8",
                bg="#FFFFFF"
            ).pack(side="left", padx=(0, 8))

        def export_pdf(c_id=cid):
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

        pdf_btn = tk.Button(
            evidence_row,
            text="📄 Export PDF",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2",
            command=export_pdf
        )
        pdf_btn.pack(side="right")


def view_complaints(student_id):
    window = tk.Toplevel()
    window.title("My Complaint Grievance History - CampusCare")
    window.geometry("820x720")
    window.minsize(700, 600)
    window.configure(bg="#F8FAFC")

    # Header
    header = tk.Frame(window, bg="#1E3A8A", pady=16, padx=25)
    header.pack(fill="x")

    tk.Label(
        header,
        text="📋 My Complaints & Grievance History",
        font=("Segoe UI", 18, "bold"),
        fg="#FFFFFF",
        bg="#1E3A8A"
    ).pack(anchor="w")

    tk.Label(
        header,
        text="Track the lifecycle status, location details, and photo evidence for your submitted tickets",
        font=("Segoe UI", 9),
        fg="#93C5FD",
        bg="#1E3A8A"
    ).pack(anchor="w", pady=(2, 0))

    # Filter Bar
    filter_bar = tk.Frame(window, bg="#FFFFFF", padx=20, pady=10, relief="solid", bd=1)
    filter_bar.pack(fill="x", padx=15, pady=12)

    tk.Label(
        filter_bar,
        text="Filter by Status:",
        font=("Segoe UI", 10, "bold"),
        fg="#334155",
        bg="#FFFFFF"
    ).pack(side="left", padx=(0, 10))

    status_filter = tk.StringVar(value="All")
    status_menu = ttk.Combobox(
        filter_bar,
        textvariable=status_filter,
        values=["All", "Pending", "In Progress", "Resolved"],
        state="readonly",
        width=15,
        font=("Segoe UI", 9)
    )
    status_menu.pack(side="left", padx=(0, 15))

    # Scrollable Content Area
    canvas_frame = tk.Frame(window, bg="#F8FAFC")
    canvas_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    canvas = tk.Canvas(canvas_frame, bg="#F8FAFC", highlightthickness=0)
    scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)

    scrollable_frame = tk.Frame(canvas, bg="#F8FAFC")
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def _on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind("<Configure>", _on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Filter Action
    def apply_filter():
        load_complaints(scrollable_frame, student_id, status_filter.get())

    filter_btn = tk.Button(
        filter_bar,
        text="Apply Filter",
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
        command=apply_filter
    )
    filter_btn.pack(side="left")

    status_menu.bind("<<ComboboxSelected>>", lambda e: apply_filter())

    # Initial Load
    load_complaints(scrollable_frame, student_id, "All")