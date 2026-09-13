import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def open_login_window():
    root.destroy()
    subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "student_login.py")])


def register_student():
    name = name_entry.get().strip()
    email = email_entry.get().strip()
    password = password_entry.get()

    # Check empty fields
    if not name or not email or not password:
        messagebox.showerror(
            "Validation Error",
            "All fields are required. Please fill in your name, Chandigarh University email, and password."
        )
        return

    if len(password) < 4:
        messagebox.showerror(
            "Validation Error",
            "Password must be at least 4 characters long."
        )
        return

    # Enforce Chandigarh University email validation
    is_valid, err_msg = database.is_valid_college_email(email)
    if not is_valid:
        messagebox.showerror(
            "Invalid Chandigarh University Email",
            err_msg
        )
        return

    success, result = database.register_new_student(name, email, password)

    if success:
        messagebox.showinfo(
            "Registration Successful",
            "Your student account has been created successfully!\nYou can now log in with your official Chandigarh University email."
        )
        # Clear fields
        name_entry.delete(0, tk.END)
        email_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)

        # Redirect to login
        open_login_window()
    else:
        messagebox.showerror(
            "Registration Failed",
            result
        )


# ---------------- MAIN WINDOW ----------------

root = tk.Tk()
root.title("CampusCare - Student Registration")
root.geometry("520x680")
root.minsize(480, 620)
root.configure(bg="#F8FAFC")

# Main Container
container = tk.Frame(root, bg="#FFFFFF", padx=35, pady=30, relief="solid", bd=1, highlightthickness=1, highlightbackground="#E2E8F0")
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
    text="Create Student Account",
    font=("Segoe UI", 18, "bold"),
    fg="#0F172A",
    bg="#FFFFFF"
)
title.pack(pady=(0, 4))

subtitle = tk.Label(
    container,
    text="Register using your official Chandigarh University email ID",
    font=("Segoe UI", 9),
    fg="#64748B",
    bg="#FFFFFF"
)
subtitle.pack(pady=(0, 20))

# Name Field
name_label = tk.Label(
    container,
    text="Full Name *",
    font=("Segoe UI", 10, "bold"),
    fg="#334155",
    bg="#FFFFFF"
)
name_label.pack(anchor="w")

name_entry = tk.Entry(
    container,
    font=("Segoe UI", 11),
    bd=1,
    relief="solid",
    highlightthickness=1,
    highlightbackground="#CBD5E1",
    highlightcolor="#2563EB"
)
name_entry.pack(fill="x", pady=(4, 14), ipady=5)

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
    bg="#FFFFFF",
    justify="left"
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

# Register Button
register_button = tk.Button(
    container,
    text="Complete Registration  →",
    font=("Segoe UI", 11, "bold"),
    bg="#2563EB",
    fg="#FFFFFF",
    activebackground="#1D4ED8",
    activeforeground="#FFFFFF",
    relief="flat",
    bd=0,
    cursor="hand2",
    command=register_student
)
register_button.pack(fill="x", ipady=8, pady=(0, 15))

# Already have an account row
signin_frame = tk.Frame(container, bg="#FFFFFF")
signin_frame.pack(pady=(10, 0))

signin_text = tk.Label(
    signin_frame,
    text="Already have an account? ",
    font=("Segoe UI", 9),
    fg="#64748B",
    bg="#FFFFFF"
)
signin_text.pack(side="left")

signin_btn = tk.Button(
    signin_frame,
    text="Sign In",
    font=("Segoe UI", 9, "bold"),
    fg="#2563EB",
    bg="#FFFFFF",
    activeforeground="#1D4ED8",
    activebackground="#FFFFFF",
    bd=0,
    relief="flat",
    cursor="hand2",
    command=open_login_window
)
signin_btn.pack(side="left")

# Bind Enter key
root.bind("<Return>", lambda e: register_student())

root.mainloop()