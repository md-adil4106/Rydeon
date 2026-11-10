"""
Rydeon - Frontend and Navigation Routes
---------------------------------------
Connects user interface templates with MySQL services for vehicles,
customer bookings, and fleet exploration.
"""

import os
from flask import Blueprint, render_template, request, jsonify, session, send_from_directory, abort, current_app
from app.services import vehicle_service, booking_service, user_service
from app.services.decorators import login_required
from app.database.db import check_db_health, execute_query

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def index():
    """Landing Page with hero, quick search, featured fleet, and benefits."""
    try:
        featured_vehicles = vehicle_service.get_featured_vehicles(limit=3)
        all_vehicles = vehicle_service.get_all_vehicles()
    except Exception as err:
        return render_template('errors/db_error.html', error=str(err)), 503

    return render_template(
        'index.html',
        featured_vehicles=featured_vehicles,
        all_vehicles=all_vehicles
    )

@frontend_bp.route('/catalogue')
@frontend_bp.route('/vehicles')
def catalogue():
    """Vehicle Catalogue with search, category filters, and detail modals."""
    category = request.args.get('category')
    search = request.args.get('search')
    max_price = request.args.get('max_price')

    try:
        vehicles = vehicle_service.get_all_vehicles(
            category=category,
            search=search,
            max_price=max_price
        )
    except Exception as err:
        return render_template('errors/db_error.html', error=str(err)), 503

    return render_template(
        'catalogue.html',
        vehicles=vehicles
    )

@frontend_bp.route('/dashboard')
@login_required
def dashboard():
    """Customer Dashboard protected by authentication. Displays ONLY current user records."""
    user_id = session['user_id']

    try:
        user = user_service.get_user_by_id(user_id)
        if not user:
            # Fallback if session user was deleted
            session.clear()
            return render_template('login.html'), 401

        active_booking = booking_service.get_user_active_booking(user_id)
        booking_history = booking_service.get_user_booking_history(user_id)
        stats = booking_service.get_user_stats(user_id)
        recommended = vehicle_service.get_featured_vehicles(limit=3)

        user_display = {
            "id": user['id'],
            "name": user.get('full_name', 'Valued Customer'),
            "email": user.get('email', ''),
            "phone": user.get('phone', ''),
            "tier": "Executive Gold" if user.get('role') == 'customer' else "Administrator",
            "stats": stats
        }
    except Exception as err:
        return render_template('errors/db_error.html', error=str(err)), 503

    return render_template(
        'dashboard.html',
        user=user_display,
        current_booking=active_booking,
        history=booking_history,
        recommended_vehicles=recommended
    )

@frontend_bp.route('/api/health')
def health():
    """API healthcheck endpoint verifying MySQL database connectivity."""
    is_healthy, message = check_db_health()
    status_code = 200 if is_healthy else 503
    return jsonify({
        "status": "healthy" if is_healthy else "unhealthy",
        "database": "MySQL",
        "detail": message
    }), status_code

@frontend_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """
    Safely serves uploaded static assets (documents, vehicle photos).
    Enforces strict file extension whitelisting, prevents execution of
    server-side code, prevents directory traversal, and enforces privacy access control.
    """
    # 1. Directory traversal & dotfile protection
    norm_name = os.path.normpath(filename)
    if '..' in norm_name or norm_name.startswith(('.', '/', '\\')):
        abort(404)

    # 2. Strict file extension whitelist
    allowed_exts = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}
    if '.' not in norm_name:
        abort(404)
    ext = norm_name.rsplit('.', 1)[1].lower()
    if ext not in allowed_exts:
        # Strictly block script/executable types (.py, .php, .exe, .sh, .html, etc.)
        abort(403)

    # 3. Privacy control for customer verification documents
    if norm_name.startswith('documents'):
        if 'user_id' not in session:
            abort(401)
        if session.get('role') != 'admin':
            # Verify customer owns the requested document
            relative_search = f"%{norm_name.replace('\\', '/')}%"
            doc_owner = execute_query(
                "SELECT user_id FROM documents WHERE file_path LIKE %s",
                (relative_search,),
                fetch_one=True
            )
            if doc_owner and doc_owner['user_id'] != session['user_id']:
                abort(403)

    base_upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads') if current_app else 'uploads'
    upload_path = os.path.abspath(base_upload_dir)

    response = send_from_directory(upload_path, norm_name)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response
