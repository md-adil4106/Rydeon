"""
Rydeon - Booking Service Layer
------------------------------
Handles customer booking retrieval, joins with vehicles and payments,
and statistics calculations using MySQL parameterized queries.
"""

from app.database.db import execute_query

def get_user_active_booking(user_id):
    """
    Retrieves the customer's current confirmed or pending booking from MySQL,
    joining vehicle specifications and payment data.
    """
    sql = """
        SELECT b.id AS booking_id, b.start_date, b.end_date, b.total_days, 
               b.total_amount, b.booking_status, b.payment_status,
               v.name AS vehicle_name, v.category AS vehicle_category, v.brand AS vehicle_brand,
               v.image AS image_url, v.price_per_day AS daily_rate, v.registration_number,
               p.transaction_reference, p.payment_method
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        LEFT JOIN payments p ON b.id = p.booking_id
        WHERE b.user_id = %s AND b.booking_status IN ('confirmed', 'pending')
        ORDER BY b.start_date ASC
        LIMIT 1
    """
    return execute_query(sql, (user_id,), fetch_one=True)

def get_user_booking_history(user_id):
    """
    Retrieves all past completed or cancelled bookings for a customer,
    including return inspection records and payment references.
    """
    sql = """
        SELECT b.id AS booking_id, b.start_date, b.end_date, b.total_days, 
               b.total_amount, b.booking_status, b.payment_status,
               v.name AS vehicle_name, v.category AS vehicle_category, v.registration_number,
               r.actual_return_date, r.vehicle_condition, r.remarks,
               p.transaction_reference
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        LEFT JOIN returns r ON b.id = r.booking_id
        LEFT JOIN payments p ON b.id = p.booking_id
        WHERE b.user_id = %s AND b.booking_status IN ('completed', 'cancelled')
        ORDER BY b.end_date DESC
    """
    return execute_query(sql, (user_id,), fetch_all=True)

def get_user_stats(user_id):
    """Calculates active rentals, completed trips, and stats directly from MySQL."""
    sql = """
        SELECT 
            COUNT(CASE WHEN booking_status IN ('confirmed', 'pending') THEN 1 END) AS active_rentals,
            COUNT(CASE WHEN booking_status = 'completed' THEN 1 END) AS completed_rentals,
            COALESCE(SUM(CASE WHEN booking_status = 'completed' THEN total_days * 120 ELSE 0 END), 0) AS estimated_miles
        FROM bookings
        WHERE user_id = %s
    """
    stats = execute_query(sql, (user_id,), fetch_one=True)
    if not stats:
        return {"active_rentals": 0, "completed_rentals": 0, "miles_driven": "0 mi", "reward_points": "0 pts"}

    completed = stats.get('completed_rentals', 0)
    return {
        "active_rentals": stats.get('active_rentals', 0),
        "completed_rentals": completed,
        "miles_driven": f"{stats.get('estimated_miles', 0):,} mi",
        "reward_points": f"{completed * 150:,} pts"
    }
