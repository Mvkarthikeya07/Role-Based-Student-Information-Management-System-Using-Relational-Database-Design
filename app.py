import os
import re
from flask import Flask, render_template, request, redirect, url_for, session, send_file, g
from db import DatabaseOps
import pandas as pd
from io import BytesIO
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")


def get_db() -> DatabaseOps:
    """Create DB client lazily per request to avoid import-time crashes in serverless."""
    if "db" not in g:
        g.db = DatabaseOps(
            access_token=session.get("sb_access_token"),
            refresh_token=session.get("sb_refresh_token"),
        )
    return g.db


@app.teardown_appcontext
def teardown_db(_exception):
    g.pop("db", None)


def is_strong_password(password: str) -> bool:
    """Standard password policy."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True


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
        username = request.form["username"].strip()
        password = request.form["password"]

        try:
            # Use Supabase Auth for authentication
            auth_result = get_db().sign_in_user(username, password)
            if auth_result:
                user = auth_result["user"]
                auth_session = auth_result.get("session")

                session["username"] = user["username"]
                session["role"] = user["role"]
                if auth_session:
                    session["sb_access_token"] = auth_session.access_token
                    session["sb_refresh_token"] = auth_session.refresh_token
                return redirect(url_for("home"))
            else:
                error = "Invalid Credentials"
        except Exception as exc:
            message = str(exc)
            if "Email not confirmed" in message:
                error = "Please confirm your email before logging in. Check your inbox/spam for the verification link."
            else:
                error = "Login failed. Please try again."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    try:
        get_db().client.auth.sign_out()
    except Exception:
        pass
    session.clear()
    return redirect(url_for("login"))

# ---------- Create Account / Registration ----------
@app.route("/create-account", methods=["GET", "POST"])
def create_account():
    error = None
    success = None
    form_data = {
        "username": "",
        "email": "",
        "role": "",
        "security_question": "",
        "security_answer": "",
    }
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        email = request.form["email"].strip()
        role = request.form.get("role", "").strip().lower()
        security_question = request.form["security_question"]
        security_answer = request.form["security_answer"].lower().strip()

        form_data.update(
            {
                "username": username,
                "email": email,
                "role": role,
                "security_question": security_question,
                "security_answer": security_answer,
            }
        )
        
        # Validate passwords match
        if password != confirm_password:
            error = "Passwords do not match"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS, form_data=form_data)
        
        # Validate password strength
        if not is_strong_password(password):
            error = "Password must be at least 8 chars with uppercase, lowercase, number, and special character"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS, form_data=form_data)
        
        # Validate security answer
        if not security_answer:
            error = "Security answer is required"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS, form_data=form_data)
        
        # Check if username already exists
        existing_user = get_db().get_user_by_username(username)
        if existing_user:
            error = "Username already exists"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS, form_data=form_data)
        
        # Check if email already exists locally to prevent confusing API errors
        existing_email = get_db().client.table("users").select("email").eq("email", email).execute()
        if existing_email.data:
            error = "Email address is already registered."
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS, form_data=form_data)
        
        try:
            # Create user in Supabase Auth + users profile table
            sign_up_result = get_db().sign_up_user(
                username, password, email, role, security_question, security_answer
            )
            sign_up_session = sign_up_result.get("session")
            if sign_up_session:
                session["sb_access_token"] = sign_up_session.access_token
                session["sb_refresh_token"] = sign_up_session.refresh_token
            success = "Account created successfully. If email confirmation is enabled, verify your email first, then login."
            return render_template("create_account.html", success=success, questions=SECURITY_QUESTIONS, form_data=form_data)
        except Exception as e:
            error = f"Error creating account: {str(e)}"
            return render_template("create_account.html", error=error, questions=SECURITY_QUESTIONS, form_data=form_data)
    
    return render_template("create_account.html", questions=SECURITY_QUESTIONS, form_data=form_data)

# ---------- Teacher Dashboard ----------
@app.route("/teacher")
def teacher_dashboard():
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))

    try:
        students = get_db().get_all_students()
        return render_template("teacher_dashboard.html", students=students, db_error=None)
    except Exception:
        return render_template(
            "teacher_dashboard.html",
            students=[],
            db_error="Unable to connect to database right now. Please verify Supabase env vars and network access.",
        )

@app.route("/add", methods=["POST"])
def add_student():
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))

    register_no = request.form["register_no"].strip()
    name = request.form["name"]
    year_of_joining = request.form["year_of_joining"]
    class_name = request.form["class"]
    section = request.form["section"]
    parent_phone = request.form["parent_phone"]
    parent_email = request.form["parent_email"]
    
    existing = get_db().get_student_by_register_no(register_no)
    if existing:
        return redirect(url_for("teacher_dashboard"))

    try:
        get_db().create_student(register_no, name, year_of_joining, class_name, section, parent_phone, parent_email)
    except ValueError:
        return redirect(url_for("teacher_dashboard"))
    return redirect(url_for("teacher_dashboard"))

@app.route("/edit/<student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))

    if request.method == "POST":
        update_data = {
            "register_no": request.form["register_no"].strip(),
            "name": request.form["name"],
            "year_of_joining": request.form["year_of_joining"],
            "class": request.form["class"],
            "section": request.form["section"],
            "parent_phone": request.form["parent_phone"],
            "parent_email": request.form["parent_email"]
        }
        duplicate = get_db().get_student_by_register_no(update_data["register_no"])
        if duplicate and duplicate["id"] != student_id:
            return redirect(url_for("edit_student", student_id=student_id))

        try:
            get_db().update_student(student_id, **update_data)
        except ValueError:
            return redirect(url_for("edit_student", student_id=student_id))
        return redirect(url_for("teacher_dashboard"))
    
    student = get_db().get_student_by_id(student_id)
    if not student:
        return redirect(url_for("teacher_dashboard"))
    return render_template("edit.html", student=student)

@app.route("/delete/<student_id>")
def delete_student(student_id):
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))
    
    get_db().delete_student(student_id)
    return redirect(url_for("teacher_dashboard"))

@app.route("/search", methods=["POST"])
def search_student():
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))

    keyword = request.form["keyword"]
    try:
        students = get_db().search_students(keyword)
        return render_template("teacher_dashboard.html", students=students, db_error=None)
    except Exception:
        return render_template(
            "teacher_dashboard.html",
            students=[],
            db_error="Search failed due to database connectivity issue.",
        )

@app.route("/export")
def export_students():
    if "role" not in session or session["role"] != "teacher":
        return redirect(url_for("login"))
    
    try:
        students = get_db().get_all_students()
    except Exception:
        return "Database unavailable for export right now.", 503
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
    
    try:
        students = get_db().get_all_students()
        return render_template("student_dashboard.html", students=students, db_error=None)
    except Exception:
        return render_template(
            "student_dashboard.html",
            students=[],
            db_error="Unable to load records because database is currently unreachable.",
        )

# ---------- Change Password (Dashboard) ----------
@app.route("/change-password", methods=["POST"])
def change_password():
    if "username" not in session:
        return redirect(url_for("login"))
    
    username = session["username"]
    role = session.get("role", "student")
    
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()
    otp = request.form.get("otp", "").strip()
    step = request.form.get("step", "send_code")
    
    db = get_db()
    user = db.get_user_by_username(username)
    email = user.get("email", "").strip() if user else ""
    
    def render_dash(error=None, success=None):
        try:
            students = db.get_all_students()
        except Exception:
            students = []
            if not error:
                error = "Unable to fetch students due to database connectivity issue."
        template = "teacher_dashboard.html" if role == "teacher" else "student_dashboard.html"
        return render_template(template, students=students, db_error=error, success_msg=success)

    if step == "send_code":
        # Send OTP to registered email
        if not email:
            return render_dash(error="No email associated with your account")
        
        # Generate and send OTP
        otp_code = db.generate_otp()
        if db.send_verification_email(email, username, otp_code):
            return render_dash(success=f"Verification code sent to {email}. Enter it along with your new password to proceed.")
        else:
            return render_dash(error="Failed to send verification code. Please try again.")
    
    elif step == "verify_and_update":
        # Verify OTP and update password
        if not otp or not new_password or not confirm_password:
            return render_dash(error="Please enter verification code and new password")
        
        # Verify OTP
        success_verify, msg, verified_username = db.verify_email_otp(email, otp)
        if not success_verify:
            return render_dash(error=f"Verification failed: {msg}. Please request a new code.")
        
        if verified_username != username:
            return render_dash(error="Verification failed: Email does not match")
        
        # Verify passwords match
        if new_password != confirm_password:
            return render_dash(error="New passwords do not match")
        
        # Verify password strength
        if not is_strong_password(new_password):
            return render_dash(error="Password must be at least 8 chars with uppercase, lowercase, number, and special character")
        
        try:
            # Update password
            db.client.auth.update_user({"password": new_password})
            db.update_user_password(username, new_password)
            return render_dash(success="Password updated successfully!")
        except Exception as e:
            return render_dash(error=f"Error changing password: {str(e)}")
    
    return render_dash(error="Invalid request")

# ---------- Forgot Password ----------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    error = None
    success = None
    show_email_form = False
    show_password_form = False
    username_verified = None
    email_verified = None
    
    if request.method == "POST":
        step = request.form.get("step", "verify_username")
        
        if step == "verify_username":
            # Step 1: Verify username and send OTP to email
            username = request.form.get("username", "").strip()
            if not username:
                error = "Please enter a username"
            else:
                user = get_db().get_user_by_username(username)
                if not user:
                    error = "Username not found"
                else:
                    email = user.get("email", "").strip()
                    if not email:
                        error = "No email associated with this account"
                    else:
                        # Generate and send OTP
                        otp = get_db().generate_otp()
                        if get_db().send_verification_email(email, username, otp):
                            username_verified = username
                            email_verified = email
                            show_email_form = True
                            success = f"Verification code sent to {email}. Check your email."
                        else:
                            error = "Failed to send verification code. Please try again."
        
        elif step == "verify_otp":
            # Step 2: Verify OTP
            email = request.form.get("email", "").strip()
            otp = request.form.get("otp", "").strip()
            
            if not email or not otp:
                error = "Please enter email and OTP"
                email_verified = email
                show_email_form = True
            else:
                success_verify, msg, username = get_db().verify_email_otp(email, otp)
                if success_verify:
                    username_verified = username
                    email_verified = email
                    show_password_form = True
                else:
                    error = msg
                    email_verified = email
                    show_email_form = True
        
        elif step == "change_password":
            # Step 3: Change password
            email = request.form.get("email", "").strip()
            username = request.form.get("username", "").strip()
            new_password = request.form.get("new_password", "").strip()
            confirm_password = request.form.get("confirm_password", "").strip()

            user = get_db().get_user_by_username(username)
            if not user or user.get("email", "").strip().lower() != email.lower():
                error = "Email verification failed. Incorrect email."
                show_password_form = True
                username_verified = username
                email_verified = email
            elif new_password != confirm_password:
                error = "Passwords do not match"
                show_password_form = True
                username_verified = username
                email_verified = email
            elif not is_strong_password(new_password):
                error = "Password must be at least 8 chars with uppercase, lowercase, number, and special character"
                show_password_form = True
                username_verified = username
                email_verified = email
            else:
                get_db().update_user_password(username, new_password)
                success = "Password reset successfully! You can now login."
    
    return render_template("forgot_password.html", error=error, success=success, 
                         show_email_form=show_email_form,
                         show_password_form=show_password_form, username_verified=username_verified,
                         email_verified=email_verified)

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        reset_record, error_msg = get_db().verify_password_reset_token(token)
        
        if not reset_record:
            return render_template("reset_password.html", error=error_msg or "Invalid token")
        
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            new_password = request.form.get("new_password", "").strip()
            confirm_password = request.form.get("confirm_password", "").strip()

            username = reset_record["username"]
            user = get_db().get_user_by_username(username)
            if not user or user.get("email", "").strip().lower() != email.lower():
                return render_template("reset_password.html", error="Email verification failed. Incorrect email.")
            if new_password != confirm_password:
                return render_template("reset_password.html", error="Passwords do not match")
            if not is_strong_password(new_password):
                return render_template("reset_password.html", error="Password must be at least 8 chars with uppercase, lowercase, number, and special character")

            get_db().update_user_password(username, new_password)
            return render_template("reset_password.html", success=True)
        
        return render_template("reset_password.html", token=token)
    
    except Exception as e:
        return render_template("reset_password.html", error=f"Error: {str(e)}")

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode)



@app.errorhandler(Exception)
def handle_exception(error):
    if isinstance(error, HTTPException):
        return error
    app.logger.exception("Unhandled application error: %s", error)
    return "Internal Server Error. Check server logs and verify Supabase connectivity.", 500