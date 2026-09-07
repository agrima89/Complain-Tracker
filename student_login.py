import tkinter as tk
from tkinter import messagebox
import sqlite3

from student_dashboard import open_dashboard


def login_student():

    email = email_entry.get().strip()
    password = password_entry.get()

    if email == "" or password == "":
        messagebox.showerror(
            "Error",
            "Please enter email and password."
        )
        return

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM students
        WHERE email = ? AND password = ?
    """, (email, password))

    student = cursor.fetchone()

    conn.close()

    if student:
        root.destroy()
        open_dashboard(student[0], student[1])

    else:
        messagebox.showerror(
            "Login Failed",
            "Invalid email or password."
        )


# ---------------- MAIN WINDOW ----------------

root = tk.Tk()

root.title("College Complaint Tracker")
root.geometry("500x550")

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
    text="Student Login",
    font=("Arial", 14)
)

subtitle.pack(pady=(0, 30))


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


# Login button
login_button = tk.Button(
    main_frame,
    text="Login",
    width=25,
    height=2,
    font=("Arial", 11, "bold"),
    command=login_student
)

login_button.pack(pady=20)


# Footer
footer = tk.Label(
    main_frame,
    text="College Complaint Tracker",
    font=("Arial", 9)
)

footer.pack(pady=30)


root.mainloop()