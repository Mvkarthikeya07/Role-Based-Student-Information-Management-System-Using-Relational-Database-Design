-- =====================================================
-- SUPABASE DATABASE SCHEMA
-- Role-Based Student Information Management System
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. USERS TABLE (Authentication)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('teacher', 'student')),
    security_question TEXT NOT NULL,
    security_answer TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Create index on username for faster lookups
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- =====================================================
-- 2. STUDENTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    register_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    year_of_joining DATE NOT NULL,
    class TEXT NOT NULL,
    section TEXT NOT NULL,
    parent_phone TEXT,
    parent_email TEXT,
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for search functionality
CREATE INDEX idx_students_register_no ON students(register_no);
CREATE INDEX idx_students_name ON students(name);
CREATE INDEX idx_students_year_of_joining ON students(year_of_joining);
CREATE INDEX idx_students_class ON students(class);
CREATE INDEX idx_students_section ON students(section);

-- =====================================================
-- 3. VERIFICATION CODES TABLE (OTP for Email Verification)
-- =====================================================
CREATE TABLE IF NOT EXISTS verification_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    otp TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for quick lookups
CREATE INDEX idx_verification_codes_email ON verification_codes(email);
CREATE INDEX idx_verification_codes_otp ON verification_codes(otp);
CREATE INDEX idx_verification_codes_expires_at ON verification_codes(expires_at);

-- =====================================================
-- 4. PASSWORD RESET TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS password_reset (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    used_at TIMESTAMP WITH TIME ZONE
);

-- Create index on token for quick lookups
CREATE INDEX idx_password_reset_token ON password_reset(token);
CREATE INDEX idx_password_reset_expires_at ON password_reset(expires_at);

-- =====================================================
-- 4. AUDIT LOG TABLE (Optional - for tracking changes)
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    table_name TEXT,
    record_id UUID,
    changes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address TEXT
);

-- Create index for audit queries
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- =====================================================
-- 5. ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE password_reset ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Users table policies
CREATE POLICY "Users can view their own profile"
    ON users FOR SELECT
    USING (auth.uid()::text = id::text);

CREATE POLICY "Admins can view all users"
    ON users FOR SELECT
    USING (role = 'teacher');

-- Students table policies
CREATE POLICY "Teachers can view all students"
    ON students FOR SELECT
    USING ((SELECT role FROM users WHERE id = auth.uid()) = 'teacher');

CREATE POLICY "Students can view all students (read-only dashboard)"
    ON students FOR SELECT
    USING ((SELECT role FROM users WHERE id = auth.uid()) = 'student');

CREATE POLICY "Teachers can insert students"
    ON students FOR INSERT
    WITH CHECK ((SELECT role FROM users WHERE id = auth.uid()) = 'teacher');

CREATE POLICY "Teachers can update students"
    ON students FOR UPDATE
    USING ((SELECT role FROM users WHERE id = auth.uid()) = 'teacher');

CREATE POLICY "Teachers can delete students"
    ON students FOR DELETE
    USING ((SELECT role FROM users WHERE id = auth.uid()) = 'teacher');

-- Password reset policies
CREATE POLICY "Users can view their own password reset requests"
    ON password_reset FOR SELECT
    USING (auth.uid()::text = user_id::text);

-- =====================================================
-- 6. SAMPLE DATA (Optional)
-- =====================================================

-- Insert sample users
INSERT INTO users (username, password, email, role, security_question, security_answer, is_active)
VALUES 
    ('teacher', 'hashed_password_1', 'teacher@example.com', 'teacher', 'What is your first pet''s name?', 'fluffy', TRUE),
    ('student', 'hashed_password_2', 'student@example.com', 'student', 'What is your first pet''s name?', 'buddy', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Insert sample students
INSERT INTO students (register_no, name, year_of_joining, class, section, parent_phone, parent_email)
VALUES 
    ('REG001', 'Raj Kumar', '2023-06-01', 'II Year', 'A', '+919876543210', 'parent1@example.com'),
    ('REG002', 'Priya Singh', '2023-06-01', 'II Year', 'B', '+919876543211', 'parent2@example.com'),
    ('REG003', 'Amit Patel', '2024-06-01', 'I Year', 'A', '+919876543212', 'parent3@example.com')
ON CONFLICT DO NOTHING;

-- =====================================================
-- 7. UTILITY FUNCTIONS
-- =====================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger for students table
CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 8. VIEWS FOR COMMON QUERIES
-- =====================================================

-- View for getting student details
CREATE OR REPLACE VIEW student_view AS
SELECT
    id,
    register_no,
    name,
    year_of_joining,
    class,
    section,
    parent_phone,
    parent_email,
    enrollment_date,
    updated_at
FROM students;

-- =====================================================
-- 9. SAFE MIGRATION FOR EXISTING PROJECTS
-- =====================================================
/*
Run this block once on existing databases that still have `course`
and/or non-normalized `parent_phone` values.
*/
/*
BEGIN;

ALTER TABLE students
ADD COLUMN IF NOT EXISTS year_of_joining DATE;

UPDATE students
SET year_of_joining = COALESCE(year_of_joining, CURRENT_DATE);

ALTER TABLE students
ALTER COLUMN year_of_joining SET NOT NULL;

DROP INDEX IF EXISTS idx_students_course;
DROP VIEW IF EXISTS user_student_view;
DROP VIEW IF EXISTS student_view;

ALTER TABLE students
DROP COLUMN IF EXISTS course;

-- Normalize parent phone to +91XXXXXXXXXX using last 10 digits
UPDATE students
SET parent_phone = CASE
    WHEN parent_phone IS NULL OR parent_phone = '' THEN NULL
    ELSE '+91' || RIGHT(REGEXP_REPLACE(parent_phone, '\D', '', 'g'), 10)
END;

CREATE INDEX IF NOT EXISTS idx_students_year_of_joining
ON students(year_of_joining);

CREATE OR REPLACE VIEW student_view AS
SELECT
    id,
    register_no,
    name,
    year_of_joining,
    class,
    section,
    parent_phone,
    parent_email,
    enrollment_date,
    updated_at
FROM students;

COMMIT;
*/

-- =====================================================
-- NOTES FOR MIGRATION
-- =====================================================
/*
IMPORTANT MIGRATION STEPS:

1. Update your Flask app to use Supabase instead of SQLite:
   - Install: pip install supabase-py
   - Update connection string to Supabase

2. Password Hashing:
   - NEVER store plain text passwords
   - Use bcrypt or Argon2 for hashing
   - Example: from werkzeug.security import generate_password_hash

3. Authentication:
   - Consider using Supabase Auth instead of manual username/password
   - This provides better security and built-in session management

4. Environment Variables:
   - Store SUPABASE_URL and SUPABASE_KEY in .env file
   - Never commit these to version control

5. RLS Policies:
   - These need to be adjusted based on your actual auth implementation
   - If using Supabase Auth, policies will work seamlessly

6. Backups:
   - Set up automated backups in Supabase dashboard
   - Enable Point-In-Time Recovery (PITR)
*/
