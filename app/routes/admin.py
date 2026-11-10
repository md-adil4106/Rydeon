"""
Rydeon - Administrative Operations Blueprint
--------------------------------------------
Provides role-protected endpoints for fleet administration, reservation
auditing, and customer overview. Accessible strictly to 'admin' role.
"""

from flask import Blueprint, render_template
from app.services.decorators import admin_required
from app.database.db import execute_query

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Administrative Fleet & Operations Dashboard."""
    # 1. Fleet statistics
    fleet_stats = execute_query("""
        SELECT 
            COUNT(*) AS total_vehicles,
            COUNT(CASE WHEN status = 'available' THEN 1 END) AS available_count,
            COUNT(CASE WHEN status = 'rented' THEN 1 END) AS rented_count,
            COUNT(CASE WHEN status = 'maintenance' THEN 1 END) AS maintenance_count
        FROM vehicles
    """, fetch_one=True) or {}

    # 2. Customer statistics
    customer_stats = execute_query("""
        SELECT COUNT(*) AS total_customers FROM users WHERE role = 'customer'
    """, fetch_one=True) or {}

    # 3. Booking & Revenue statistics
    booking_stats = execute_query("""
        SELECT 
            COUNT(*) AS total_bookings,
            COUNT(CASE WHEN booking_status = 'confirmed' THEN 1 END) AS active_bookings,
            COALESCE(SUM(total_amount), 0) AS gross_revenue
        FROM bookings
    """, fetch_one=True) or {}

    # 4. Recent bookings list
    recent_bookings = execute_query("""
        SELECT b.id, b.start_date, b.end_date, b.total_days, b.total_amount, 
               b.booking_status, b.payment_status,
               u.full_name AS customer_name, u.email AS customer_email,
               v.name AS vehicle_name, v.registration_number
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN vehicles v ON b.vehicle_id = v.id
        ORDER BY b.created_at DESC
        LIMIT 10
    """, fetch_all=True) or []

    # 5. Full fleet overview
    fleet = execute_query("""
        SELECT id, name, brand, category, registration_number, seating_capacity,
               fuel_type, price_per_day, status
        FROM vehicles
        ORDER BY id ASC
    """, fetch_all=True) or []

    return render_template(
        'admin/dashboard.html',
        fleet_stats=fleet_stats,
        customer_count=customer_stats.get('total_customers', 0),
        booking_stats=booking_stats,
        recent_bookings=recent_bookings,
        fleet=fleet
    )
