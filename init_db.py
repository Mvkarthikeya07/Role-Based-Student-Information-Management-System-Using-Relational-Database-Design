"""Initialize and seed Supabase database."""

from db import seed_default_data, verify_connection


def main() -> int:
    print("=" * 60)
    print("Student Management System - Database Initialization")
    print("=" * 60)

    print("Step 1: Verifying Supabase connection...")
    try:
        verify_connection()
        print("OK: Supabase connection verified")
    except Exception as exc:
        print(f"ERROR: Connection check failed: {exc}")
        return 1

    print("Step 2: Seeding default data...")
    try:
        seed_default_data()
        print("OK: Default data initialized")
    except Exception as exc:
        print(f"ERROR: Seed failed: {exc}")
        return 1

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
