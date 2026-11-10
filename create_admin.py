"""
Rydeon - Administrative Account Initialization CLI
--------------------------------------------------
Development & Operational utility to safely initialize or reset an
administrator account without exposing credentials in source control.

Usage:
  Interactive Mode:
    python create_admin.py

  Automated / CI / Docker Mode (via environment variables):
    set ADMIN_EMAIL=admin@rydeon-rentals.com
    set ADMIN_PASSWORD=YourSecureAdminPassword123!
    python create_admin.py --env
"""

import os
import sys
import getpass
from werkzeug.security import generate_password_hash

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.db import execute_query
from app.services.auth_service import validate_registration_input

def create_or_update_admin(full_name, email, phone, password):
    """Creates a new admin account or updates existing user to admin with new password."""
    clean_name = full_name.strip()
    clean_email = email.strip().lower()
    clean_phone = phone.strip()

    is_valid, error = validate_registration_input(clean_name, clean_email, clean_phone, password)
    if not is_valid:
        print(f"[ERROR] Validation failed: {error}")
        return False

    password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    sql = """
        INSERT INTO users (full_name, email, phone, password_hash, role)
        VALUES (%s, %s, %s, %s, 'admin')
        ON DUPLICATE KEY UPDATE
            full_name = VALUES(full_name),
            phone = VALUES(phone),
            password_hash = VALUES(password_hash),
            role = 'admin';
    """
    execute_query(sql, (clean_name, clean_email, clean_phone, password_hash), commit=True)
    print(f"[SUCCESS] Administrator account for '{clean_email}' successfully initialized with role 'admin'.")
    return True

def main():
    print("=" * 65)
    print("  RYDEON - SECURE ADMINISTRATOR INITIALIZATION UTILITY")
    print("=" * 65)

    if "--env" in sys.argv:
        email = os.environ.get("ADMIN_EMAIL", "admin@rydeon-rentals.com")
        password = os.environ.get("ADMIN_PASSWORD")
        full_name = os.environ.get("ADMIN_NAME", "System Administrator")
        phone = os.environ.get("ADMIN_PHONE", "+1-800-555-0100")

        if not password:
            print("[ERROR] Automated mode requires ADMIN_PASSWORD environment variable.")
            sys.exit(1)

        success = create_or_update_admin(full_name, email, phone, password)
        sys.exit(0 if success else 1)

    # Interactive Mode
    try:
        full_name = input("Enter Administrator Full Name [System Administrator]: ").strip() or "System Administrator"
        email = input("Enter Administrator Email [admin@rydeon-rentals.com]: ").strip() or "admin@rydeon-rentals.com"
        phone = input("Enter Contact Phone [+1-800-555-0100]: ").strip() or "+1-800-555-0100"

        password = getpass.getpass("Enter Secure Password (min 8 characters): ")
        confirm_password = getpass.getpass("Confirm Secure Password: ")

        if password != confirm_password:
            print("[ERROR] Passwords do not match. Aborting.")
            sys.exit(1)

        create_or_update_admin(full_name, email, phone, password)
    except (KeyboardInterrupt, EOFError):
        print("\n[CANCELLED] Operation aborted by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()
