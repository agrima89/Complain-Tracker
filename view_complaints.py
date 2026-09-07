import tkinter as tk
from tkinter import ttk
import sqlite3


def load_complaints(window, student_id, status_filter):

    # Remove old complaint frames
    for widget in window.winfo_children():

        if getattr(widget, "is_complaint_frame", False):
            widget.destroy()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if status_filter == "All":

        cursor.execute("""
            SELECT complaint_id, category, description,
                   location, priority, status, date
            FROM complaints
            WHERE student_id = ?
        """, (student_id,))

    else:

        cursor.execute("""
            SELECT complaint_id, category, description,
                   location, priority, status, date
            FROM complaints
            WHERE student_id = ?
            AND status = ?
        """, (student_id, status_filter))

    complaints = cursor.fetchall()

    conn.close()

    if not complaints:

        label = tk.Label(
            window,
            text="No complaints found.",
            font=("Arial", 14)
        )

        label.pack(pady=30)

        label.is_complaint_frame = True

        return

    # Display complaints
    for complaint in complaints:

        complaint_text = (
            f"Complaint ID: {complaint[0]}\n"
            f"Category: {complaint[1]}\n"
            f"Description: {complaint[2]}\n"
            f"Location: {complaint[3]}\n"
            f"Priority: {complaint[4]}\n"
            f"Status: {complaint[5]}\n"
            f"Date: {complaint[6]}"
        )

        frame = tk.Frame(
            window,
            relief="solid",
            borderwidth=1,
            padx=15,
            pady=10
        )

        frame.pack(
            fill="x",
            padx=30,
            pady=10
        )

        frame.is_complaint_frame = True

        tk.Label(
            frame,
            text=complaint_text,
            justify="left",
            anchor="w",
            font=("Arial", 11)
        ).pack(fill="x")


def view_complaints(student_id):

    window = tk.Toplevel()
    window.title("My Complaints")
    window.geometry("700x600")

    # Heading
    title = tk.Label(
        window,
        text="My Complaints",
        font=("Arial", 22, "bold")
    )

    title.pack(pady=20)

    # Status filter
    tk.Label(
        window,
        text="Filter by Status:",
        font=("Arial", 12)
    ).pack()

    status_filter = tk.StringVar()
    status_filter.set("All")

    status_menu = ttk.Combobox(
        window,
        textvariable=status_filter,
        values=[
            "All",
            "Pending",
            "In Progress",
            "Resolved"
        ],
        state="readonly",
        width=25
    )

    status_menu.pack(pady=8)

    # Filter button
    filter_button = tk.Button(
        window,
        text="Filter Complaints",
        width=20,
        command=lambda: load_complaints(
            window,
            student_id,
            status_filter.get()
        )
    )

    filter_button.pack(pady=10)

    # Load all complaints initially
    load_complaints(
        window,
        student_id,
        "All"
    )