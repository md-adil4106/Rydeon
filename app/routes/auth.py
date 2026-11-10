"""
Rydeon - Authentication Routes Blueprint
----------------------------------------
Handles customer and administrator login, registration, and logout workflows.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services import auth_service
from app.services.csrf import validate_csrf_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Customer & Admin Authentication."""
    # If already logged in, redirect based on role
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('frontend.dashboard'))

    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf_token(csrf_token):
            flash("Security validation failed (CSRF token missing or invalid). Please refresh.", "danger")
            return render_template('login.html'), 400

        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both your email address and password.", "danger")
            return render_template('login.html', email=email), 400

        user = auth_service.authenticate_user(email, password)
        if not user:
            flash("Invalid email address or password. Please verify your credentials.", "danger")
            return render_template('login.html', email=email), 401

        # Establish secure session
        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['email'] = user['email']
        session['role'] = user['role']
        session.permanent = True

        flash(f"Welcome back, {user['full_name']}!", "success")

        # Redirect to intended next URL or role-based landing
        next_url = request.args.get('next')
        if next_url and next_url.startswith('/') and not next_url.startswith('//') and next_url not in ('/login', '/logout'):
            return redirect(next_url)

        if user['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('frontend.dashboard'))

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Customer Account Creation."""
    if 'user_id' in session:
        return redirect(url_for('frontend.dashboard'))

    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf_token(csrf_token):
            flash("Security validation failed (CSRF token invalid). Please refresh.", "danger")
            return render_template('register.html'), 400

        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        form_data = {
            "full_name": full_name,
            "email": email,
            "phone": phone
        }

        if password != confirm_password:
            flash("Passwords do not match. Please re-enter both fields.", "danger")
            return render_template('register.html', **form_data), 400

        try:
            user = auth_service.register_user(
                full_name=full_name,
                email=email,
                phone=phone,
                password=password,
                role='customer'
            )
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template('register.html', **form_data), 400

        # Auto-login after successful registration
        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['email'] = user['email']
        session['role'] = user['role']
        session.permanent = True

        flash(f"Registration successful! Welcome to Rydeon, {user['full_name']}.", "success")
        return redirect(url_for('frontend.dashboard'))

    return render_template('register.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Secure Session Termination."""
    user_name = session.get('user_name', '')
    session.clear()
    flash(f"You have been signed out successfully. Goodbye{', ' + user_name if user_name else ''}.", "info")
    return redirect(url_for('frontend.index'))
