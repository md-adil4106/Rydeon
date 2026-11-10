"""
Rydeon - Authentication & Role-Based Access Control (RBAC) Test Suite
---------------------------------------------------------------------
Validates:
1. Customer registration with input validation.
2. Duplicate email registration rejection.
3. Password hashing security (never stored in plaintext).
4. Customer login and redirect to /dashboard.
5. Administrator login and redirect to /admin/dashboard.
6. Incorrect password and non-existent account rejection.
7. Secure session termination on logout.
8. Role-based route protection:
   - Anonymous access blocked from /dashboard and /admin.
   - Customer blocked from administrative routes (403 Forbidden).
   - Administrator permitted access to /admin/dashboard.
"""

import pytest
from app import create_app
from config.config import TestingConfig
from app.database.db import execute_query
from create_admin import create_or_update_admin

@pytest.fixture(scope="module")
def app():
    app = create_app(TestingConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# ==============================================================================
# 1. REGISTRATION TESTS
# ==============================================================================
def test_successful_customer_registration(client):
    """Verify new customer registration with valid credentials."""
    # Ensure test email does not exist prior
    test_email = "newcustomer.test@example.com"
    execute_query("DELETE FROM users WHERE email = %s", (test_email,), commit=True)

    payload = {
        "full_name": "Elena Rostova",
        "email": test_email,
        "phone": "+1 (555) 839-2019",
        "password": "SecurePassword2026!",
        "confirm_password": "SecurePassword2026!",
        "terms": "on"
    }

    response = client.post('/register', data=payload, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'] == '/dashboard'

    # Verify user exists in MySQL and password is not plaintext
    user = execute_query("SELECT id, full_name, email, password_hash, role FROM users WHERE email = %s", (test_email,), fetch_one=True)
    assert user is not None
    assert user['full_name'] == "Elena Rostova"
    assert user['role'] == "customer"
    assert "SecurePassword2026!" not in user['password_hash']
    assert user['password_hash'].startswith('pbkdf2:sha256:')

def test_duplicate_email_registration_rejection(client):
    """Verify duplicate email registration is rejected with appropriate error."""
    payload = {
        "full_name": "Another Person",
        "email": "alexander.wright@example.com",  # Already seeded in DB
        "phone": "+1 (555) 999-0000",
        "password": "DifferentPassword2026!",
        "confirm_password": "DifferentPassword2026!",
        "terms": "on"
    }

    response = client.post('/register', data=payload, follow_redirects=True)
    assert response.status_code == 400
    html = response.data.decode('utf-8')
    assert "already registered" in html.lower()

def test_registration_validation_mismatched_passwords(client):
    """Verify registration fails when password and confirm_password do not match."""
    payload = {
        "full_name": "Mismatch Tester",
        "email": "mismatch@example.com",
        "phone": "+1 (555) 123-4567",
        "password": "Password1234!",
        "confirm_password": "CompletelyDifferentPassword!",
        "terms": "on"
    }

    response = client.post('/register', data=payload, follow_redirects=True)
    assert response.status_code == 400
    html = response.data.decode('utf-8')
    assert "passwords do not match" in html.lower()

def test_registration_validation_short_password(client):
    """Verify registration rejects passwords shorter than 8 characters."""
    payload = {
        "full_name": "Short Password User",
        "email": "shortpass@example.com",
        "phone": "+1 (555) 123-4567",
        "password": "short",
        "confirm_password": "short",
        "terms": "on"
    }

    response = client.post('/register', data=payload, follow_redirects=True)
    assert response.status_code == 400
    html = response.data.decode('utf-8')
    assert "at least 8 characters" in html.lower()

# ==============================================================================
# 2. LOGIN & AUTHENTICATION TESTS
# ==============================================================================
def test_successful_customer_login(client):
    """Verify customer authenticates and is redirected to /dashboard."""
    payload = {
        "email": "alexander.wright@example.com",
        "password": "CustomerSecret2026!"
    }

    response = client.post('/login', data=payload, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'] == '/dashboard'

    with client.session_transaction() as sess:
        assert sess['user_id'] is not None
        assert sess['role'] == 'customer'
        assert sess['user_name'] == 'Alexander Wright'

def test_successful_admin_login(client):
    """Verify administrator authenticates and is redirected to /admin/dashboard."""
    payload = {
        "email": "admin@rydeon-rentals.com",
        "password": "AdminSecret2026!"
    }

    response = client.post('/login', data=payload, follow_redirects=False)
    assert response.status_code == 302
    assert '/admin' in response.headers['Location']

    with client.session_transaction() as sess:
        assert sess['user_id'] is not None
        assert sess['role'] == 'admin'

def test_incorrect_password_rejection(client):
    """Verify authentication fails on incorrect password."""
    payload = {
        "email": "alexander.wright@example.com",
        "password": "WrongPassword999!"
    }

    response = client.post('/login', data=payload, follow_redirects=True)
    assert response.status_code == 401
    html = response.data.decode('utf-8')
    assert "invalid email address or password" in html.lower()

    with client.session_transaction() as sess:
        assert 'user_id' not in sess

def test_nonexistent_user_login_rejection(client):
    """Verify non-existent email cannot authenticate."""
    payload = {
        "email": "ghost.user@doesnotexist.com",
        "password": "AnyPassword123!"
    }

    response = client.post('/login', data=payload, follow_redirects=True)
    assert response.status_code == 401
    html = response.data.decode('utf-8')
    assert "invalid email address or password" in html.lower()

# ==============================================================================
# 3. LOGOUT TEST
# ==============================================================================
def test_logout_clears_session(client):
    """Verify logout terminates user session and redirects to index."""
    # First establish session
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_name'] = 'Alexander Wright'
        sess['role'] = 'customer'

    # Perform logout
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'] == '/'

    # Verify session is empty
    with client.session_transaction() as sess:
        assert 'user_id' not in sess
        assert 'role' not in sess

# ==============================================================================
# 4. ROLE-BASED ROUTE PROTECTION (RBAC)
# ==============================================================================
def test_anonymous_cannot_access_customer_dashboard(client):
    """Verify unauthenticated user cannot access /dashboard."""
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_anonymous_cannot_access_admin_dashboard(client):
    """Verify unauthenticated user cannot access /admin/dashboard."""
    response = client.get('/admin/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_customer_cannot_access_admin_dashboard(client):
    """Verify authenticated customer is forbidden (403) from /admin/dashboard."""
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_name'] = 'Alexander Wright'
        sess['role'] = 'customer'

    response = client.get('/admin/dashboard', follow_redirects=False)
    assert response.status_code == 403
    html = response.data.decode('utf-8')
    assert "403 - Access Forbidden" in html

def test_admin_can_access_admin_dashboard(client):
    """Verify administrator has access to /admin/dashboard."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Admin User'
        sess['role'] = 'admin'

    response = client.get('/admin/dashboard')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "Fleet Operations" in html
    assert "Admin Privileges Active" in html

# ==============================================================================
# 5. ADMIN INITIALIZATION CLI SCRIPT TEST
# ==============================================================================
def test_create_or_update_admin_utility():
    """Verify create_admin script creates an admin with hashed credentials."""
    test_admin_email = "ops.manager@rydeon-rentals.com"
    success = create_or_update_admin(
        full_name="Operations Manager",
        email=test_admin_email,
        phone="+1-800-555-0199",
        password="OpsManagerSecret2026!"
    )
    assert success is True

    admin_row = execute_query("SELECT full_name, email, role, password_hash FROM users WHERE email = %s", (test_admin_email,), fetch_one=True)
    assert admin_row is not None
    assert admin_row['role'] == 'admin'
    assert "OpsManagerSecret2026!" not in admin_row['password_hash']
