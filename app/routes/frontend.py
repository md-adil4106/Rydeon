"""
Rydeon - Frontend and Navigation Routes
---------------------------------------
Connects user interface templates with MySQL services for vehicles,
customer bookings, and fleet exploration.
"""

from flask import Blueprint, render_template, request, jsonify, session
from app.services import vehicle_service, booking_service, user_service
from app.services.decorators import login_required
from app.database.db import check_db_health

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
