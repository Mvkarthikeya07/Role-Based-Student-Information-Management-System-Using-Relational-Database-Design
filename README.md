<div align="center">

<img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Flask-2.3.3-000000?style=for-the-badge&logo=flask&logoColor=white"/>
<img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white"/>
<img src="https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel&logoColor=white"/>
<img src="https://img.shields.io/badge/RBAC-Role%20Based%20Access-DC143C?style=for-the-badge"/>
<img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge"/>

<br/><br/>

# Role-Based Student Information Management System
### Full-Stack Flask · Supabase PostgreSQL · RBAC · PBKDF2 Auth · Row Level Security · Vercel Deployment

*A production-deployed academic records system with role-based access control, PBKDF2 password hashing, Supabase Row Level Security, and serverless deployment on Vercel.*

<br/>

[Overview](#-overview) · [Architecture](#-architecture) · [Roles & Permissions](#-roles--permissions) · [Database Design](#-database-design) · [Auth Flow](#-authentication-flow) · [Screenshots](#-screenshots) · [Setup](#-setup) · [Routes](#-route-reference) · [Deployment](#-vercel-deployment) · [Roadmap](#-roadmap)

</div>

---

## Overview

This is a production-deployed, full-stack student records management system built on **Flask**, **Supabase (PostgreSQL)**, and deployed to **Vercel**. It enforces role-based access control at both the Flask routing layer and the database layer via Supabase **Row Level Security (RLS)** policies.

The system is not a SQLite demo — it uses a cloud PostgreSQL backend with UUID primary keys, indexed tables, auto-updating `updated_at` triggers, and proper password security via `werkzeug`'s PBKDF2-SHA256 hashing.

**What this system actually implements under the hood:**

- Passwords hashed with `generate_password_hash(method="pbkdf2:sha256", salt_length=16)` — never stored in plaintext
- Login accepts both username and email as identifiers, with duplicate-email detection
- Password policy enforced at registration: minimum 8 characters, uppercase, lowercase, digit, and special character all required
- Multi-step password recovery: username verification → email + security answer validation → PBKDF2-hashed new password written to Supabase
- Supabase RLS policies enforce that students and teachers can only access what their role permits — even if Flask routing is bypassed
- Indian phone number normalization to `+91XXXXXXXXXX` format with 10-digit validation on all student records
- CSV export streams a Pandas DataFrame via `BytesIO` with correct `Content-Disposition` headers — no temp files written to disk
- Serverless-compatible: `DatabaseOps` is instantiated lazily per request via Flask's `g` object, avoiding connection issues in Vercel's serverless environment

**Developed during an internship at Rashtriya Ispat Nigam Limited (RINL) — Vizag Steel Plant**, IT & ERP Department, Dec 2024 – Jan 2025.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Client (Browser)                            │
│  login · create_account · teacher_dashboard · student_dashboard      │
│  edit · forgot_password                                              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │  HTTPS
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Vercel Serverless (app.py)                        │
│                        Python 3.12 Runtime                           │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Session & RBAC Middleware                        │   │
│  │  session['role'] checked on every protected route            │   │
│  │  Wrong role → redirect to /login                             │   │
│  └───────────────────────────┬──────────────────────────────────┘   │
│                              │                                       │
│       ┌──────────────────────┼──────────────────┐                   │
│       ▼                      ▼                  ▼                   │
│  ┌─────────────┐   ┌──────────────────┐  ┌────────────────┐        │
│  │ Auth Routes │   │  Teacher Routes  │  │ Student Routes │        │
│  │             │   │                  │  │                │        │
│  │ /login      │   │ /teacher         │  │ /student       │        │
│  │ /create-acc │   │ /add             │  │ (read-only)    │        │
│  │ /logout     │   │ /edit/<id>       │  └────────────────┘        │
│  │ /forgot-pw  │   │ /delete/<id>     │                            │
│  │ /change-pw  │   │ /search          │                            │
│  └─────────────┘   │ /export          │                            │
│                    └──────────────────┘                            │
│                                                                      │
│  DatabaseOps instantiated lazily per request via Flask g object      │
└──────────────────────────────┬───────────────────────────────────────┘
                               │  Supabase Python SDK
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   Supabase (PostgreSQL + RLS)                        │
│                                                                      │
│  ┌─────────────────────┐        ┌──────────────────────────────┐    │
│  │       users         │        │          students            │    │
│  │─────────────────────│        │──────────────────────────────│    │
│  │ id UUID PK          │        │ id UUID PK                   │    │
│  │ username TEXT UNIQUE│        │ register_no TEXT UNIQUE      │    │
│  │ password TEXT       │        │ name TEXT                    │    │
│  │ email TEXT          │        │ year_of_joining DATE         │    │
│  │ role TEXT (CHECK)   │        │ class TEXT                   │    │
│  │ security_question   │        │ section TEXT                 │    │
│  │ security_answer     │        │ parent_phone TEXT (+91...)   │    │
│  │ created_at TIMESTAMPTZ       │ parent_email TEXT            │    │
│  │ updated_at TIMESTAMPTZ       │ enrollment_date TIMESTAMPTZ  │    │
│  │ is_active BOOLEAN   │        │ updated_at TIMESTAMPTZ       │    │
│  └─────────────────────┘        └──────────────────────────────┘    │
│                                                                      │
│  RLS Policies enforce access at DB level, independent of Flask       │
│  Indexes on: username, email, role, register_no, name, class        │
│  Triggers: auto-update updated_at on every row UPDATE               │
└──────────────────────────────────────────────────────────────────────┘
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
| Search (register no / name / class / section) | ✅ | ❌ |
| Export records to CSV | ✅ | ❌ |
| Change own password | ✅ | ✅ |
| Password recovery (forgot password) | ✅ | ✅ |

Role is enforced at two independent layers:
1. **Flask routing** — `session['role']` is checked before processing every protected request
2. **Supabase RLS** — PostgreSQL policies block unauthorized reads/writes at the database level even if routing is bypassed

---

## Database Design

### `users`

| Column | Type | Constraint | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Auto-generated primary key |
| `username` | TEXT | UNIQUE NOT NULL | Login identifier |
| `password` | TEXT | NOT NULL | PBKDF2-SHA256 hash (werkzeug) |
| `email` | TEXT | NOT NULL | Used for password recovery |
| `role` | TEXT | CHECK IN ('teacher','student') | Access level |
| `security_question` | TEXT | NOT NULL | Recovery question |
| `security_answer` | TEXT | NOT NULL | Lowercased and stripped at write time |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Account creation time |
| `updated_at` | TIMESTAMPTZ | Auto-trigger | Updated on every row change |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account status flag |

Indexes: `username`, `email`, `role`

### `students`

| Column | Type | Constraint | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Auto-generated primary key |
| `register_no` | TEXT | UNIQUE NOT NULL | Student registration number |
| `name` | TEXT | NOT NULL | Full name |
| `year_of_joining` | DATE | NOT NULL | Enrollment date |
| `class` | TEXT | NOT NULL | Year / class (e.g. "II Year") |
| `section` | TEXT | NOT NULL | Section identifier |
| `parent_phone` | TEXT | — | Normalized to `+91XXXXXXXXXX` |
| `parent_email` | TEXT | — | Guardian email |
| `enrollment_date` | TIMESTAMPTZ | DEFAULT NOW() | Record creation time |
| `updated_at` | TIMESTAMPTZ | Auto-trigger | Updated on every row change |

Indexes: `register_no`, `name`, `year_of_joining`, `class`, `section`

### Row Level Security Policies

| Table | Operation | Policy |
|---|---|---|
| `students` | SELECT | Teachers and students can both read all records |
| `students` | INSERT | Teachers only |
| `students` | UPDATE | Teachers only |
| `students` | DELETE | Teachers only |
| `users` | SELECT | Users can view their own profile; teachers can view all |

---

## Authentication Flow

### Login

```
POST /login
    │
    ├── Input: username or email + password
    │
    ├── Identifier contains '@'? → query by email (raises error if multiple accounts share email)
    │                           → query by username otherwise
    │
    ├── User not found → "Invalid Credentials"
    │
    ├── _verify_password(stored_pbkdf2_hash, input_password)
    │       └── Fails → "Invalid Credentials"
    │
    └── Success → session['username'], session['role'] set
                        │
                        ├── role == 'teacher' → /teacher
                        └── role == 'student' → /student
```

### Password Policy (Registration & Change Password)

Passwords must satisfy all of the following — validated by `is_strong_password()` in `app.py`:

- Minimum 8 characters
- At least one uppercase letter `[A-Z]`
- At least one lowercase letter `[a-z]`
- At least one digit `[0-9]`
- At least one special character `[^A-Za-z0-9]`

### Password Recovery (3-Step)

```
Step 1 — POST /forgot-password (step=verify_username)
    └── Verify username exists in users table
    └── Retrieve and display associated security question

Step 2 & 3 — POST /forgot-password (step=reset_with_security)
    ├── Validate email matches the account on record
    ├── Validate security_answer matches stored value (case-insensitive)
    ├── Validate new password == confirm_password
    ├── Enforce is_strong_password() policy
    └── update_user_password() → PBKDF2-hashed new password written to Supabase
```

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

> **Note:** If screenshots appear broken, re-upload them directly to this repository via the GitHub editor to generate repo-scoped CDN URLs.

---

## Repository Structure

```
Role-Based-Student-Information-Management-System/
│
├── app.py                        # Flask app — routes, RBAC, auth, CSV export
├── db.py                         # Supabase client, DatabaseOps, password hashing
├── init_db.py                    # Connection verification + default data seeding
├── supabase_schema.sql           # Full PostgreSQL schema with RLS, indexes, triggers
├── vercel.json                   # Vercel serverless deployment config (Python 3.12)
├── requirements.txt              # Python dependencies
├── .gitignore
├── README.md
└── LICENSE
│
└── templates/
    ├── base.html                 # Shared layout
    ├── login.html                # Login form (username or email)
    ├── create_account.html       # Registration with password policy + security question
    ├── forgot_password.html      # 3-step password recovery
    ├── teacher_dashboard.html    # CRUD dashboard with search and export
    ├── student_dashboard.html    # Read-only records view
    └── edit.html                 # Edit student record form
```

---

## Setup

### Prerequisites

- Python 3.12+
- A [Supabase](https://supabase.com) project with the schema applied

### 1. Clone the repository

```bash
git clone https://github.com/Mvkarthikeya07/Role-Based-Student-Information-Management-System-Using-Relational-Database-Design
cd Role-Based-Student-Information-Management-System-Using-Relational-Database-Design-main
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Supabase environment variables

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key-here
FLASK_SECRET_KEY=your-random-secret-key
FLASK_DEBUG=False
```

> Use the **service_role** key (not the `anon` key) — required for RLS bypass and password updates.

### 5. Apply the database schema

Run `supabase_schema.sql` in your Supabase project's SQL editor to create tables, indexes, RLS policies, and triggers.

### 6. Initialize with default data (optional)

```bash
python init_db.py
```

Creates default `teacher` / `student` accounts and 5 sample student records if the tables are empty.

### 7. Run the application

```bash
python app.py
```

Open: `http://127.0.0.1:5000/login`

**Default credentials (after seeding):**

| Role | Username | Password |
|---|---|---|
| Teacher | `teacher` | `Teacher@123` |
| Student | `student` | `Student@456` |

---

## Route Reference

| Method | Route | Role | Description |
|---|---|---|---|
| `GET` | `/` | Any | Redirect based on session role |
| `GET/POST` | `/login` | Public | Authenticate (username or email) |
| `GET/POST` | `/create-account` | Public | Register with password policy + security question |
| `GET` | `/logout` | Any | Clear session |
| `GET` | `/teacher` | Teacher | Dashboard with full student list |
| `POST` | `/add` | Teacher | Insert new student record |
| `GET/POST` | `/edit/<id>` | Teacher | Fetch and update student by UUID |
| `GET` | `/delete/<id>` | Teacher | Delete student by UUID |
| `POST` | `/search` | Teacher | Keyword search across register_no, name, class, section |
| `GET` | `/export` | Teacher | Stream CSV via Pandas BytesIO |
| `GET` | `/student` | Student | Read-only records view |
| `POST` | `/change-password` | Teacher/Student | Change password with old password verification |
| `GET/POST` | `/forgot-password` | Public | 3-step password recovery |

---

## Vercel Deployment

The project is configured for serverless deployment on Vercel via `vercel.json`:

```json
{
  "version": 2,
  "builds": [{ "src": "app.py", "use": "@vercel/python", "config": { "pythonVersion": "3.12" } }],
  "routes": [{ "src": "/(.*)", "dest": "app.py" }]
}
```

**To deploy:**

```bash
npm install -g vercel
vercel
```

Set the following environment variables in the Vercel dashboard under **Project Settings → Environment Variables**:

| Variable | Value |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your service_role key |
| `FLASK_SECRET_KEY` | A random secret string |

The `DatabaseOps` object is instantiated per-request via Flask's `g` object, making it compatible with Vercel's stateless serverless execution model.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 2.3.3 |
| Database | Supabase (PostgreSQL) with RLS |
| ORM / DB Client | Supabase Python SDK v2 |
| Password Security | `werkzeug.security` PBKDF2-SHA256 |
| Templating | Jinja2 (server-side rendering) |
| Frontend | HTML, Bootstrap |
| Data Export | Pandas + BytesIO (in-memory CSV) |
| Deployment | Vercel Serverless (Python 3.12) |
| Environment | `python-dotenv` |

---

## Known Limitations

| Limitation | Impact | Planned Fix |
|---|---|---|
| No CSRF protection | Vulnerable to cross-site request forgery | `Flask-WTF` CSRF tokens |
| Security answers stored as plaintext | Can be read if DB is compromised | Hash answers with bcrypt |
| No AJAX / live updates | Full page reload on every action | Fetch API + JSON endpoints |
| No email OTP — recovery uses security question | Weaker than email-based reset | `Flask-Mail` + time-limited tokens |
| No rate limiting on login | Brute-force vulnerability | `Flask-Limiter` |

---

## Roadmap

- [ ] CSRF protection via `Flask-WTF`
- [ ] Email-based OTP password recovery (`Flask-Mail`)
- [ ] Rate limiting on `/login` (`Flask-Limiter`)
- [ ] Admin role with user management capabilities
- [ ] Attendance and grading module
- [ ] Dashboard analytics with Chart.js
- [ ] REST API refactor + React frontend
- [ ] Argon2 password hashing upgrade

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
  <sub>Built during enterprise IT exposure · Supabase-backed · Vercel-deployed · Production-ready security.</sub>
</div>
