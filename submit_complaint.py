import tkinter as tk
from tkinter import messagebox
from datetime import date
import sqlite3


def submit_complaint(student_id):

    category = category_var.get()
    description = description_entry.get("1.0", tk.END).strip()
    location = location_entry.get()
    priority = priority_var.get()

    # Check empty fields
    if category == "Select Category":
        messagebox.showerror("Error", "Please select a category")
        return

    if description == "":
        messagebox.showerror("Error", "Please enter a description")
        return

    if location == "":
        messagebox.showerror("Error", "Please enter the location")
        return

    # Connect to database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO complaints
        (student_id, category, description, location, priority, status, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id,
        category,
        description,
        location,
        priority,
        "Pending",
        str(date.today())
    ))

    conn.commit()
    conn.close()

    messagebox.showinfo(
        "Success",
        "Complaint submitted successfully!"
    )

    root.destroy()


def open_complaint_form(student_id):

    global root
    global category_var
    global description_entry
    global location_entry
    global priority_var

    try:
        root = tk.Toplevel()
    except Exception:
        root = tk.Tk()

    root.title("Submit Complaint")
    root.geometry("500x550")

    # Heading
    title = tk.Label(
        root,
        text="Submit Complaint",
        font=("Arial", 22, "bold")
    )
    title.pack(pady=25)

    # Category
    tk.Label(
        root,
        text="Category",
        font=("Arial", 12)
    ).pack()

    category_var = tk.StringVar()
    category_var.set("Select Category")

    category_menu = tk.OptionMenu(
        root,
        category_var,
        "Electrical",
        "Cleaning",
        "Classroom",
        "Hostel",
        "Wi-Fi/Internet",
        "Library",
        "Infrastructure",
        "Other"
    )

    category_menu.config(width=25)
    category_menu.pack(pady=8)

    # Description
    tk.Label(
        root,
        text="Description",
        font=("Arial", 12)
    ).pack()

    description_entry = tk.Text(
        root,
        width=40,
        height=6
    )
    description_entry.pack(pady=8)

    # Location
    tk.Label(
        root,
        text="Location",
        font=("Arial", 12)
    ).pack()

    location_entry = tk.Entry(
        root,
        width=40
    )
    location_entry.pack(pady=8)

    # Priority
    tk.Label(
        root,
        text="Priority",
        font=("Arial", 12)
    ).pack()

    priority_var = tk.StringVar()
    priority_var.set("Medium")

    priority_menu = tk.OptionMenu(
        root,
        priority_var,
        "Low",
        "Medium",
        "High"
    )

    priority_menu.config(width=25)
    priority_menu.pack(pady=8)

    # Submit button
    submit_button = tk.Button(
        root,
        text="Submit Complaint",
        width=25,
        height=2,
        command=lambda: submit_complaint(student_id)
    )

    submit_button.pack(pady=25)

    if isinstance(root, tk.Tk):
        root.mainloop()