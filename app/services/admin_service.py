"""
Rydeon - Administrative Operations Service Layer
------------------------------------------------
Provides database services for admin dashboard metrics, vehicle fleet CRUD,
booking approvals, document verification audits, and vehicle returns.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
import os
import time
from werkzeug.utils import secure_filename
from flask import current_app
from app.database.db import execute_query, get_db_cursor
from app.services.booking_service import check_vehicle_overlap

ALLOWED_VEHICLE_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_VEHICLE_IMG_SIZE = 8 * 1024 * 1024  # 8 MB

def get_admin_dashboard_metrics():
    """Calculates all administrative statistics directly from MySQL."""
    # Vehicles breakdown
    v_metrics = execute_query("""
        SELECT 
            COUNT(*) AS total_vehicles,
            COUNT(CASE WHEN status = 'available' THEN 1 END) AS available_vehicles,
            COUNT(CASE WHEN status = 'rented' THEN 1 END) AS rented_vehicles,
            COUNT(CASE WHEN status = 'maintenance' THEN 1 END) AS maintenance_vehicles
        FROM vehicles
    """, fetch_one=True) or {}

    # Customers count
    c_metrics = execute_query("""
        SELECT COUNT(*) AS total_customers FROM users WHERE role = 'customer'
    """, fetch_one=True) or {}

    # Bookings breakdown & revenue
    b_metrics = execute_query("""
        SELECT 
            COUNT(*) AS total_bookings,
            COUNT(CASE WHEN booking_status = 'pending' THEN 1 END) AS pending_bookings,
            COUNT(CASE WHEN booking_status = 'confirmed' THEN 1 END) AS active_rentals,
            COUNT(CASE WHEN booking_status = 'completed' THEN 1 END) AS completed_rentals,
            COUNT(CASE WHEN booking_status = 'cancelled' THEN 1 END) AS cancelled_bookings,
            COALESCE(SUM(CASE WHEN booking_status IN ('confirmed', 'completed') THEN total_amount ELSE 0 END), 0) AS gross_revenue
        FROM bookings
    """, fetch_one=True) or {}

    # Pending documents count
    d_metrics = execute_query("""
        SELECT COUNT(*) AS pending_documents FROM documents WHERE verification_status = 'pending'
    """, fetch_one=True) or {}

    return {
        "total_vehicles": v_metrics.get('total_vehicles', 0),
        "available_vehicles": v_metrics.get('available_vehicles', 0),
        "rented_vehicles": v_metrics.get('rented_vehicles', 0),
        "maintenance_vehicles": v_metrics.get('maintenance_vehicles', 0),
        "total_customers": c_metrics.get('total_customers', 0),
        "total_bookings": b_metrics.get('total_bookings', 0),
        "pending_bookings": b_metrics.get('pending_bookings', 0),
        "active_rentals": b_metrics.get('active_rentals', 0),
        "completed_rentals": b_metrics.get('completed_rentals', 0),
        "cancelled_bookings": b_metrics.get('cancelled_bookings', 0),
        "gross_revenue": float(b_metrics.get('gross_revenue', 0)),
        "pending_documents": d_metrics.get('pending_documents', 0)
    }

# ==============================================================================
# VEHICLE FLEET MANAGEMENT (CRUD)
# ==============================================================================
def save_vehicle_image(file_storage):
    """Safely validates and stores an uploaded vehicle photograph."""
    if not file_storage or file_storage.filename == '':
        return None

    filename = file_storage.filename
    if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_VEHICLE_IMG_EXTENSIONS:
        raise ValueError("Invalid image format. Allowed: PNG, JPG, JPEG, WEBP.")

    base_upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads') if current_app else 'uploads'
    veh_dir = os.path.join(base_upload_dir, 'vehicles')
    os.makedirs(veh_dir, exist_ok=True)

    ext = filename.rsplit('.', 1)[1].lower()
    clean_name = secure_filename(filename.rsplit('.', 1)[0])[:25]
    unique_name = f"veh_{clean_name}_{int(time.time())}.{ext}"
    relative_path = os.path.join('uploads', 'vehicles', unique_name).replace('\\', '/')
    abs_dest = os.path.join(veh_dir, unique_name)

    file_storage.save(abs_dest)
    # Prefix with leading slash for web serving
    return f"/{relative_path}"

def add_vehicle(name, brand, category, registration_number, seating_capacity,
                fuel_type, transmission, price_per_day, description, status='available',
                image_file=None, image_url=None):
    """Adds a new vehicle to the fleet with validation and duplicate registration prevention."""
    clean_reg = registration_number.strip().upper()
    if not clean_reg:
        raise ValueError("Registration number is mandatory.")

    existing = execute_query("SELECT id FROM vehicles WHERE registration_number = %s", (clean_reg,), fetch_one=True)
    if existing:
        raise ValueError(f"Vehicle with registration number '{clean_reg}' already exists in fleet.")

    if not name or not brand or not category:
        raise ValueError("Vehicle name, brand, and category are required fields.")

    try:
        price = float(price_per_day)
        if price <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Daily rental price must be a positive monetary value.")

    try:
        seats = int(seating_capacity)
        if seats < 1:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Seating capacity must be at least 1.")

    if status not in ('available', 'rented', 'maintenance'):
        status = 'available'

    # Determine image path
    final_image = image_url or "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1000&q=80"
    if image_file and image_file.filename:
        saved_img = save_vehicle_image(image_file)
        if saved_img:
            final_image = saved_img

    sql = """
        INSERT INTO vehicles (
            name, brand, category, registration_number, seating_capacity,
            fuel_type, transmission, price_per_day, image, description, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    res = execute_query(sql, (
        name.strip(), brand.strip(), category.strip(), clean_reg,
        seats, fuel_type.strip(), transmission.strip(), price,
        final_image, description.strip() if description else '', status
    ), commit=True)

    return res['lastrowid']

def update_vehicle(vehicle_id, name, brand, category, registration_number, seating_capacity,
                   fuel_type, transmission, price_per_day, description, status,
                   image_file=None, image_url=None):
    """Updates an existing vehicle record with uniqueness validation."""
    clean_reg = registration_number.strip().upper()

    existing = execute_query("SELECT id FROM vehicles WHERE registration_number = %s AND id != %s", (clean_reg, vehicle_id), fetch_one=True)
    if existing:
        raise ValueError(f"Registration number '{clean_reg}' is already assigned to vehicle #{existing['id']}.")

    try:
        price = float(price_per_day)
        if price <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Price per day must be a positive number.")

    try:
        seats = int(seating_capacity)
        if seats < 1:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Seating capacity must be at least 1.")

    # Image handling: keep current unless a new file or URL is provided
    current_veh = execute_query("SELECT image FROM vehicles WHERE id = %s", (vehicle_id,), fetch_one=True)
    final_image = current_veh['image'] if current_veh else ''

    if image_file and image_file.filename:
        saved_img = save_vehicle_image(image_file)
        if saved_img:
            final_image = saved_img
    elif image_url and image_url.strip():
        final_image = image_url.strip()

    sql = """
        UPDATE vehicles 
        SET name = %s, brand = %s, category = %s, registration_number = %s,
            seating_capacity = %s, fuel_type = %s, transmission = %s,
            price_per_day = %s, image = %s, description = %s, status = %s
        WHERE id = %s
    """
    execute_query(sql, (
        name.strip(), brand.strip(), category.strip(), clean_reg,
        seats, fuel_type.strip(), transmission.strip(),
        price, final_image, description.strip() if description else '', status, vehicle_id
    ), commit=True)
    return True

def delete_vehicle(vehicle_id):
    """
    Deletes a vehicle only when it has NO dependent booking records.
    Prevents foreign key integrity corruption.
    """
    bookings_count = execute_query("""
        SELECT COUNT(*) AS total FROM bookings WHERE vehicle_id = %s
    """, (vehicle_id,), fetch_one=True)

    if bookings_count and bookings_count['total'] > 0:
        raise ValueError(
            f"Cannot delete vehicle #{vehicle_id}: It has {bookings_count['total']} associated booking record(s). "
            f"To disable reservations without deleting historical records, set its status to 'maintenance'."
        )

    execute_query("DELETE FROM vehicles WHERE id = %s", (vehicle_id,), commit=True)
    return True

def update_vehicle_status(vehicle_id, new_status):
    """Quickly toggles a vehicle status between available, rented, maintenance."""
    if new_status not in ('available', 'rented', 'maintenance'):
        raise ValueError("Invalid status option.")
    execute_query("UPDATE vehicles SET status = %s WHERE id = %s", (new_status, vehicle_id), commit=True)
    return True

# ==============================================================================
# BOOKING MANAGEMENT & CONFLICT-AWARE APPROVALS
# ==============================================================================
def get_all_bookings_admin(search=None, status=None):
    """Retrieves all reservations with customer, vehicle, and payment details."""
    sql = """
        SELECT b.id, b.booking_reference, b.start_date, b.end_date, b.total_days, 
               b.total_amount, b.booking_status, b.payment_status, b.created_at,
               u.id AS customer_id, u.full_name AS customer_name, u.email AS customer_email, u.phone AS customer_phone,
               v.id AS vehicle_id, v.name AS vehicle_name, v.category AS vehicle_category, v.registration_number,
               p.transaction_reference, p.payment_method
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN vehicles v ON b.vehicle_id = v.id
        LEFT JOIN payments p ON b.id = p.booking_id
        WHERE 1=1
    """
    params = []

    if status and status != 'all':
        sql += " AND b.booking_status = %s"
        params.append(status)

    if search:
        wildcard = f"%{search.strip().lower()}%"
        sql += """ AND (
            LOWER(b.booking_reference) LIKE %s 
            OR LOWER(u.full_name) LIKE %s 
            OR LOWER(u.email) LIKE %s 
            OR LOWER(v.name) LIKE %s 
            OR LOWER(v.registration_number) LIKE %s
        )"""
        params.extend([wildcard, wildcard, wildcard, wildcard, wildcard])

    sql += " ORDER BY b.created_at DESC"
    return execute_query(sql, tuple(params), fetch_all=True) or []

def update_booking_status_admin(booking_id, new_status):
    """
    Updates booking status.
    If approving to 'confirmed', validates that vehicle has no overlapping active bookings!
    """
    if new_status not in ('pending', 'confirmed', 'completed', 'cancelled'):
        raise ValueError(f"Invalid booking status '{new_status}'.")

    booking = execute_query("SELECT id, vehicle_id, start_date, end_date, booking_status FROM bookings WHERE id = %s", (booking_id,), fetch_one=True)
    if not booking:
        raise ValueError("Booking record not found.")

    if new_status == 'confirmed':
        # Prevent conflicting approvals
        is_free, reason = check_vehicle_overlap(
            booking['vehicle_id'],
            booking['start_date'],
            booking['end_date'],
            exclude_booking_id=booking_id
        )
        if not is_free:
            raise ValueError(f"Conflicting Approval Error: {reason}")

    with get_db_cursor(commit=True) as (conn, cursor):
        cursor.execute("UPDATE bookings SET booking_status = %s WHERE id = %s", (new_status, booking_id))
        if new_status == 'cancelled':
            cursor.execute("UPDATE payments SET payment_status = 'refunded' WHERE booking_id = %s", (booking_id,))
        elif new_status == 'confirmed':
            cursor.execute("UPDATE payments SET payment_status = 'completed' WHERE booking_id = %s", (booking_id,))

    return True

# ==============================================================================
# DOCUMENT VERIFICATION MANAGEMENT
# ==============================================================================
def get_all_documents_admin(status=None):
    """Retrieves all customer identification documents."""
    sql = """
        SELECT d.id, d.user_id, d.booking_id, d.document_type, d.file_path, 
               d.verification_status, d.remarks, d.uploaded_at,
               u.full_name AS customer_name, u.email AS customer_email,
               b.booking_reference, v.name AS vehicle_name
        FROM documents d
        JOIN users u ON d.user_id = u.id
        LEFT JOIN bookings b ON d.booking_id = b.id
        LEFT JOIN vehicles v ON b.vehicle_id = v.id
        WHERE 1=1
    """
    params = []
    if status and status != 'all':
        sql += " AND d.verification_status = %s"
        params.append(status)

    sql += " ORDER BY d.uploaded_at DESC"
    return execute_query(sql, tuple(params), fetch_all=True) or []

def verify_document_admin(document_id, new_status, remarks=None):
    """Approves or rejects a customer document and records review remarks."""
    if new_status not in ('verified', 'rejected', 'pending'):
        raise ValueError(f"Invalid verification status '{new_status}'.")

    sql = """
        UPDATE documents 
        SET verification_status = %s, remarks = %s
        WHERE id = %s
    """
    execute_query(sql, (new_status, remarks.strip() if remarks else '', document_id), commit=True)
    return True

# ==============================================================================
# VEHICLE RETURN PROCESSING & LATE FEE ENGINE
# ==============================================================================
def get_active_bookings_for_return():
    """Finds all confirmed active reservations eligible for vehicle return processing."""
    sql = """
        SELECT b.id, b.booking_reference, b.start_date, b.end_date, b.total_days, 
               b.total_amount, b.booking_status,
               u.full_name AS customer_name, u.email AS customer_email,
               v.id AS vehicle_id, v.name AS vehicle_name, v.registration_number, v.price_per_day
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.booking_status = 'confirmed'
        ORDER BY b.end_date ASC
    """
    return execute_query(sql, fetch_all=True) or []

def process_vehicle_return(booking_id, actual_return_dt_val, vehicle_condition, manual_charges=0.0, remarks=None):
    """
    Records vehicle return, calculates late charges automatically,
    marks booking 'completed', and frees up vehicle status to 'available'.
    """
    booking = execute_query("""
        SELECT b.id, b.vehicle_id, b.end_date, b.booking_status, v.price_per_day, v.name AS vehicle_name
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.id = %s
    """, (booking_id,), fetch_one=True)

    if not booking:
        raise ValueError("Booking record not found.")

    if booking['booking_status'] != 'confirmed':
        raise ValueError(f"Cannot process return for booking with status '{booking['booking_status']}'. Only 'confirmed' rentals can be returned.")

    if isinstance(actual_return_dt_val, str):
        # Parse datetime string e.g. "2026-11-18T14:30" or "%Y-%m-%d %H:%M:%S"
        clean_dt = actual_return_dt_val.replace('T', ' ')
        try:
            actual_dt = datetime.strptime(clean_dt[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            actual_dt = datetime.strptime(clean_dt[:16], "%Y-%m-%d %H:%M")
    elif isinstance(actual_return_dt_val, datetime):
        actual_dt = actual_return_dt_val
    else:
        actual_dt = datetime.now()

    # 1. Automatic Late Return Fee Computation
    scheduled_end = booking['end_date']
    daily_rate = float(booking['price_per_day'])
    late_fee = 0.0

    if actual_dt.date() > scheduled_end:
        overdue_days = (actual_dt.date() - scheduled_end).days
        # Late fee policy: 1.5x daily rental rate for each overdue day
        late_fee = overdue_days * daily_rate * 1.5

    try:
        extra_charges = float(manual_charges or 0.0)
    except (ValueError, TypeError):
        extra_charges = 0.0

    total_additional_charges = late_fee + extra_charges

    # 2. Store Return record and update booking + vehicle in a transaction
    with get_db_cursor(commit=True) as (conn, cursor):
        cursor.execute("""
            INSERT INTO returns (booking_id, actual_return_date, additional_charges, vehicle_condition, remarks)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                actual_return_date = VALUES(actual_return_date),
                additional_charges = VALUES(additional_charges),
                vehicle_condition = VALUES(vehicle_condition),
                remarks = VALUES(remarks)
        """, (booking_id, actual_dt, total_additional_charges, vehicle_condition.strip(), remarks.strip() if remarks else ''))

        cursor.execute("UPDATE bookings SET booking_status = 'completed' WHERE id = %s", (booking_id,))
        cursor.execute("UPDATE vehicles SET status = 'available' WHERE id = %s", (booking['vehicle_id'],))

    return {
        "booking_id": booking_id,
        "vehicle_name": booking['vehicle_name'],
        "actual_return_date": actual_dt,
        "late_fee": late_fee,
        "manual_charges": extra_charges,
        "total_additional_charges": total_additional_charges,
        "vehicle_condition": vehicle_condition
    }
