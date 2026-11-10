from flask import Blueprint, render_template
from app.services.sample_data import (
    SAMPLE_VEHICLES,
    SAMPLE_USER,
    SAMPLE_CURRENT_BOOKING,
    SAMPLE_BOOKING_HISTORY
)

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def index():
    """Landing Page with hero, quick search, featured fleet, and benefits."""
    featured_vehicles = [v for v in SAMPLE_VEHICLES if v.get('featured')]
    return render_template(
        'index.html',
        featured_vehicles=featured_vehicles,
        all_vehicles=SAMPLE_VEHICLES
    )

@frontend_bp.route('/catalogue')
@frontend_bp.route('/vehicles')
def catalogue():
    """Vehicle Catalogue with search, category filters, and detail modals."""
    return render_template(
        'catalogue.html',
        vehicles=SAMPLE_VEHICLES
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
    return render_template(
        'dashboard.html',
        user=SAMPLE_USER,
        current_booking=SAMPLE_CURRENT_BOOKING,
        history=SAMPLE_BOOKING_HISTORY,
        recommended_vehicles=SAMPLE_VEHICLES[:3]
    )
