import tkinter as tk
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def open_student_login():
    root.destroy()
    subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "student_login.py")])


def open_student_register():
    root.destroy()
    subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "student_registration.py")])


def open_admin_login():
    root.destroy()
    subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "admin_login.py")])


def launch_web_portal():
    root.destroy()
    subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "run_app.py")])


root = tk.Tk()

root.title("College Complaint & Solution Tracker")
root.geometry("800x560")


# Title
title = tk.Label(
    root,
    text="College Complaint & Solution Tracker",
    font=("Arial", 22, "bold")
)

title.pack(pady=(35, 10))

subtitle = tk.Label(
    root,
    text="Modern University Grievance Redressal System",
    font=("Arial", 12),
    fg="#64748B"
)
subtitle.pack(pady=(0, 25))

# Web App Primary Button
web_button = tk.Button(
    root,
    text="🌐 Launch Modern Web Portal (Recommended)",
    width=38,
    font=("Arial", 11, "bold"),
    bg="#2563EB",
    fg="#FFFFFF",
    activebackground="#1D4ED8",
    activeforeground="#FFFFFF",
    relief="flat",
    cursor="hand2",
    command=launch_web_portal
)
web_button.pack(pady=(0, 20), ipady=8)

separator = tk.Label(
    root,
    text="─── or launch desktop GUI modules ───",
    font=("Arial", 9),
    fg="#94A3B8"
)
separator.pack(pady=(0, 10))



# Student Login Button
student_login = tk.Button(
    root,
    text="Student Login",
    width=25,
    font=("Arial", 11),
    command=open_student_login
)

student_login.pack(pady=10)


# Student Registration Button
student_register = tk.Button(
    root,
    text="Student Registration",
    width=25,
    font=("Arial", 11),
    command=open_student_register
)

student_register.pack(pady=10)


# Admin Login Button
admin_login = tk.Button(
    root,
    text="Admin Login",
    width=25,
    font=("Arial", 11),
    command=open_admin_login
)

admin_login.pack(pady=10)


# Exit Button
exit_button = tk.Button(
    root,
    text="Exit",
    width=25,
    font=("Arial", 11),
    command=root.destroy
)

exit_button.pack(pady=10)


root.mainloop()