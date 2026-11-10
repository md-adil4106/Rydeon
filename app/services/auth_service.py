"""
Rydeon - Authentication & Role Security Service
------------------------------------------------
Provides secure user registration, password hashing via Werkzeug,
credential authentication, and role validation using MySQL.
"""

import re
from werkzeug.security import generate_password_hash, check_password_hash
from app.database.db import execute_query
from app.services.user_service import get_user_by_email

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def validate_registration_input(full_name, email, phone, password, confirm_password=None):
    """
    Validates registration inputs.
    Returns (True, None) if valid, or (False, error_message) if invalid.
    """
    if not full_name or len(full_name.strip()) < 2:
        return False, "Full name must be at least 2 characters."

    if not email or not EMAIL_REGEX.match(email.strip()):
        return False, "Please provide a valid email address."

    clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone or '')
    if len(clean_phone) < 7:
        return False, "Please enter a valid contact phone number."

    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters in length."

    if confirm_password is not None and password != confirm_password:
        return False, "Passwords do not match."

    return True, None

def register_user(full_name, email, phone, password, role='customer'):
    """
    Registers a new user into the database with a hashed password.
    Prevents duplicate email registrations.
    """
    clean_name = full_name.strip()
    clean_email = email.strip().lower()
    clean_phone = phone.strip()

    is_valid, error = validate_registration_input(clean_name, clean_email, clean_phone, password)
    if not is_valid:
        raise ValueError(error)

    if role not in ('customer', 'admin'):
        raise ValueError("Invalid role specified.")

    # Check for existing email
    existing_user = get_user_by_email(clean_email)
    if existing_user:
        raise ValueError("An account with this email address is already registered.")

    # Hash password securely
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    sql = """
        INSERT INTO users (full_name, email, phone, password_hash, role)
        VALUES (%s, %s, %s, %s, %s)
    """
    result = execute_query(sql, (clean_name, clean_email, clean_phone, password_hash, role), commit=True)
    new_user_id = result['lastrowid']

    # Retrieve and return created user
    user = execute_query("SELECT id, full_name, email, phone, role, created_at FROM users WHERE id = %s", (new_user_id,), fetch_one=True)
    return user

def authenticate_user(email, password):
    """
    Authenticates a user by email and plaintext password.
    Returns sanitized user dict if authenticated, otherwise None.
    """
    if not email or not password:
        return None

    clean_email = email.strip().lower()
    user = get_user_by_email(clean_email)

    if not user:
        return None

    if not check_password_hash(user['password_hash'], password):
        return None

    # Sanitize user dict (remove password_hash)
    return {
        "id": user['id'],
        "full_name": user['full_name'],
        "email": user['email'],
        "phone": user['phone'],
        "role": user['role'],
        "created_at": user['created_at']
    }

def create_admin_account(full_name, email, phone, password):
    """
    Development / operational utility to safely create an administrator account.
    """
    return register_user(full_name, email, phone, password, role='admin')
