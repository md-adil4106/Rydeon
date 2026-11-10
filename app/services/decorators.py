"""
Rydeon - Route Security Decorators
----------------------------------
Protects routes requiring authenticated user sessions or administrative privileges.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request, abort, jsonify

def login_required(f):
    """Decorator ensuring that the user is authenticated in the current session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required", "status": 401}), 401
            flash("Please sign in to access your account dashboard.", "warning")
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator ensuring that the logged-in user possesses administrative privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required", "status": 401}), 401
            flash("Please sign in with administrator credentials.", "warning")
            return redirect(url_for('auth.login', next=request.path))

        if session.get('role') != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({"error": "Forbidden: Administrator role required", "status": 403}), 403
            flash("Access forbidden: You do not possess administrative permissions.", "danger")
            abort(403)

        return f(*args, **kwargs)
    return decorated_function
