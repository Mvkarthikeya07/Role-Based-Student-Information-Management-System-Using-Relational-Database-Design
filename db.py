"""Database module for Supabase-backed Student Information System."""

import os
import re
from datetime import datetime, timedelta

from dotenv import load_dotenv
from supabase import Client, create_client
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

def _hash_password(password: str) -> str:
    """Create a standard PBKDF2 password hash."""
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)


def _verify_password(stored_hash: str, password: str) -> bool:
    """Verify password using standard hash verification."""
    if not stored_hash:
        return False
    return check_password_hash(stored_hash, password)


def _normalize_indian_phone(phone: str) -> str:
    """Normalize to +91XXXXXXXXXX and validate exactly 10 local digits."""
    raw = (phone or "").strip()
    digits = re.sub(r"\D", "", raw)

    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]

    if len(digits) != 10:
        raise ValueError("Parent phone must be exactly 10 digits")

    return f"+91{digits}"


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

    def __init__(self, access_token: str = None, refresh_token: str = None):
        self.client = SupabaseConfig.get_client()
        if access_token and refresh_token:
            # Bind this client to the authenticated user session (RLS-aware requests).
            self.client.auth.set_session(access_token, refresh_token)

    def create_user(self, username: str, password: str, email: str, role: str, security_question: str, security_answer: str):
        data = {
            "username": username,
            "password": _hash_password(password),
            "email": email,
            "role": role,
            "security_question": security_question,
            "security_answer": security_answer.lower().strip(),
        }
        response = self.client.table("users").insert(data).execute()
        return response.data

    def sign_up_user(self, username: str, password: str, email: str, role: str, security_question: str, security_answer: str):
        """
        Create an auth user in Supabase Auth and a matching profile row in public.users.
        """
        auth_response = self.client.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"data": {"username": username, "role": role}},
            }
        )

        auth_user = getattr(auth_response, "user", None)
        auth_session = getattr(auth_response, "session", None)
        if not auth_user:
            raise ValueError("Sign up failed. Please verify email/password settings in Supabase Auth.")

        profile_data = {
            "id": auth_user.id,
            "username": username,
            "password": "_supabase_auth_managed_",
            "email": email,
            "role": role,
            "security_question": security_question,
            "security_answer": security_answer.lower().strip(),
            "is_active": True,
        }

        # Upsert keeps this idempotent if the user retries sign-up flow.
        self.client.table("users").upsert(profile_data, on_conflict="username").execute()
        return {"user": auth_user, "session": auth_session}

    def get_user_by_username(self, username: str):
        response = self.client.table("users").select("*").eq("username", username).execute()
        return response.data[0] if response.data else None

    def verify_user_password(self, username: str, password: str):
        user = self.get_user_by_username(username)
        if user and _verify_password(user["password"], password):
            return user
        return None

    def sign_in_user(self, login_identifier: str, password: str):
        """
        Authenticate via Supabase Auth (email+password).
        Accepts either username or email as login identifier.
        """
        identifier = (login_identifier or "").strip()
        if not identifier:
            return None

        if "@" in identifier:
            email = identifier
        else:
            profile = self.get_user_by_username(identifier)
            if not profile:
                return None
            email = profile.get("email", "")
            if not email:
                return None

        auth_response = self.client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        auth_user = getattr(auth_response, "user", None)
        auth_session = getattr(auth_response, "session", None)
        if not auth_user:
            return None

        profile_response = self.client.table("users").select("*").eq("id", auth_user.id).limit(1).execute()
        profile = profile_response.data[0] if profile_response.data else None
        if not profile:
            profile_response = self.client.table("users").select("*").eq("email", email).limit(1).execute()
            profile = profile_response.data[0] if profile_response.data else None

        if profile is None:
            return None

        return {"user": profile, "session": auth_session}

    def update_user_password(self, username: str, new_password: str):
        hashed_password = _hash_password(new_password)
        response = self.client.table("users").update({"password": hashed_password}).eq("username", username).execute()
        return response.data

    def create_student(
        self,
        register_no: str,
        name: str,
        year_of_joining: str,
        class_name: str,
        section: str,
        parent_phone: str,
        parent_email: str,
        **kwargs,
    ):
        # Allow callers that pass class="..." from forms or seed dictionaries.
        resolved_class = class_name if class_name is not None else kwargs.get("class")
        data = {
            "register_no": register_no,
            "name": name,
            "year_of_joining": year_of_joining,
            "class": resolved_class,
            "section": section,
            "parent_phone": _normalize_indian_phone(parent_phone),
            "parent_email": parent_email,
        }
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
                keyword_lower in student.get("register_no", "").lower()
                or keyword_lower in student.get("name", "").lower()
            )
        ]

    def get_student_by_register_no(self, register_no: str):
        response = self.client.table("students").select("*").eq("register_no", register_no).execute()
        return response.data[0] if response.data else None

    def get_student_by_id(self, student_id: str):
        response = self.client.table("students").select("*").eq("id", student_id).execute()
        return response.data[0] if response.data else None

    def update_student(self, student_id: str, **kwargs):
        if "parent_phone" in kwargs:
            kwargs["parent_phone"] = _normalize_indian_phone(kwargs["parent_phone"])
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
                "register_no": "REG001",
                "name": "Raj Kumar",
                "year_of_joining": "2023-06-01",
                "class": "II Year",
                "section": "A",
                "parent_phone": "+919876543210",
                "parent_email": "parent1@example.com",
            },
            {
                "register_no": "REG002",
                "name": "Priya Singh",
                "year_of_joining": "2023-06-01",
                "class": "II Year",
                "section": "B",
                "parent_phone": "+919876543211",
                "parent_email": "parent2@example.com",
            },
            {
                "register_no": "REG003",
                "name": "Amit Patel",
                "year_of_joining": "2024-06-01",
                "class": "I Year",
                "section": "A",
                "parent_phone": "+919876543212",
                "parent_email": "parent3@example.com",
            },
            {
                "register_no": "REG004",
                "name": "Neha Verma",
                "year_of_joining": "2022-06-01",
                "class": "III Year",
                "section": "C",
                "parent_phone": "+919876543213",
                "parent_email": "parent4@example.com",
            },
            {
                "register_no": "REG005",
                "name": "Arun Kumar",
                "year_of_joining": "2024-06-01",
                "class": "I Year",
                "section": "B",
                "parent_phone": "+919876543214",
                "parent_email": "parent5@example.com",
            },
        ]
        for student in sample_students:
            db.create_student(
                register_no=student["register_no"],
                name=student["name"],
                year_of_joining=student["year_of_joining"],
                class_name=student["class"],
                section=student["section"],
                parent_phone=student["parent_phone"],
                parent_email=student["parent_email"],
            )

    return True
