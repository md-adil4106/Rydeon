"""
Rydeon - Customer Booking & Reservation Service Layer
-----------------------------------------------------
Handles date validation, overlap prevention, concurrency row locking,
automatic price calculation, transaction management, and reservation cancellations.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
import secrets
from app.database.db import get_db_cursor, execute_query
from app.services.document_service import validate_and_save_document

def generate_unique_booking_reference():
    """Generates an executive booking reference format: RYD-YYYY-XXXXXX."""
    year = date.today().year
    random_code = secrets.token_hex(3).upper()
    return f"RYD-{year}-{random_code}"

def generate_simulated_transaction_reference():
    """Generates a clearly identified simulated demo transaction reference."""
    year = date.today().year
    random_hex = secrets.token_hex(4).upper()
    return f"SIM-TXN-{year}-{random_hex}"

def parse_iso_date(date_val):
    """Safely converts string or date object into date."""
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, str):
        return datetime.strptime(date_val.strip(), "%Y-%m-%d").date()
    raise ValueError(f"Invalid date representation: {date_val}")

def check_vehicle_overlap(vehicle_id, start_date, end_date, exclude_booking_id=None, cursor=None):
    """
    Checks whether a vehicle has overlapping active or confirmed reservations.
    Returns (True, None) if vehicle is free, or (False, reason) if conflicted.
    """
    sql = """
        SELECT id, booking_reference, start_date, end_date
        FROM bookings
        WHERE vehicle_id = %s
          AND booking_status IN ('confirmed', 'pending')
          AND start_date < %s
          AND end_date > %s
    """
    params = [vehicle_id, end_date, start_date]

    if exclude_booking_id:
        sql += " AND id != %s"
        params.append(exclude_booking_id)

    if cursor:
        cursor.execute(sql, tuple(params))
        conflict = cursor.fetchone()
    else:
        conflict = execute_query(sql, tuple(params), fetch_one=True)

    if conflict:
        return False, f"Vehicle is already reserved from {conflict['start_date']} to {conflict['end_date']}."
    return True, None

def calculate_booking_quote(vehicle_id, start_date_val, end_date_val):
    """
    Backend price calculation engine.
    Never relies on frontend client numbers.
    """
    start_date = parse_iso_date(start_date_val)
    end_date = parse_iso_date(end_date_val)

    today = date.today()
    if start_date < today:
        raise ValueError("Pick-up date cannot be in the past.")

    if end_date <= start_date:
        raise ValueError("Return date must be strictly after the pick-up date.")

    total_days = (end_date - start_date).days
    if total_days < 1:
        raise ValueError("Minimum rental duration is 1 day.")

    vehicle = execute_query("SELECT id, name, price_per_day, status FROM vehicles WHERE id = %s", (vehicle_id,), fetch_one=True)
    if not vehicle:
        raise ValueError("Vehicle not found in catalog.")

    daily_rate = Decimal(str(vehicle['price_per_day']))
    total_amount = daily_rate * Decimal(total_days)

    return {
        "vehicle_id": vehicle['id'],
        "vehicle_name": vehicle['name'],
        "daily_rate": float(daily_rate),
        "start_date": start_date,
        "end_date": end_date,
        "total_days": total_days,
        "total_amount": float(total_amount)
    }

def create_customer_booking(user_id, vehicle_id, start_date_val, end_date_val, payment_method='Credit Card (Visa)', document_file=None):
    """
    Creates a confirmed booking with row-level transaction locking to guarantee
    zero race conditions or double bookings during simultaneous submissions.
    """
    start_date = parse_iso_date(start_date_val)
    end_date = parse_iso_date(end_date_val)

    today = date.today()
    if start_date < today:
        raise ValueError("Pick-up date cannot be in the past.")

    if end_date <= start_date:
        raise ValueError("Return date must be after pick-up date.")

    total_days = (end_date - start_date).days
    if total_days < 1:
        raise ValueError("Minimum rental duration is 1 day.")

    with get_db_cursor(commit=True) as (conn, cursor):
        # 1. Row-level pessimistic locking on vehicle
        cursor.execute("""
            SELECT id, name, price_per_day, status 
            FROM vehicles 
            WHERE id = %s 
            FOR UPDATE
        """, (vehicle_id,))
        vehicle = cursor.fetchone()

        if not vehicle:
            raise ValueError("Requested vehicle does not exist.")

        if vehicle['status'] == 'maintenance':
            raise ValueError("This vehicle is currently undergoing scheduled maintenance.")

        # 2. Check for date overlaps under lock
        cursor.execute("""
            SELECT id, booking_reference, start_date, end_date
            FROM bookings
            WHERE vehicle_id = %s
              AND booking_status IN ('confirmed', 'pending')
              AND start_date < %s
              AND end_date > %s
        """, (vehicle_id, end_date, start_date))
        overlap = cursor.fetchone()

        if overlap:
            raise ValueError(f"This vehicle is already reserved for {overlap['start_date']} to {overlap['end_date']}. Please choose alternative dates.")

        # 3. Calculate verified backend price
        daily_rate = Decimal(str(vehicle['price_per_day']))
        total_amount = daily_rate * Decimal(total_days)
        booking_ref = generate_unique_booking_reference()

        # 4. Insert booking record
        cursor.execute("""
            INSERT INTO bookings (
                booking_reference, user_id, vehicle_id, start_date, end_date,
                total_days, total_amount, booking_status, payment_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'confirmed', 'paid')
        """, (booking_ref, user_id, vehicle_id, start_date, end_date, total_days, total_amount))
        booking_id = cursor.lastrowid

        # 5. Insert payment record (Simulated Transaction)
        txn_ref = generate_simulated_transaction_reference()
        cursor.execute("""
            INSERT INTO payments (booking_id, amount, transaction_reference, payment_method, payment_status)
            VALUES (%s, %s, %s, %s, 'completed')
        """, (booking_id, total_amount, txn_ref, payment_method))

    # 6. Save document if uploaded with booking
    if document_file and document_file.filename:
        validate_and_save_document(user_id, booking_id, "drivers_license", document_file)

    return get_booking_by_id(booking_id, user_id=user_id)

def simulate_booking_payment(booking_id, user_id, payment_method, demo_meta=None):
    """
    Simulates a secure checkout payment transaction for an existing booking.
    Generates a unique simulation reference, updates MySQL payment & booking status consistently.
    """
    booking = get_booking_by_id(booking_id, user_id=user_id)
    if not booking:
        raise ValueError("Booking record not found or access denied.")

    if booking['payment_status'] == 'paid' and booking['booking_status'] == 'confirmed':
        return {
            "status": "already_paid",
            "booking": booking,
            "transaction_reference": booking.get('transaction_reference')
        }

    txn_ref = generate_simulated_transaction_reference()
    amount = Decimal(str(booking['total_amount']))

    with get_db_cursor(commit=True) as (conn, cursor):
        # Upsert payment record
        cursor.execute("""
            INSERT INTO payments (booking_id, amount, transaction_reference, payment_method, payment_status)
            VALUES (%s, %s, %s, %s, 'completed')
            ON DUPLICATE KEY UPDATE
                amount = VALUES(amount),
                transaction_reference = VALUES(transaction_reference),
                payment_method = VALUES(payment_method),
                payment_status = 'completed'
        """, (booking_id, amount, txn_ref, payment_method))

        # Update booking status to confirmed & paid
        cursor.execute("""
            UPDATE bookings 
            SET payment_status = 'paid',
                booking_status = CASE WHEN booking_status = 'cancelled' THEN 'cancelled' ELSE 'confirmed' END
            WHERE id = %s
        """, (booking_id,))

    updated = get_booking_by_id(booking_id, user_id=user_id)
    return {
        "status": "success",
        "booking": updated,
        "transaction_reference": txn_ref
    }

def get_booking_by_id(booking_id, user_id=None):
    """
    Retrieves full booking specifications joining vehicles, users, payments, and returns.
    Enforces customer privacy isolation when user_id is provided.
    """
    sql = """
        SELECT b.id AS booking_id, b.booking_reference, b.start_date, b.end_date,
               b.total_days, b.total_amount, b.booking_status, b.payment_status, b.created_at,
               v.id AS vehicle_id, v.name AS vehicle_name, v.brand AS vehicle_brand,
               v.category AS vehicle_category, v.registration_number, v.seating_capacity,
               v.fuel_type, v.transmission, v.price_per_day AS daily_rate, v.image AS image_url,
               u.id AS customer_id, u.full_name AS customer_name, u.email AS customer_email, u.phone AS customer_phone,
               p.transaction_reference, p.payment_method, p.payment_status AS txn_status, p.created_at AS payment_date,
               r.actual_return_date, r.additional_charges, r.vehicle_condition, r.remarks
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        JOIN users u ON b.user_id = u.id
        LEFT JOIN payments p ON b.id = p.booking_id
        LEFT JOIN returns r ON b.id = r.booking_id
        WHERE b.id = %s
    """
    params = [booking_id]
    if user_id:
        sql += " AND b.user_id = %s"
        params.append(user_id)

    return execute_query(sql, tuple(params), fetch_one=True)

def get_user_active_booking(user_id):
    """Retrieves current active confirmed booking for the customer dashboard."""
    sql = """
        SELECT b.id AS booking_id, b.booking_reference, b.start_date, b.end_date, b.total_days, 
               b.total_amount, b.booking_status, b.payment_status,
               v.id AS vehicle_id, v.name AS vehicle_name, v.category AS vehicle_category, v.brand AS vehicle_brand,
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

def get_user_upcoming_bookings(user_id):
    """Retrieves all upcoming active bookings for the customer."""
    sql = """
        SELECT b.id AS booking_id, b.booking_reference, b.start_date, b.end_date, b.total_days, 
               b.total_amount, b.booking_status, b.payment_status,
               v.id AS vehicle_id, v.name AS vehicle_name, v.category AS vehicle_category,
               v.image AS image_url, v.registration_number, v.price_per_day AS daily_rate,
               p.transaction_reference
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        LEFT JOIN payments p ON b.id = p.booking_id
        WHERE b.user_id = %s AND b.booking_status IN ('confirmed', 'pending')
        ORDER BY b.start_date ASC
    """
    return execute_query(sql, (user_id,), fetch_all=True) or []

def get_user_past_bookings(user_id):
    """Retrieves historical completed or cancelled bookings for the customer."""
    sql = """
        SELECT b.id AS booking_id, b.booking_reference, b.start_date, b.end_date, b.total_days, 
               b.total_amount, b.booking_status, b.payment_status,
               v.id AS vehicle_id, v.name AS vehicle_name, v.category AS vehicle_category,
               v.image AS image_url, v.registration_number, v.price_per_day AS daily_rate,
               p.transaction_reference, r.actual_return_date, r.vehicle_condition
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        LEFT JOIN payments p ON b.id = p.booking_id
        LEFT JOIN returns r ON b.id = r.booking_id
        WHERE b.user_id = %s AND b.booking_status IN ('completed', 'cancelled')
        ORDER BY b.end_date DESC
    """
    return execute_query(sql, (user_id,), fetch_all=True) or []

def get_user_booking_history(user_id):
    """Retrieves combined past booking records."""
    return get_user_past_bookings(user_id)

def cancel_customer_booking(booking_id, user_id):
    """
    Allows a customer to cancel their reservation only when permitted by status
    and project rules (confirmed/pending and pick-up date is at least tomorrow).
    """
    booking = get_booking_by_id(booking_id, user_id=user_id)
    if not booking:
        raise ValueError("Booking record not found or access denied.")

    if booking['booking_status'] not in ('confirmed', 'pending'):
        raise ValueError(f"Cannot cancel a booking with status '{booking['booking_status']}'.")

    # Check cancellation window: pick-up date must be in the future
    today = date.today()
    if booking['start_date'] <= today:
        raise ValueError("Bookings scheduled for today or in the past cannot be cancelled online. Please contact concierge.")

    with get_db_cursor(commit=True) as (conn, cursor):
        cursor.execute("""
            UPDATE bookings 
            SET booking_status = 'cancelled', payment_status = 'refunded'
            WHERE id = %s AND user_id = %s
        """, (booking_id, user_id))

        cursor.execute("""
            UPDATE payments 
            SET payment_status = 'refunded'
            WHERE booking_id = %s
        """, (booking_id,))

    return True

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
