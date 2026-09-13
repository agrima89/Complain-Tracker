import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
import database
from student_dashboard import open_dashboard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def open_registration_window():
    root.destroy()
    subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "student_registration.py")])


def login_student():
    email = email_entry.get().strip()
    password = password_entry.get()

    if not email or not password:
        messagebox.showerror(
            "Input Error",
            "Please enter your Chandigarh University email and password."
        )
        return

    # Validate Chandigarh University email (@culkomail.in)
    is_valid, err_msg = database.is_valid_college_email(email)
    if not is_valid:
        messagebox.showerror(
            "Invalid Chandigarh University Email",
            err_msg
        )
        return

    student, auth_err = database.authenticate_student(email, password)

    if student:
        root.destroy()
        open_dashboard(student["student_id"], student["name"])
    else:
        messagebox.showerror(
            "Login Failed",
            auth_err or "Invalid Chandigarh University email or password. Please verify your credentials."
        )


# ---------------- MAIN WINDOW ----------------

root = tk.Tk()
root.title("CampusCare - Student Login")
root.geometry("520x640")
root.minsize(480, 580)
root.configure(bg="#F8FAFC")

# Main Container
container = tk.Frame(
    root,
    bg="#FFFFFF",
    padx=35,
    pady=30,
    relief="solid",
    bd=1,
    highlightthickness=1,
    highlightbackground="#E2E8F0"
)
container.pack(expand=True, fill="both", padx=30, pady=25)

# Logo / Icon
logo_label = tk.Label(
    container,
    text="🏫",
    font=("Segoe UI", 28),
    bg="#FFFFFF"
)
logo_label.pack(pady=(0, 5))

# Title
title = tk.Label(
    container,
    text="Student Portal Login",
    font=("Segoe UI", 18, "bold"),
    fg="#0F172A",
    bg="#FFFFFF"
)
title.pack(pady=(0, 4))

subtitle = tk.Label(
    container,
    text="Sign in using your official Chandigarh University email ID",
    font=("Segoe UI", 9),
    fg="#64748B",
    bg="#FFFFFF"
)
subtitle.pack(pady=(0, 20))

# Email Field
email_label = tk.Label(
    container,
    text="Chandigarh University Email *",
    font=("Segoe UI", 10, "bold"),
    fg="#334155",
    bg="#FFFFFF"
)
email_label.pack(anchor="w")

email_entry = tk.Entry(
    container,
    font=("Segoe UI", 11),
    bd=1,
    relief="solid",
    highlightthickness=1,
    highlightbackground="#CBD5E1",
    highlightcolor="#2563EB"
)
email_entry.pack(fill="x", pady=(4, 2), ipady=5)

email_hint = tk.Label(
    container,
    text="Use your official Chandigarh University email (@culkomail.in)",
    font=("Segoe UI", 8),
    fg="#64748B",
    bg="#FFFFFF"
)
email_hint.pack(anchor="w", pady=(0, 14))

# Password Field
password_label = tk.Label(
    container,
    text="Password *",
    font=("Segoe UI", 10, "bold"),
    fg="#334155",
    bg="#FFFFFF"
)
password_label.pack(anchor="w")

password_entry = tk.Entry(
    container,
    font=("Segoe UI", 11),
    show="*",
    bd=1,
    relief="solid",
    highlightthickness=1,
    highlightbackground="#CBD5E1",
    highlightcolor="#2563EB"
)
password_entry.pack(fill="x", pady=(4, 20), ipady=5)

# Login Button
login_button = tk.Button(
    container,
    text="Sign In  →",
    font=("Segoe UI", 11, "bold"),
    bg="#2563EB",
    fg="#FFFFFF",
    activebackground="#1D4ED8",
    activeforeground="#FFFFFF",
    relief="flat",
    bd=0,
    cursor="hand2",
    command=login_student
)
login_button.pack(fill="x", ipady=8, pady=(0, 15))

# Registration Prompt
register_frame = tk.Frame(container, bg="#FFFFFF")
register_frame.pack(pady=(10, 0))

register_text = tk.Label(
    register_frame,
    text="Don't have an account? ",
    font=("Segoe UI", 9),
    fg="#64748B",
    bg="#FFFFFF"
)
register_text.pack(side="left")

register_btn = tk.Button(
    register_frame,
    text="Register Now",
    font=("Segoe UI", 9, "bold"),
    fg="#2563EB",
    bg="#FFFFFF",
    activeforeground="#1D4ED8",
    activebackground="#FFFFFF",
    bd=0,
    relief="flat",
    cursor="hand2",
    command=open_registration_window
)
register_btn.pack(side="left")

# Bind Enter key
root.bind("<Return>", lambda e: login_student())

root.mainloop()