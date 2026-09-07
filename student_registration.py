import tkinter as tk
from tkinter import messagebox
import sqlite3


def register_student():

    name = name_entry.get().strip()
    email = email_entry.get().strip()
    password = password_entry.get()

    # Check empty fields
    if name == "" or email == "" or password == "":
        messagebox.showerror(
            "Error",
            "Please fill in all fields."
        )
        return

    # Connect to database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO students (name, email, password)
            VALUES (?, ?, ?)
        """, (name, email, password))

        conn.commit()

        messagebox.showinfo(
            "Success",
            "Registration successful!"
        )

        # Clear fields
        name_entry.delete(0, tk.END)
        email_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)

    except sqlite3.IntegrityError:

        messagebox.showerror(
            "Error",
            "This email is already registered."
        )

    conn.close()


# ---------------- MAIN WINDOW ----------------

root = tk.Tk()

root.title("College Complaint Tracker")
root.geometry("500x600")

root.resizable(False, False)


# Main container
main_frame = tk.Frame(root)
main_frame.pack(expand=True)


# Application title
title = tk.Label(
    main_frame,
    text="College Complaint Tracker",
    font=("Arial", 22, "bold")
)

title.pack(pady=(30, 5))


# Subtitle
subtitle = tk.Label(
    main_frame,
    text="Student Registration",
    font=("Arial", 14)
)

subtitle.pack(pady=(0, 30))


# Name
name_label = tk.Label(
    main_frame,
    text="Name",
    font=("Arial", 12)
)

name_label.pack(anchor="w")

name_entry = tk.Entry(
    main_frame,
    width=40,
    font=("Arial", 11)
)

name_entry.pack(pady=(5, 15))


# Email
email_label = tk.Label(
    main_frame,
    text="Email",
    font=("Arial", 12)
)

email_label.pack(anchor="w")

email_entry = tk.Entry(
    main_frame,
    width=40,
    font=("Arial", 11)
)

email_entry.pack(pady=(5, 15))


# Password
password_label = tk.Label(
    main_frame,
    text="Password",
    font=("Arial", 12)
)

password_label.pack(anchor="w")

password_entry = tk.Entry(
    main_frame,
    width=40,
    font=("Arial", 11),
    show="*"
)

password_entry.pack(pady=(5, 20))


# Register button
register_button = tk.Button(
    main_frame,
    text="Register",
    width=25,
    height=2,
    font=("Arial", 11, "bold"),
    command=register_student
)

register_button.pack(pady=20)


# Footer
footer = tk.Label(
    main_frame,
    text="College Complaint Tracker",
    font=("Arial", 9)
)

footer.pack(pady=30)


root.mainloop()