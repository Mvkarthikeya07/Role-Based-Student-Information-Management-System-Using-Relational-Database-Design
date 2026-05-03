"""Database module for Supabase-backed Student Information System."""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from supabase import Client, create_client
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()


class SupabaseConfig:
    """Supabase configuration and client management."""

    SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize project URL in case /rest/v1 was provided."""
        normalized = (url or "").strip().rstrip("/")
        if normalized.endswith("/rest/v1"):
            normalized = normalized[: -len("/rest/v1")]
        return normalized

    @staticmethod
    def get_client() -> Client:
        normalized_url = SupabaseConfig.normalize_url(SupabaseConfig.SUPABASE_URL)
        if not normalized_url:
            raise ValueError("SUPABASE_URL is not set in .env")
        if not SupabaseConfig.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY is not set in .env")
        return create_client(normalized_url, SupabaseConfig.SUPABASE_KEY)


class DatabaseOps:
    """Database operations wrapper."""

    def __init__(self):
        self.client = SupabaseConfig.get_client()

    def create_user(self, username: str, password: str, email: str, role: str, security_question: str, security_answer: str):
        data = {
            "username": username,
            "password": generate_password_hash(password),
            "email": email,
            "role": role,
            "security_question": security_question,
            "security_answer": security_answer.lower().strip(),
        }
        response = self.client.table("users").insert(data).execute()
        return response.data

    def get_user_by_username(self, username: str):
        response = self.client.table("users").select("*").eq("username", username).execute()
        return response.data[0] if response.data else None

    def verify_user_password(self, username: str, password: str):
        user = self.get_user_by_username(username)
        if user and check_password_hash(user["password"], password):
            return user
        return None

    def update_user_password(self, username: str, new_password: str):
        hashed_password = generate_password_hash(new_password)
        response = self.client.table("users").update({"password": hashed_password}).eq("username", username).execute()
        return response.data

    def create_student(
        self,
        name: str,
        course: str,
        class_name: str,
        section: str,
        parent_phone: str,
        parent_email: str,
        user_id: str = None,
        **kwargs,
    ):
        # Allow callers that pass class="..." from forms or seed dictionaries.
        resolved_class = class_name if class_name is not None else kwargs.get("class")
        data = {
            "name": name,
            "course": course,
            "class": resolved_class,
            "section": section,
            "parent_phone": parent_phone,
            "parent_email": parent_email,
        }
        if user_id:
            data["user_id"] = user_id
        response = self.client.table("students").insert(data).execute()
        return response.data

    def get_all_students(self):
        response = self.client.table("students").select("*").execute()
        return response.data

    def search_students(self, keyword: str):
        all_students = self.get_all_students()
        keyword_lower = keyword.lower()
        return [
            student
            for student in all_students
            if (
                keyword_lower in student.get("name", "").lower()
                or keyword_lower in student.get("course", "").lower()
                or keyword_lower in student.get("class", "").lower()
                or keyword_lower in student.get("section", "").lower()
            )
        ]

    def get_student_by_id(self, student_id: str):
        response = self.client.table("students").select("*").eq("id", student_id).execute()
        return response.data[0] if response.data else None

    def update_student(self, student_id: str, **kwargs):
        response = self.client.table("students").update(kwargs).eq("id", student_id).execute()
        return response.data

    def delete_student(self, student_id: str):
        response = self.client.table("students").delete().eq("id", student_id).execute()
        return response.data

    def create_password_reset_token(self, username: str, token: str, expires_in_hours: int = 24):
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        data = {
            "user_id": user["id"],
            "username": username,
            "token": token,
            "expires_at": expires_at.isoformat(),
        }
        response = self.client.table("password_reset").insert(data).execute()
        return response.data

    def verify_password_reset_token(self, token: str):
        response = self.client.table("password_reset").select("*").eq("token", token).execute()
        if not response.data:
            return None, "Invalid token"
        reset_record = response.data[0]
        expires_at = datetime.fromisoformat(reset_record["expires_at"].replace("Z", "+00:00"))
        if datetime.utcnow() > expires_at:
            return None, "Token expired"
        return reset_record, None


def verify_connection() -> bool:
    """Verify that Supabase connection and key tables are accessible."""
    client = SupabaseConfig.get_client()
    client.table("users").select("id", count="exact").limit(1).execute()
    client.table("students").select("id", count="exact").limit(1).execute()
    return True


def seed_default_data() -> bool:
    """Create default users and sample student rows if missing."""
    db = DatabaseOps()

    if not db.get_user_by_username("teacher"):
        db.create_user(
            username="teacher",
            password="1234",
            email="teacher@example.com",
            role="teacher",
            security_question="What is your first pet's name?",
            security_answer="fluffy",
        )

    if not db.get_user_by_username("student"):
        db.create_user(
            username="student",
            password="1234",
            email="student@example.com",
            role="student",
            security_question="What is your first pet's name?",
            security_answer="buddy",
        )

    if len(db.get_all_students()) == 0:
        sample_students = [
            {
                "name": "Raj Kumar",
                "course": "B.Tech",
                "class": "II Year",
                "section": "A",
                "parent_phone": "9876543210",
                "parent_email": "parent1@example.com",
            },
            {
                "name": "Priya Singh",
                "course": "B.Tech",
                "class": "II Year",
                "section": "B",
                "parent_phone": "9876543211",
                "parent_email": "parent2@example.com",
            },
            {
                "name": "Amit Patel",
                "course": "B.Com",
                "class": "I Year",
                "section": "A",
                "parent_phone": "9876543212",
                "parent_email": "parent3@example.com",
            },
            {
                "name": "Neha Verma",
                "course": "B.Tech",
                "class": "III Year",
                "section": "C",
                "parent_phone": "9876543213",
                "parent_email": "parent4@example.com",
            },
            {
                "name": "Arun Kumar",
                "course": "B.Sc",
                "class": "I Year",
                "section": "B",
                "parent_phone": "9876543214",
                "parent_email": "parent5@example.com",
            },
        ]
        for student in sample_students:
            db.create_student(**student)

    return True
