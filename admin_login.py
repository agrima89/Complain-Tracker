import tkinter as tk
from tkinter import messagebox
import sqlite3
from admin_dashboard import open_admin_dashboard


def admin_login():

    username = username_entry.get()
    password = password_entry.get()

    # Check empty fields
    if username == "" or password == "":
        messagebox.showerror(
            "Error",
            "All fields are required"
        )
        return

    # Connect to database
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM admins
        WHERE username = ? AND password = ?
    """, (username, password))

    admin = cursor.fetchone()

    conn.close()

    # Check login
    if admin:
        root.destroy()
        open_admin_dashboard()

    else:
        messagebox.showerror(
            "Error",
            "Invalid username or password"
        )


# Main window
root = tk.Tk()

root.title("Admin Login")
root.geometry("450x350")


# Title
title = tk.Label(
    root,
    text="Admin Login",
    font=("Arial", 20, "bold")
)
title.pack(pady=30)


# Username
tk.Label(
    root,
    text="Username",
    font=("Arial", 12)
).pack()

username_entry = tk.Entry(
    root,
    width=35
)
username_entry.pack(pady=5)


# Password
tk.Label(
    root,
    text="Password",
    font=("Arial", 12)
).pack()

password_entry = tk.Entry(
    root,
    width=35,
    show="*"
)
password_entry.pack(pady=5)


# Login button
login_button = tk.Button(
    root,
    text="Login",
    width=20,
    command=admin_login
)
login_button.pack(pady=25)


root.mainloop()