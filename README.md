<div align="center">

<img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask&logoColor=white"/>
<img src="https://img.shields.io/badge/SQLite-Relational%20DB-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
<img src="https://img.shields.io/badge/Bootstrap-Responsive%20UI-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white"/>
<img src="https://img.shields.io/badge/RBAC-Role%20Based%20Access-DC143C?style=for-the-badge"/>
<img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge"/>

<br/><br/>

# Role-Based Student Information Management System
### Full-Stack Flask + SQLite Web App · RBAC · Multi-Step Auth · CRUD · CSV Export

*A database-centric academic records system implementing role-based access control, session authentication, and multi-step password recovery — built to simulate real-world enterprise IT workflows.*

<br/>

[Overview](#-overview) · [Architecture](#-architecture) · [Roles & Permissions](#-roles--permissions) · [Database Design](#-database-design) · [Screenshots](#-screenshots) · [Installation](#-installation) · [Usage](#-usage) · [Routes](#-route-reference) · [Roadmap](#-roadmap)

</div>

---

## Overview

Academic record systems in real organizations are not simple CRUD apps — they enforce access boundaries, protect sensitive data behind authenticated sessions, and provide role-specific workflows. This project replicates that pattern at a clear, understandable scale.

Built with **Flask** and **SQLite**, the system separates concerns cleanly: teachers get full write access to student records; students get read-only dashboards. Authentication is session-based with a three-step password recovery flow. All student data is exportable to CSV via Pandas.

**What distinguishes this from a typical student project:**

- RBAC is enforced at the routing level — role is stored in the session and validated on every protected route, not just the login redirect
- Password recovery uses a three-step verification chain (username → security question → reset) with a `password_reset` table holding token, `created_at`, and `expires_at` — designed to be extended to time-limited email tokens
- Multi-field search across name, course, class, and section runs as a single parameterized SQLite query, not client-side filtering
- CSV export uses Pandas `DataFrame.to_csv()` streamed via Flask's `Response` object with the correct `Content-Disposition` header

**Developed during an internship at Rashtriya Ispat Nigam Limited (RINL / Vizag Steel Plant)**, IT & ERP Department, Dec 2024 – Jan 2025.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Client (Browser)                          │
│   login.html · teacher_dashboard.html · student_dashboard.html   │
│   create_account.html · edit.html · forgot/reset_password.html   │
└──────────────────────────────┬───────────────────────────────────┘
                               │  HTTP Requests
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Flask Backend (app.py)                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │               Session & Auth Middleware                  │    │
│  │   Role validation on every protected route               │    │
│  │   session['role'] → 'teacher' | 'student'               │    │
│  └──────────────────────────┬──────────────────────────────┘    │
│                              │                                   │
│        ┌─────────────────────┼──────────────────────┐           │
│        ▼                     ▼                      ▼           │
│  ┌──────────────┐   ┌─────────────────┐   ┌──────────────────┐  │
│  │  Auth Routes │   │  Teacher Routes │   │  Student Routes  │  │
│  │              │   │                 │   │                  │  │
│  │ /login       │   │ /dashboard      │   │ /student-dash    │  │
│  │ /register    │   │ /add            │   │ /view-records    │  │
│  │ /forgot-pw   │   │ /edit/<id>      │   │                  │  │
│  │ /reset-pw    │   │ /delete/<id>    │   │  Read-only       │  │
│  │ /logout      │   │ /search         │   │  access only     │  │
│  └──────┬───────┘   │ /export-csv     │   └──────────────────┘  │
│         │           └────────┬────────┘                         │
│         │                    │                                   │
└─────────┼────────────────────┼───────────────────────────────────┘
          │                    │
          ▼                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                      SQLite Database                             │
│                       (students.db)                              │
│                                                                  │
│   ┌─────────────┐   ┌──────────────┐   ┌────────────────────┐   │
│   │    users    │   │   students   │   │   password_reset   │   │
│   │─────────────│   │──────────────│   │────────────────────│   │
│   │ id          │   │ id           │   │ id                 │   │
│   │ username    │   │ name         │   │ username           │   │
│   │ password    │   │ course       │   │ token              │   │
│   │ email       │   │ class        │   │ created_at         │   │
│   │ role        │   │ section      │   │ expires_at         │   │
│   │ security_q  │   │ parent_phone │   └────────────────────┘   │
│   │ security_a  │   │ parent_email │                            │
│   └─────────────┘   └──────────────┘                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## Roles & Permissions

| Capability | Teacher | Student |
|---|:---:|:---:|
| Login / Logout | ✅ | ✅ |
| View student records | ✅ | ✅ |
| Add student records | ✅ | ❌ |
| Edit student records | ✅ | ❌ |
| Delete student records | ✅ | ❌ |
| Search (name / course / class / section) | ✅ | ❌ |
| Export records to CSV | ✅ | ❌ |
| Password recovery | ✅ | ✅ |

Role is assigned at account creation and stored in the `users` table. It is loaded into `session['role']` at login and checked on every protected route before processing the request.

---

## Authentication Flow

```
User submits credentials
        │
        ▼
Validate username + password against users table
        │
        ├── Failure → redirect to /login with error message
        │
        └── Success → store session['user'] and session['role']
                │
                ├── role == 'teacher' → redirect to /dashboard
                │
                └── role == 'student' → redirect to /student-dash
```

### Password Recovery (3-Step)

```
Step 1: Enter username          → verify username exists in users table
Step 2: Answer security question → validate security_answer matches stored value
Step 3: Enter new password       → update password in users table
                                   (token recorded in password_reset table)
```

The `password_reset` table stores `token`, `created_at`, and `expires_at` — structured to support time-limited email-based OTP recovery as a future upgrade without schema changes.

---

## Database Design

### `users`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment primary key |
| `username` | TEXT UNIQUE | Login identifier |
| `password` | TEXT | Password (plaintext — see roadmap for bcrypt upgrade) |
| `email` | TEXT | User email address |
| `role` | TEXT | `'teacher'` or `'student'` |
| `security_question` | TEXT | Recovery question |
| `security_answer` | TEXT | Recovery answer |

### `students`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment primary key |
| `name` | TEXT | Student full name |
| `course` | TEXT | Enrolled course / programme |
| `class` | TEXT | Class identifier |
| `section` | TEXT | Section identifier |
| `parent_phone` | TEXT | Parent / guardian contact number |
| `parent_email` | TEXT | Parent / guardian email |

### `password_reset`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment primary key |
| `username` | TEXT | Associated user account |
| `token` | TEXT | Reset token (extensible to email OTP) |
| `created_at` | DATETIME | Token creation timestamp |
| `expires_at` | DATETIME | Token expiry timestamp |

---

## Screenshots

### Login Page
<img width="1366" height="768" alt="Login Page" src="https://github.com/user-attachments/assets/89f0073f-b3c9-4588-99a4-cb76d4c42894" />

### Teacher Dashboard
<img width="1366" height="768" alt="Teacher Dashboard" src="https://github.com/user-attachments/assets/fd273bdc-a06e-4d5f-ac4b-6102e41d7b9d" />

### Student Dashboard
<img width="1366" height="768" alt="Student Dashboard" src="https://github.com/user-attachments/assets/90640182-f1ec-46fd-bc55-d8bca7bb9fff" />

### Edit Student Record
<img width="1366" height="768" alt="Edit Student Record" src="https://github.com/user-attachments/assets/5d842889-2a30-4939-9899-ae6433f33a31" />

### Create Account
<img width="1366" height="768" alt="Create Account" src="https://github.com/user-attachments/assets/b75758ba-79ac-4218-88fe-04df9cf6fd9d" />

---

## Repository Structure

```
student_management_system/
│
├── app.py                       # Flask app — routes, auth, CRUD, export
├── students.db                  # SQLite database (auto-created on first run)
├── requirements.txt
├── README.md
└── LICENSE
│
├── templates/
│   ├── login.html               # Login form
│   ├── create_account.html      # Account registration
│   ├── forgot_password.html     # Step 1 & 2 of password recovery
│   ├── reset_password.html      # Step 3 — new password entry
│   ├── teacher_dashboard.html   # Full CRUD dashboard
│   ├── student_dashboard.html   # Read-only records view
│   └── edit.html                # Edit student record form
```

---

## Installation

**Prerequisites:** Python 3.8+, pip

**1. Clone the repository**

```bash
git clone https://github.com/Mvkarthikeya07/Role-Based-Student-Information-Management-System-Using-Relational-Database-Design
cd student-management-system
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the application**

```bash
python app.py
```

**5. Open in browser**

```
http://127.0.0.1:5000/login
```

The SQLite database (`students.db`) is created automatically on first run. No manual schema setup required.

---

## Usage

**Register an account** at `/register`, selecting either the Teacher or Student role.

**Teacher workflow:**
- Log in → Teacher Dashboard
- Add, edit, or delete student records
- Use the search bar to filter by name, course, class, or section
- Export the full student list to CSV via the export button

**Student workflow:**
- Log in → Student Dashboard
- View student records in read-only mode

**Forgot your password?**
- Navigate to `/forgot-password`
- Complete the three-step recovery: username → security question → new password

---

## Route Reference

| Method | Route | Role | Description |
|---|---|---|---|
| `GET` | `/login` | Public | Login page |
| `POST` | `/login` | Public | Authenticate user, set session |
| `GET` | `/register` | Public | Account creation form |
| `POST` | `/register` | Public | Create user in `users` table |
| `GET` | `/logout` | Any | Clear session, redirect to login |
| `GET` | `/dashboard` | Teacher | Teacher dashboard with student list |
| `POST` | `/add` | Teacher | Insert new student record |
| `GET/POST` | `/edit/<id>` | Teacher | Fetch and update student record |
| `POST` | `/delete/<id>` | Teacher | Delete student record by ID |
| `GET` | `/search` | Teacher | Multi-field search query |
| `GET` | `/export-csv` | Teacher | Stream CSV via Pandas + Flask Response |
| `GET` | `/student-dash` | Student | Read-only student records view |
| `GET/POST` | `/forgot-password` | Public | Steps 1 & 2 of password recovery |
| `GET/POST` | `/reset-password` | Public | Step 3 — password update |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite (`sqlite3` via Flask-SQLAlchemy or direct) |
| Templating | Jinja2 (server-side rendering) |
| Frontend | HTML, Bootstrap |
| Data Export | Pandas (`DataFrame.to_csv`) |
| Session Auth | Flask `session` (server-side) |

---

## Known Limitations

These are documented openly and are candidates for the roadmap below:

| Limitation | Impact | Fix |
|---|---|---|
| Passwords stored in plaintext | Security risk | `bcrypt` hashing |
| No CSRF protection | Vulnerable to cross-site request forgery | `Flask-WTF` CSRF tokens |
| Security questions are static | Weak recovery mechanism | Email OTP via `Flask-Mail` |
| No AJAX / live updates | Full page reload on every action | Fetch API + JSON endpoints |
| SQLite not suited for concurrency | Breaks under multi-user load | Migrate to PostgreSQL / MySQL |

---

## Roadmap

- [ ] Password hashing with `bcrypt`
- [ ] CSRF protection via `Flask-WTF`
- [ ] Email-based OTP password recovery (`Flask-Mail`)
- [ ] Admin role with user management capabilities
- [ ] Attendance and grading module
- [ ] Dashboard analytics with Chart.js
- [ ] REST API refactor + React frontend
- [ ] Migration to PostgreSQL with `Flask-Migrate`
- [ ] Docker containerization

---

## Internship Context

Developed during an internship at **Rashtriya Ispat Nigam Limited (RINL) — Vizag Steel Plant**, IT & ERP Department (Dec 2024 – Jan 2025). The project was scoped around understanding enterprise data management, role-based system design, and backend-driven application architecture in a production IT environment.

---

## Author

**M V Karthikeya**
B.Tech — Computer Science (AI & ML)
SRM Institute of Science and Technology

🔗 GitHub: [github.com/Mvkarthikeya07](https://github.com/Mvkarthikeya07)

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Built during enterprise IT exposure · Designed for clarity, extensibility, and real-world relevance.</sub>
</div>
