🎓 Role-Based Student Information Management System Using Relational Database Design

A Role-Based Database Management System for Academic Institutions

📌 Overview

The Student Management System is a database-driven web application designed to manage student records efficiently through a role-based access control system. The application enables secure login for teachers and students, allowing controlled access to academic records stored in a relational database.

This project was developed as part of an industrial internship, focusing on Database Management Systems (DBMS) and IT-enabled enterprise systems, demonstrating how backend databases integrate with web-based interfaces in real-world organizational environments.

🏢 Internship & Project Details

Organization: Rashtriya Ispat Nigam Limited (Vizag Steel Plant)

Department: IT & ERP Department

Project Title: Database Management System

Duration: 4 Weeks
(December 6, 2024 – January 31, 2025)

Domain: DBMS + IT Systems

This project reflects practical exposure to enterprise-level data handling, role-based access, and IT system workflows used in large-scale organizations.

🎯 Objectives

Design a secure, role-based student information system

Implement CRUD operations using a relational database

Apply authentication and authorization mechanisms

Integrate backend database logic with a web interface

Demonstrate practical DBMS concepts in an enterprise context
````
🚀 Key Features

✔ Role-based login (Teacher & Student)
✔ Secure authentication system
✔ Teacher dashboard for managing student records
✔ Student dashboard for viewing assigned data
✔ Database-backed persistent storage
✔ Search, edit, delete, and export functionality
✔ Clean and responsive user interface
`````
🧠 System Design Approach

The system follows a database-centric web architecture:

Core Concepts Applied

Relational Database Design (SQLite)

Role-Based Access Control (RBAC)

Server-side validation

CRUD operations

Separation of concerns (UI, logic, database)

User Roles

Teacher

Add new student records

Edit and delete existing records

Search students by name or course

Export student data to CSV

Student

Secure login

View assigned student details

Read-only access to records
````
🏗️ Project Structure
student_management_system/
│
├── static/
│   └── style.css                   # Application styling
│
├── templates/
│   ├── login.html                  # Login page
│   ├── teacher_dashboard.html      # Teacher dashboard
│   ├── student_dashboard.html      # Student dashboard
│   └── edit.html                   # Edit student details
│
├── app.py                          # Flask application entry point
├── init_db.py                      # Database initialization script
├── students.db                    # SQLite database
│
├── LICENSE
└── README.md
````
🔄 Application Workflow

User logs in using assigned credentials

System validates role (Teacher / Student)

User is redirected to the respective dashboard

Teacher performs database operations (CRUD)

Student views assigned records securely

🖥️ Application Screenshots
Login Interface

<img width="1366" height="768" alt="Screenshot (60)" src="https://github.com/user-attachments/assets/09119cde-36df-43ed-9b51-b071b76f335f" />

Secure login page for both teachers and students.

Teacher Dashboard

<img width="1366" height="768" alt="Screenshot (61)" src="https://github.com/user-attachments/assets/0ccdb0be-b82e-469f-a9a7-ce4e29725c93" />

Teacher interface for adding, editing, searching, and exporting student records.

Student Login

<img width="1366" height="768" alt="Screenshot (62)" src="https://github.com/user-attachments/assets/537002f6-ea25-44dd-baf5-25068b5a12fd" />

Student authentication interface with restricted access.

Student Dashboard

<img width="1366" height="768" alt="Screenshot (63)" src="https://github.com/user-attachments/assets/1eba4bf2-cb27-4af9-a88a-78df128c00f9" />

Read-only dashboard allowing students to view their records.

⚙️ Installation & Usage
1️⃣ Clone the Repository
git clone <your-repository-url>
cd student_management_system

2️⃣ Create a Virtual Environment (Optional)
python -m venv venv
source venv/binactivate     # Windows: venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Initialize Database
python init_db.py

5️⃣ Run the Application
python app.py

6️⃣ Access the Application
http://127.0.0.1:5000/login

🧪 Technologies Used

Python

Flask

SQLite

HTML & CSS

CSV Export

Role-Based Authentication

🔬 Technical Highlights

Database-driven web application

Secure role-based access control

Clean separation of frontend and backend

Persistent data storage using SQLite

Designed following real-world IT system practices

🔮 Future Enhancements

Password hashing and encryption

User registration module

Attendance and marks management

Migration to MySQL / PostgreSQL

ERP system integration

👤 Author

M V Karthikeya
Computer Science Engineer
Interests: Database Systems, Backend Development, IT Systems

GitHub: https://github.com/Mvkarthikeya07

📜 License

This project is licensed under the MIT License.

⭐ Final Remarks

This project represents a real-world database management system, developed under an industrial internship environment, demonstrating strong understanding of DBMS concepts, IT workflows, and enterprise-grade system design.
