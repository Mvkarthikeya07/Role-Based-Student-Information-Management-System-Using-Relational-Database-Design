from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import pandas as pd
import secrets
import string
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for login sessions

# Security Questions Pool
SECURITY_QUESTIONS = [
    "What is your first pet's name?",
    "What is your mother's maiden name?",
    "In what city were you born?",
    "What is your favorite book?",
    "What was the name of your primary school?",
    "What is your favorite movie?",
    "What was your first car model?",
    "What is your favorite food?",
    "What is the name of the street you grew up on?",
    "What was your first job?"
]

# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect("students.db")
    cur = conn.cursor()

    # Users (Teacher & Student accounts)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            role TEXT,
            security_question TEXT,
            security_answer TEXT
        )
    """)

    # Students Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            course TEXT,
            class TEXT,
            section TEXT,
            parent_phone TEXT,
            parent_email TEXT
        )
    """)

    # Password Reset Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS password_reset (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            token TEXT UNIQUE,
            created_at TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)

    # Add default teacher & student if not exists
    cur.execute("SELECT * FROM users WHERE username=?", ("teacher",))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password, email, role, security_question, security_answer) VALUES (?, ?, ?, ?, ?, ?)", 
                   ("teacher", "1234", "teacher@example.com", "teacher", "What is your first pet's name?", "fluffy"))

    cur.execute("SELECT * FROM users WHERE username=?", ("student",))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password, email, role, security_question, security_answer) VALUES (?, ?, ?, ?, ?, ?)", 
                   ("student", "1234", "student@example.com", "student", "What is your first pet's name?", "buddy"))

    conn.commit()
    conn.close()

init_db()

# ---------- Routes ----------
@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    if session["role"] == "teacher":
        return redirect(url_for("teacher_dashboard"))
    else:
        return redirect(url_for("student_dashboard"))

# ---------- Login ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("students.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["username"] = user[1]  # username
            session["role"] = user[4]  # role (was user[3] - now corrected for new schema)
            return redirect(url_for("home"))
        else:
            error = "Invalid Credentials"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- Create Account / Registration ----------
@app.route("/create-account", methods=["GET", "POST"])
def create_account():
    error = None
    success = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        email = request.form["email"]
        role = request.form["role"]
        security_question = request.form["security_question"]
        security_answer = request.form["security_answer"].lower().strip()
        
        # Validate passwords match
        if password != confirm_password:
            error = "Passwords do not match"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS)
        
        # Validate password length
        if len(password) < 4:
            error = "Password must be at least 4 characters long"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS)
        
        # Validate security answer
        if not security_answer:
            error = "Security answer is required"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS)
        
        conn = sqlite3.connect("students.db")
        cur = conn.cursor()
        
        # Check if username already exists
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        if cur.fetchone():
            conn.close()
            error = "Username already exists"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS)
        
        try:
            # Insert new user with security question
            cur.execute("INSERT INTO users (username, password, email, role, security_question, security_answer) VALUES (?, ?, ?, ?, ?, ?)", 
                       (username, password, email, role, security_question, security_answer))
            conn.commit()
            conn.close()
            success = "Account created successfully! You can now login."
            return render_template("create_account.html", success=success, questions=SECURITY_QUESTIONS)
        except Exception as e:
            conn.close()
            error = f"Error creating account: {str(e)}"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS)
    
    return render_template("create_account.html", questions=SECURITY_QUESTIONS)

# ---------- Teacher Dashboard ----------
@app.route("/teacher")
def teacher_dashboard():
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))

    conn = sqlite3.connect("students.db")
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return render_template("teacher_dashboard.html", students=students)

@app.route("/add", methods=["POST"])
def add_student():
    name = request.form["name"]
    course = request.form["course"]
    class_name = request.form["class"]
    section = request.form["section"]
    parent_phone = request.form["parent_phone"]
    parent_email = request.form["parent_email"]
    
    conn = sqlite3.connect("students.db")
    conn.execute("INSERT INTO students (name, course, class, section, parent_phone, parent_email) VALUES (?, ?, ?, ?, ?, ?)", 
                 (name, course, class_name, section, parent_phone, parent_email))
    conn.commit()
    conn.close()
    return redirect(url_for("teacher_dashboard"))

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    conn = sqlite3.connect("students.db")
    if request.method == "POST":
        name = request.form["name"]
        course = request.form["course"]
        class_name = request.form["class"]
        section = request.form["section"]
        parent_phone = request.form["parent_phone"]
        parent_email = request.form["parent_email"]
        
        conn.execute("UPDATE students SET name=?, course=?, class=?, section=?, parent_phone=?, parent_email=? WHERE id=?", 
                    (name, course, class_name, section, parent_phone, parent_email, id))
        conn.commit()
        conn.close()
        return redirect(url_for("teacher_dashboard"))
    student = conn.execute("SELECT * FROM students WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("edit.html", student=student)

@app.route("/delete/<int:id>")
def delete_student(id):
    conn = sqlite3.connect("students.db")
    conn.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("teacher_dashboard"))

@app.route("/search", methods=["POST"])
def search_student():
    keyword = request.form["keyword"]
    conn = sqlite3.connect("students.db")
    students = conn.execute("SELECT * FROM students WHERE name LIKE ? OR course LIKE ? OR class LIKE ? OR section LIKE ?", 
                            ('%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%')).fetchall()
    conn.close()
    return render_template("teacher_dashboard.html", students=students)

@app.route("/export")
def export_students():
    conn = sqlite3.connect("students.db")
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    df.to_csv("students.csv", index=False)
    return send_file("students.csv", as_attachment=True)

# ---------- Student Dashboard ----------
@app.route("/student")
def student_dashboard():
    if "role" not in session or session["role"] != "student":
        return redirect(url_for("login"))
    conn = sqlite3.connect("students.db")
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return render_template("student_dashboard.html", students=students)

# ---------- Forgot Password ----------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    error = None
    success = None
    show_reset_form = False
    username_verified = None
    security_question = None
    show_password_form = False
    
    if request.method == "POST":
        step = request.form.get("step", "verify_username")
        
        if step == "verify_username":
            # Step 1: Verify username
            username = request.form.get("username", "").strip()
            if not username:
                error = "Please enter a username"
            else:
                conn = sqlite3.connect("students.db")
                user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
                conn.close()
                
                if user:
                    # Correct column indices: 5=security_question, 6=security_answer
                    security_question = user[5]
                    username_verified = username
                    show_reset_form = True
                else:
                    error = "Username not found"
        
        elif step == "verify_security":
            # Step 2: Verify security question
            username = request.form.get("username", "").strip()
            security_answer = request.form.get("security_answer", "").lower().strip()
            
            conn = sqlite3.connect("students.db")
            user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            conn.close()
            
            if user:
                # Correct column index: 6=security_answer
                stored_answer = user[6].lower().strip() if user[6] else ""
                if stored_answer == security_answer:
                    username_verified = username
                    show_password_form = True
                    show_reset_form = True
                else:
                    error = "Incorrect security answer"
                    security_question = user[5]
                    username_verified = username
                    show_reset_form = True
            else:
                error = "Username not found"
        
        elif step == "change_password":
            # Step 3: Change password
            username = request.form.get("username", "").strip()
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")
            
            if new_password != confirm_password:
                error = "Passwords do not match"
                show_password_form = True
                show_reset_form = True
                username_verified = username
            elif len(new_password) < 4:
                error = "Password must be at least 4 characters long"
                show_password_form = True
                show_reset_form = True
                username_verified = username
            else:
                conn = sqlite3.connect("students.db")
                conn.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
                conn.commit()
                conn.close()
                success = "Password reset successfully! You can now login."
    
    return render_template("forgot_password.html", error=error, success=success, 
                         show_reset_form=show_reset_form, username_verified=username_verified,
                         security_question=security_question, show_password_form=show_password_form)

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    conn = sqlite3.connect("students.db")
    reset_request = conn.execute("SELECT * FROM password_reset WHERE token=?", (token,)).fetchone()
    
    if not reset_request or datetime.fromisoformat(reset_request[4]) < datetime.now():
        conn.close()
        return render_template("reset_password.html", error="Reset link expired or invalid")
    
    if request.method == "POST":
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]
        
        if new_password == confirm_password:
            username = reset_request[1]
            conn.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
            conn.execute("DELETE FROM password_reset WHERE token=?", (token,))
            conn.commit()
            conn.close()
            return render_template("reset_password.html", success=True)
        else:
            conn.close()
            return render_template("reset_password.html", error="Passwords do not match")
    
    conn.close()
    return render_template("reset_password.html", token=token)

if __name__ == "__main__":
    app.run(debug=True)
