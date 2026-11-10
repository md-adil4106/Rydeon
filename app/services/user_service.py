"""
Rydeon - User Service Layer
---------------------------
Retrieves user profiles and authentication records from MySQL.
"""

from app.database.db import execute_query

def get_user_by_email(email):
    """Retrieves a user record by email address."""
    sql = """
        SELECT id, full_name, email, phone, password_hash, role, created_at
        FROM users
        WHERE email = %s
    """
    return execute_query(sql, (email,), fetch_one=True)

def get_user_by_id(user_id):
    """Retrieves a user record by primary key ID."""
    sql = """
        SELECT id, full_name, email, phone, role, created_at
        FROM users
        WHERE id = %s
    """
    return execute_query(sql, (user_id,), fetch_one=True)

def get_default_preview_user():
    """Retrieves the seeded default customer for frontend preview."""
    user = get_user_by_email("alexander.wright@example.com")
    if user:
        return user
    # Fallback to the first customer in database
    return execute_query("SELECT id, full_name, email, phone, role, created_at FROM users WHERE role='customer' LIMIT 1", fetch_one=True)
