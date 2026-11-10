"""
Rydeon - Frontend and Navigation Routes
---------------------------------------
Connects user interface templates with MySQL services for vehicles,
customer bookings, and fleet exploration.
"""

from flask import Blueprint, render_template, request, jsonify
from app.services import vehicle_service, booking_service, user_service
from app.database.db import check_db_health

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def index():
    """Landing Page with hero, quick search, featured fleet, and benefits."""
    try:
        featured_vehicles = vehicle_service.get_featured_vehicles(limit=3)
        all_vehicles = vehicle_service.get_all_vehicles()
    except Exception as err:
        # If DB connection fails, render graceful DB error page
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

@frontend_bp.route('/login')
def login():
    """Customer & Admin Login Screen."""
    return render_template('login.html')

@frontend_bp.route('/register')
def register():
    """New Customer Registration Screen."""
    return render_template('register.html')

@frontend_bp.route('/dashboard')
def dashboard():
    """Customer Dashboard with active rentals, booking history, and vehicle recommendations."""
    try:
        user = user_service.get_default_preview_user()
        user_id = user['id'] if user else 1

        active_booking = booking_service.get_user_active_booking(user_id)
        booking_history = booking_service.get_user_booking_history(user_id)
        stats = booking_service.get_user_stats(user_id)
        recommended = vehicle_service.get_featured_vehicles(limit=3)

        user_display = {
            "name": user.get('full_name', 'Alexander Wright') if user else 'Alexander Wright',
            "email": user.get('email', 'alexander.wright@example.com') if user else 'alexander.wright@example.com',
            "phone": user.get('phone', '+1 (555) 389-7241') if user else '+1 (555) 389-7241',
            "tier": "Executive Gold",
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
