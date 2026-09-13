import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
import os
from PIL import Image, ImageTk
import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class ComplaintSubmissionForm:
    def __init__(self, parent, student_id):
        self.student_id = student_id
        self.parent = parent
        self.selected_photo_path = None
        self.photo_preview_image = None

        if parent is None:
            self.root = tk.Tk()
            self.is_toplevel = False
        else:
            self.root = tk.Toplevel(parent)
            self.is_toplevel = True

        self.root.title("Submit Campus Grievance - CampusCare")
        self.root.geometry("750x850")
        self.root.minsize(680, 720)
        self.root.configure(bg="#F8FAFC")

        self.setup_ui()

    def setup_ui(self):
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="#FFFFFF", background="#E2E8F0")

        # Top Header Bar
        header = tk.Frame(self.root, bg="#1E3A8A", pady=18, padx=25)
        header.pack(fill="x")

        title_lbl = tk.Label(
            header,
            text="📝 Submit a Campus Complaint",
            font=("Segoe UI", 18, "bold"),
            fg="#FFFFFF",
            bg="#1E3A8A"
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            header,
            text="Provide complete issue details and mandatory photo evidence for swift resolution",
            font=("Segoe UI", 9),
            fg="#93C5FD",
            bg="#1E3A8A"
        )
        subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # Main Scrollable Container
        canvas_frame = tk.Frame(self.root, bg="#F8FAFC")
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#F8FAFC", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = tk.Frame(self.canvas, bg="#F8FAFC", padx=25, pady=15)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def _on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)

        self.canvas.bind("<Configure>", _on_canvas_configure)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mousewheel scroll binding
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Build Section Cards
        self.build_issue_section()
        self.build_photo_section()
        self.build_location_section()
        self.build_priority_section()
        self.build_submit_section()

    def create_card(self, title_text, icon=""):
        card = tk.Frame(
            self.scrollable_frame,
            bg="#FFFFFF",
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground="#E2E8F0"
        )
        card.pack(fill="x", pady=(0, 15))

        header_frame = tk.Frame(card, bg="#F1F5F9", padx=16, pady=10)
        header_frame.pack(fill="x")

        tk.Label(
            header_frame,
            text=f"{icon} {title_text}",
            font=("Segoe UI", 11, "bold"),
            fg="#1E293B",
            bg="#F1F5F9"
        ).pack(anchor="w")

        body = tk.Frame(card, bg="#FFFFFF", padx=18, pady=15)
        body.pack(fill="x")
        return body

    def build_issue_section(self):
        body = self.create_card("What is the Issue?", "📌")

        # Category
        tk.Label(
            body,
            text="Complaint Category *",
            font=("Segoe UI", 10, "bold"),
            fg="#334155",
            bg="#FFFFFF"
        ).pack(anchor="w")

        self.category_var = tk.StringVar(value="Select Category")
        categories = [
            "Electrical",
            "Cleaning",
            "Classroom",
            "Hostel",
            "Wi-Fi/Internet",
            "Library",
            "Infrastructure",
            "Other"
        ]
        self.category_dropdown = ttk.Combobox(
            body,
            textvariable=self.category_var,
            values=categories,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.category_dropdown.pack(fill="x", pady=(4, 12), ipady=3)

        # Description
        tk.Label(
            body,
            text="Detailed Description *",
            font=("Segoe UI", 10, "bold"),
            fg="#334155",
            bg="#FFFFFF"
        ).pack(anchor="w")

        tk.Label(
            body,
            text="Explain: What happened? What is damaged/wrong? Where exactly? Any other useful info.",
            font=("Segoe UI", 8),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 4))

        self.description_text = tk.Text(
            body,
            height=4,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            highlightcolor="#2563EB",
            wrap="word"
        )
        self.description_text.pack(fill="x", pady=(0, 5))

    def build_photo_section(self):
        body = self.create_card("Upload Photo Evidence (Mandatory)", "📸")

        tk.Label(
            body,
            text="A clear photo of the damaged/faulty item or location is strictly required.",
            font=("Segoe UI", 9),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 10))

        upload_row = tk.Frame(body, bg="#FFFFFF")
        upload_row.pack(fill="x", pady=(0, 8))

        # Upload Button
        upload_btn = tk.Button(
            upload_row,
            text="📁 Select Photo (JPG, PNG)",
            font=("Segoe UI", 10, "bold"),
            bg="#0284C7",
            fg="#FFFFFF",
            activebackground="#0369A1",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.browse_photo
        )
        upload_btn.pack(side="left", padx=(0, 12))

        # Remove Button
        self.remove_photo_btn = tk.Button(
            upload_row,
            text="✕ Remove Photo",
            font=("Segoe UI", 9),
            bg="#FEE2E2",
            fg="#DC2626",
            activebackground="#FECACA",
            activeforeground="#991B1B",
            relief="flat",
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.remove_photo,
            state="disabled"
        )
        self.remove_photo_btn.pack(side="left")

        # Filename label
        self.photo_filename_lbl = tk.Label(
            body,
            text="No photo selected (Required *).",
            font=("Segoe UI", 9, "italic"),
            fg="#DC2626",
            bg="#FFFFFF"
        )
        self.photo_filename_lbl.pack(anchor="w", pady=(6, 8))

        # Image preview container
        self.preview_frame = tk.Frame(body, bg="#F1F5F9", width=140, height=100, relief="solid", bd=1)
        self.preview_frame.pack(anchor="w", pady=(0, 5))
        self.preview_frame.pack_propagate(False)

        self.preview_label = tk.Label(
            self.preview_frame,
            text="Image Preview",
            font=("Segoe UI", 8),
            fg="#94A3B8",
            bg="#F1F5F9"
        )
        self.preview_label.pack(expand=True)

    def browse_photo(self):
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.webp"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(
            title="Select Complaint Evidence Photo",
            filetypes=filetypes
        )
        if filename:
            self.selected_photo_path = filename
            base_name = os.path.basename(filename)
            self.photo_filename_lbl.config(
                text=f"Selected: {base_name}",
                font=("Segoe UI", 9, "bold"),
                fg="#059669"
            )
            self.remove_photo_btn.config(state="normal")
            self.update_image_preview(filename)

    def remove_photo(self):
        self.selected_photo_path = None
        self.photo_preview_image = None
        self.photo_filename_lbl.config(
            text="No photo selected (Required *).",
            font=("Segoe UI", 9, "italic"),
            fg="#DC2626"
        )
        self.remove_photo_btn.config(state="disabled")
        self.preview_label.config(image="", text="Image Preview")

    def update_image_preview(self, filepath):
        try:
            img = Image.open(filepath)
            img.thumbnail((135, 95))
            self.photo_preview_image = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.photo_preview_image, text="")
        except Exception:
            self.preview_label.config(image="", text="Preview unavailable")

    def build_location_section(self):
        body = self.create_card("Where is the Issue?", "📍")

        # 1. Block Selection
        tk.Label(
            body,
            text="Select Block *",
            font=("Segoe UI", 10, "bold"),
            fg="#334155",
            bg="#FFFFFF"
        ).pack(anchor="w")

        blocks = [
            "Block A",
            "Block B",
            "Block C",
            "Block D",
            "Block E",
            "Block F",
            "Other"
        ]
        self.block_var = tk.StringVar(value="Block A")
        self.block_dropdown = ttk.Combobox(
            body,
            textvariable=self.block_var,
            values=blocks,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.block_dropdown.pack(fill="x", pady=(4, 12), ipady=3)

        # 2. Exact Location Fields Sub-section
        tk.Label(
            body,
            text="Exact Location Details",
            font=("Segoe UI", 10, "bold"),
            fg="#1E293B",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 2))

        tk.Label(
            body,
            text="Specify floor, room number, wing/side, and nearby landmarks for accurate inspection.",
            font=("Segoe UI", 8),
            fg="#64748B",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 10))

        # Row 1: Floor No. & Room No.
        row1 = tk.Frame(body, bg="#FFFFFF")
        row1.pack(fill="x", pady=(0, 10))

        # Floor
        floor_col = tk.Frame(row1, bg="#FFFFFF")
        floor_col.pack(side="left", fill="x", expand=True, padx=(0, 10))

        tk.Label(
            floor_col,
            text="Floor No.",
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#FFFFFF"
        ).pack(anchor="w")

        self.floor_var = tk.StringVar(value="Ground Floor")
        floor_options = [
            "Ground Floor",
            "1st Floor",
            "2nd Floor",
            "3rd Floor",
            "4th Floor",
            "5th Floor",
            "Basement",
            "Terrace / Rooftop",
            "Other"
        ]
        self.floor_dropdown = ttk.Combobox(
            floor_col,
            textvariable=self.floor_var,
            values=floor_options,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.floor_dropdown.pack(fill="x", pady=(2, 0), ipady=3)

        # Room No.
        room_col = tk.Frame(row1, bg="#FFFFFF")
        room_col.pack(side="left", fill="x", expand=True)

        tk.Label(
            room_col,
            text="Room No. / Lab (e.g. F-204, LH-1)",
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#FFFFFF"
        ).pack(anchor="w")

        self.room_entry = tk.Entry(
            room_col,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            highlightcolor="#2563EB"
        )
        self.room_entry.pack(fill="x", pady=(2, 0), ipady=4)

        # Row 2: Side & Nearby Known Area
        row2 = tk.Frame(body, bg="#FFFFFF")
        row2.pack(fill="x", pady=(0, 10))

        # Side: RHS / LHS
        side_col = tk.Frame(row2, bg="#FFFFFF")
        side_col.pack(side="left", fill="x", expand=True, padx=(0, 10))

        tk.Label(
            side_col,
            text="Corridor Side",
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#FFFFFF"
        ).pack(anchor="w")

        self.side_var = tk.StringVar(value="RHS")
        side_options = ["RHS (Right Hand Side)", "LHS (Left Hand Side)", "Center / Open Area", "N/A"]
        self.side_dropdown = ttk.Combobox(
            side_col,
            textvariable=self.side_var,
            values=side_options,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.side_dropdown.pack(fill="x", pady=(2, 0), ipady=3)

        # Nearby Known Area
        nearby_col = tk.Frame(row2, bg="#FFFFFF")
        nearby_col.pack(side="left", fill="x", expand=True)

        tk.Label(
            nearby_col,
            text="Nearby Known Area / Landmark",
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#FFFFFF"
        ).pack(anchor="w")

        self.nearby_entry = tk.Entry(
            nearby_col,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            highlightcolor="#2563EB"
        )
        self.nearby_entry.pack(fill="x", pady=(2, 0), ipady=4)

        # Additional Location Details
        tk.Label(
            body,
            text="Additional Location Details",
            font=("Segoe UI", 9, "bold"),
            fg="#475569",
            bg="#FFFFFF"
        ).pack(anchor="w", pady=(2, 0))

        self.additional_location_entry = tk.Entry(
            body,
            font=("Segoe UI", 10),
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            highlightcolor="#2563EB"
        )
        self.additional_location_entry.pack(fill="x", pady=(2, 0), ipady=4)

    def build_priority_section(self):
        body = self.create_card("Priority Level", "⚡")

        self.priority_var = tk.StringVar(value="Medium")

        priorities = [
            ("Low Priority", "Low", "Minor / routine maintenance"),
            ("Medium Priority", "Medium", "Standard response required"),
            ("High Priority", "High", "Urgent / safety hazard")
        ]

        p_row = tk.Frame(body, bg="#FFFFFF")
        p_row.pack(fill="x")

        for label_text, val, subtext in priorities:
            f = tk.Frame(p_row, bg="#F8FAFC", padx=10, pady=8, relief="solid", bd=1)
            f.pack(side="left", fill="x", expand=True, padx=4)

            rb = tk.Radiobutton(
                f,
                text=label_text,
                variable=self.priority_var,
                value=val,
                font=("Segoe UI", 9, "bold"),
                bg="#F8FAFC",
                activebackground="#F8FAFC"
            )
            rb.pack(anchor="w")

            tk.Label(
                f,
                text=subtext,
                font=("Segoe UI", 8),
                fg="#64748B",
                bg="#F8FAFC"
            ).pack(anchor="w", padx=(20, 0))

    def build_submit_section(self):
        btn_frame = tk.Frame(self.scrollable_frame, bg="#F8FAFC", pady=10)
        btn_frame.pack(fill="x", pady=(0, 25))

        submit_btn = tk.Button(
            btn_frame,
            text="✓  Submit Complaint Ticket",
            font=("Segoe UI", 12, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=25,
            pady=12,
            cursor="hand2",
            command=self.submit
        )
        submit_btn.pack(side="right")

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Segoe UI", 10),
            bg="#E2E8F0",
            fg="#334155",
            activebackground="#CBD5E1",
            activeforeground="#0F172A",
            relief="flat",
            bd=0,
            padx=18,
            pady=10,
            cursor="hand2",
            command=self.root.destroy
        )
        cancel_btn.pack(side="right", padx=(0, 10))

    def submit(self):
        category = self.category_var.get().strip()
        description = self.description_text.get("1.0", tk.END).strip()
        block = self.block_var.get().strip()
        floor_no = self.floor_var.get().strip()
        room_no = self.room_entry.get().strip()
        corridor_side = self.side_var.get().strip()
        nearby_area = self.nearby_entry.get().strip()
        additional_location = self.additional_location_entry.get().strip()
        priority = self.priority_var.get().strip()

        # 1. Category validation
        if not category or category == "Select Category":
            messagebox.showerror(
                "Validation Error",
                "Please select a valid complaint category."
            )
            return

        # 2. Description validation
        if not description:
            messagebox.showerror(
                "Validation Error",
                "Please provide a detailed description of the issue."
            )
            return

        if len(description) < 5:
            messagebox.showerror(
                "Validation Error",
                "Please provide a more descriptive explanation of the problem."
            )
            return

        # 3. Mandatory Photo Validation
        if not self.selected_photo_path or not os.path.isfile(self.selected_photo_path):
            messagebox.showerror(
                "Photo Evidence Required",
                "Photo evidence is required to submit this complaint.\n\nPlease click 'Select Photo' to attach an image."
            )
            return

        # 4. Block Validation
        if not block:
            messagebox.showerror(
                "Validation Error",
                "Please select the campus block where the issue is located."
            )
            return

        # Save photo with collision-free filename
        saved_rel_photo_path = database.save_complaint_image(self.selected_photo_path)
        if not saved_rel_photo_path:
            messagebox.showerror(
                "Error",
                "Failed to save the evidence photo. Please try choosing the image again."
            )
            return

        today_str = str(date.today())

        complaint_id = database.create_complaint(
            student_id=self.student_id,
            category=category,
            description=description,
            photo_path=saved_rel_photo_path,
            block=block,
            floor_no=floor_no,
            room_no=room_no,
            corridor_side=corridor_side,
            nearby_area=nearby_area,
            additional_location=additional_location,
            priority=priority,
            date_str=today_str
        )

        messagebox.showinfo(
            "Ticket Submitted",
            f"Your complaint ticket #{complaint_id:03d} has been submitted successfully!\n\n"
            f"Category: {category}\n"
            f"Location: {block}, {floor_no}\n"
            f"Evidence photo saved securely."
        )

        self.root.destroy()


def open_complaint_form(student_id):
    form = ComplaintSubmissionForm(None, student_id)
    if not form.is_toplevel:
        form.root.mainloop()


if __name__ == "__main__":
    open_complaint_form(1)