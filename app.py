import os
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from db import DatabaseOps
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")  # Required for login sessions

# Initialize database connection
db = DatabaseOps()

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

        # Use Supabase for authentication
        user = db.verify_user_password(username, password)

        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]
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
        
        # Check if username already exists
        existing_user = db.get_user_by_username(username)
        if existing_user:
            error = "Username already exists"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS)
        
        try:
            # Create user in Supabase
            db.create_user(username, password, email, role, security_question, security_answer)
            success = "Account created successfully! You can now login."
            return render_template("create_account.html", success=success, questions=SECURITY_QUESTIONS)
        except Exception as e:
            error = f"Error creating account: {str(e)}"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS)
    
    return render_template("create_account.html", questions=SECURITY_QUESTIONS)

# ---------- Teacher Dashboard ----------
@app.route("/teacher")
def teacher_dashboard():
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))

    students = db.get_all_students()
    return render_template("teacher_dashboard.html", students=students)

@app.route("/add", methods=["POST"])
def add_student():
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))

    name = request.form["name"]
    course = request.form["course"]
    class_name = request.form["class"]
    section = request.form["section"]
    parent_phone = request.form["parent_phone"]
    parent_email = request.form["parent_email"]
    
    db.create_student(name, course, class_name, section, parent_phone, parent_email)
    return redirect(url_for("teacher_dashboard"))

@app.route("/edit/<student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))

    if request.method == "POST":
        update_data = {
            "name": request.form["name"],
            "course": request.form["course"],
            "class": request.form["class"],
            "section": request.form["section"],
            "parent_phone": request.form["parent_phone"],
            "parent_email": request.form["parent_email"]
        }
        db.update_student(student_id, **update_data)
        return redirect(url_for("teacher_dashboard"))
    
    student = db.get_student_by_id(student_id)
    if not student:
        return redirect(url_for("teacher_dashboard"))
    return render_template("edit.html", student=student)

@app.route("/delete/<student_id>")
def delete_student(student_id):
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))
    
    db.delete_student(student_id)
    return redirect(url_for("teacher_dashboard"))

@app.route("/search", methods=["POST"])
def search_student():
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))

    keyword = request.form["keyword"]
    students = db.search_students(keyword)
    return render_template("teacher_dashboard.html", students=students)

@app.route("/export")
def export_students():
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))
    
    students = db.get_all_students()
    df = pd.DataFrame(students)
    
    # Create in-memory CSV file
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return send_file(csv_buffer, mimetype="text/csv", as_attachment=True, download_name="students.csv")

# ---------- Student Dashboard ----------
@app.route("/student")
def student_dashboard():
    if "role" not in session or session["role"] != "student":
        return redirect(url_for("login"))
    
    students = db.get_all_students()
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
                user = db.get_user_by_username(username)
                
                if user:
                    security_question = user["security_question"]
                    username_verified = username
                    show_reset_form = True
                else:
                    error = "Username not found"
        
        elif step == "verify_security":
            # Step 2: Verify security question
            username = request.form.get("username", "").strip()
            security_answer = request.form.get("security_answer", "").lower().strip()
            
            user = db.get_user_by_username(username)
            
            if user:
                stored_answer = user["security_answer"].lower().strip() if user["security_answer"] else ""
                if stored_answer == security_answer:
                    username_verified = username
                    show_password_form = True
                    show_reset_form = True
                else:
                    error = "Incorrect security answer"
                    security_question = user["security_question"]
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
                db.update_user_password(username, new_password)
                success = "Password reset successfully! You can now login."
    
    return render_template("forgot_password.html", error=error, success=success, 
                         show_reset_form=show_reset_form, username_verified=username_verified,
                         security_question=security_question, show_password_form=show_password_form)

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        reset_record, error_msg = db.verify_password_reset_token(token)
        
        if not reset_record:
            return render_template("reset_password.html", error=error_msg or "Invalid token")
        
        if request.method == "POST":
            new_password = request.form["new_password"]
            confirm_password = request.form["confirm_password"]
            
            if new_password == confirm_password:
                username = reset_record["username"]
                db.update_user_password(username, new_password)
                return render_template("reset_password.html", success=True)
            else:
                return render_template("reset_password.html", error="Passwords do not match")
        
        return render_template("reset_password.html", token=token)
    
    except Exception as e:
        return render_template("reset_password.html", error=f"Error: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)

