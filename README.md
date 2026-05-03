# ðŸŽ“ Role-Based Student Information Management System

## ðŸš€ Enterprise-Style DBMS Web Application with Role-Based Access Control

---

## ðŸ“Œ Overview

The **Role-Based Student Information Management System** is a full-stack, database-driven web application designed to manage student records securely and efficiently within an academic environment.

Built using **Flask (Python)** and **SQLite**, the system demonstrates how modern web applications integrate **backend logic, relational databases, and role-based authentication** to simulate real-world enterprise IT systems.

This project goes beyond a basic CRUD application by implementing:

* Role-based dashboards
* Multi-step password recovery
* Data export functionality
* Structured database design

ðŸ’¡ This system simulates a real-world academic ERP module, demonstrating how structured data systems, role-based access, and backend-driven workflows are implemented in enterprise environments.

```

## ðŸ¢ Internship & Project Context

**Organization:** Rashtriya Ispat Nigam Limited (Vizag Steel Plant)  
**Department:** IT & ERP  
**Project Domain:** DBMS & Enterprise IT Systems  
**Duration:** Dec 2024 â€“ Jan 2025

This project reflects **hands-on exposure to enterprise workflows**, including:

* Data handling and persistence
* Role-based system design
* Backend-driven application architecture

```
---

## ðŸŽ¯ Objectives

* Design a **secure, role-based student management system**
* Implement **CRUD operations** using relational databases
* Apply **authentication and session management**
* Integrate **Flask backend with dynamic HTML templates**
* Demonstrate **real-world DBMS concepts in a web environment**

---

## ðŸ§  System Architecture

The application follows a **database-centric architecture**:

```
Client (Browser)
   â†“
Flask Backend (Routes + Logic)
   â†“
SQLite Database
```

### Core Concepts Applied

* Relational Database Design
* Role-Based Access Control (RBAC)
* Session-Based Authentication
* Server-Side Rendering (Jinja2)
* CRUD Operations
* Separation of Concerns

---

## ðŸ” Authentication & Security Features

* Role-based login (Teacher / Student)
* Session management using Flask
* Multi-step password recovery system:

  * Username verification
  * Security question validation
  * Password reset
* Token-based password reset structure (extensible)

> âš ï¸ Note: Password hashing and advanced security mechanisms can be added as future enhancements.

---

## ðŸ‘¥ User Roles & Capabilities

### ðŸ‘©â€ðŸ« Teacher

* Add student records
* Edit and update student data
* Delete records
* Search students (multi-field)
* Export data to CSV

### ðŸŽ“ Student

* Secure login
* View student records
* Read-only access

---
```
## ðŸš€ Key Features

âœ” Role-Based Access Control (RBAC)
âœ” Authentication System with Session Handling
âœ” Multi-Step Password Recovery
âœ” Teacher Dashboard (Full CRUD Operations)
âœ” Student Dashboard (Read-Only Access)
âœ” Search Functionality (Name, Course, Class, Section)
âœ” CSV Export of Student Data
âœ” Responsive UI using Bootstrap
```
---

## ðŸ“¸ Application Screenshots

ðŸ“Œ Below are real screenshots of the working application demonstrating authentication, role-based access, and CRUD operations.

### ðŸ” Login Page
<img width="1366" height="768" alt="Screenshot (24)" src="https://github.com/user-attachments/assets/89f0073f-b3c9-4588-99a4-cb76d4c42894" />

### ðŸ‘©â€ðŸ« Teacher Dashboard
<img width="1366" height="768" alt="Screenshot (23)" src="https://github.com/user-attachments/assets/fd273bdc-a06e-4d5f-ac4b-6102e41d7b9d" />

### ðŸŽ“ Student Dashboard
<img width="1366" height="768" alt="Screenshot (26)" src="https://github.com/user-attachments/assets/90640182-f1ec-46fd-bc55-d8bca7bb9fff" />

### âœï¸ Edit Student
<img width="1366" height="768" alt="Screenshot (27)" src="https://github.com/user-attachments/assets/5d842889-2a30-4939-9899-ae6433f33a31" />

### ðŸ“ Create Account
<img width="1366" height="768" alt="Screenshot (25)" src="https://github.com/user-attachments/assets/b75758ba-79ac-4218-88fe-04df9cf6fd9d" />

---

## ðŸ—„ï¸ Database Design

### ðŸ“‹ Users Table

* id
* username
* password
* email
* role
* security_question
* security_answer

### ðŸ“‹ Students Table

* id
* name
* course
* class
* section
* parent_phone
* parent_email

### ðŸ“‹ Password Reset Table

* id
* username
* token
* created_at
* expires_at

---

## ðŸ”„ Application Workflow

1. User logs in with credentials
2. System validates role (Teacher / Student)
3. Redirect to appropriate dashboard
4. Teacher performs CRUD operations
5. Student views records (restricted access)
6. Password recovery available via multi-step verification

---

## ðŸ“ Project Structure

```
student_management_system/
â”‚
â”œâ”€â”€ templates/
â”‚   â”œâ”€â”€ login.html
â”‚   â”œâ”€â”€ create_account.html
â”‚   â”œâ”€â”€ forgot_password.html
â”‚   â”œâ”€â”€ reset_password.html
â”‚   â”œâ”€â”€ teacher_dashboard.html
â”‚   â”œâ”€â”€ student_dashboard.html
â”‚   â”œâ”€â”€ edit.html
â”‚
â”œâ”€â”€ app.py
â”œâ”€â”€ (removed: now uses Supabase via db.py)
â”‚
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ README.md
â””â”€â”€ LICENSE
```

---

## âš™ï¸ Installation & Setup

### 1ï¸âƒ£ Clone Repository

```bash
git clone https://github.com/Mvkarthikeya07/Role-Based-Student-Information-Management-System-Using-Relational-Database-Design
cd student-management-system
```

### 2ï¸âƒ£ Create Virtual Environment (Optional)

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3ï¸âƒ£ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4ï¸âƒ£ Run Application

```bash
python app.py
```

### 5ï¸âƒ£ Access App

```
http://127.0.0.1:5000/login
```

---

## ðŸ§ª Tech Stack

* **Backend:** Python, Flask
* **Database:** SQLite
* **Frontend:** HTML, Bootstrap
* **Data Handling:** Pandas (CSV export)

---

## ðŸ”¬ Technical Highlights

* Full-stack DBMS application
* Role-based access control implementation
* Multi-step authentication flow
* Clean backend routing structure
* Database-driven dynamic rendering
* Export functionality using Pandas

---

## âš ï¸ Limitations

* Passwords stored without hashing (can be improved)
* Security questions are basic
* No CSRF protection
* Limited frontend interactivity (no AJAX)

---

## ðŸ”® Future Enhancements

* ðŸ” Password hashing (bcrypt)
* ðŸ“§ Email-based OTP authentication
* ðŸ§¾ Attendance & grading system
* ðŸ“Š Dashboard analytics (charts)
* ðŸ§‘â€ðŸ’¼ Admin role implementation
* ðŸŒ REST API + React frontend
* ðŸ›¢ï¸ Migration to MySQL/PostgreSQL

---

## ðŸ‘¤ Author

**M V Karthikeya**
Computer Science Engineer

**Interests:**

* Database Systems
* Backend Development
* AI Systems & Automation

ðŸ”— GitHub: [https://github.com/Mvkarthikeya07](https://github.com/Mvkarthikeya07)

---

## ðŸ“œ License

This project is licensed under the **MIT License**.

---

## â­ Final Remarks

This project demonstrates a **strong foundation in database-driven application development**, combining **DBMS concepts, backend engineering, and role-based system design**.

It reflects practical exposure to **real-world IT systems** and serves as a solid base for building **scalable, production-grade applications**.

