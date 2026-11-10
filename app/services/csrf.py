"""
Rydeon - Lightweight CSRF Protection
------------------------------------
Provides session-bound cryptographic CSRF token generation and validation.
"""

import hmac
import secrets
from flask import session, current_app

def generate_csrf_token():
    """Generates or retrieves the session-bound CSRF token."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token(token):
    """
    Validates a submitted CSRF token against the current session token.
    Uses constant-time comparison to prevent timing attacks.
    """
    if current_app and current_app.config.get('TESTING') and not current_app.config.get('WTF_CSRF_ENABLED', True):
        return True

    session_token = session.get('csrf_token')
    if not session_token or not token:
        return False

    return hmac.compare_digest(str(session_token), str(token))
