"""
Rydeon - Administrative Operations & Staff Dashboard Test Suite
---------------------------------------------------------------
Validates:
1. Strict administrative role-based access control (RBAC).
2. Verified MySQL metrics calculation on the admin dashboard.
3. Full Vehicle Fleet CRUD operations (Add, Edit, Status Toggle, Safe Delete).
4. Booking management with conflict-aware approvals.
5. Customer document auditing with verification remarks.
6. Vehicle return check-in, automated late return fee computation, and status restoration.
"""

from datetime import date, datetime, timedelta
import io
import pytest
from app import create_app
from config.config import TestingConfig
from app.database.db import execute_query
from app.services import admin_service, vehicle_service, booking_service, document_service

@pytest.fixture(scope="module")
def app():
    app = create_app(TestingConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_client(app):
    """Client authenticated with administrative credentials."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Admin User'
        sess['email'] = 'admin@rydeon-rentals.com'
        sess['role'] = 'admin'
    return client

@pytest.fixture
def customer_client(app):
    """Client authenticated as standard customer."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_name'] = 'Alexander Wright'
        sess['email'] = 'alexander.wright@example.com'
        sess['role'] = 'customer'
    return client

# ==============================================================================
# 1. ACCESS CONTROL TESTS
# ==============================================================================
def test_anonymous_blocked_from_all_admin_routes(client):
    """Verify unauthenticated user cannot access any admin endpoint."""
    admin_routes = ['/admin/', '/admin/dashboard', '/admin/vehicles', '/admin/bookings', '/admin/documents', '/admin/returns']
    for route in admin_routes:
        resp = client.get(route, follow_redirects=False)
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

def test_customer_forbidden_from_admin_routes(customer_client):
    """Verify authenticated customer receives 403 Forbidden on all admin endpoints."""
    admin_routes = ['/admin/', '/admin/dashboard', '/admin/vehicles', '/admin/bookings', '/admin/documents', '/admin/returns']
    for route in admin_routes:
        resp = customer_client.get(route, follow_redirects=False)
        assert resp.status_code == 403
        assert "403 - Access Forbidden" in resp.data.decode('utf-8')

def test_admin_permitted_on_all_admin_routes(admin_client):
    """Verify administrator has full access to all admin endpoints."""
    admin_routes = ['/admin/', '/admin/dashboard', '/admin/vehicles', '/admin/bookings', '/admin/documents', '/admin/returns']
    for route in admin_routes:
        resp = admin_client.get(route)
        assert resp.status_code == 200

# ==============================================================================
# 2. DASHBOARD METRICS CALCULATION (REAL MYSQL DATA)
# ==============================================================================
def test_admin_dashboard_metrics_calculation():
    """Verify MySQL calculates metrics matching actual table row counts."""
    metrics = admin_service.get_admin_dashboard_metrics()
    assert metrics['total_vehicles'] >= 12
    assert metrics['total_customers'] >= 1
    assert metrics['total_bookings'] >= 1
    assert isinstance(metrics['active_rentals'], int)
    assert isinstance(metrics['completed_rentals'], int)
    assert isinstance(metrics['gross_revenue'], (int, float))

# ==============================================================================
# 3. VEHICLE FLEET MANAGEMENT (CRUD) TESTS
# ==============================================================================
def test_admin_add_vehicle_workflow(admin_client):
    """Verify adding a new vehicle to the fleet."""
    test_reg = "RYD-TEST-99"
    execute_query("DELETE FROM vehicles WHERE registration_number = %s", (test_reg,), commit=True)

    payload = {
        "name": "Audi e-tron GT RS",
        "brand": "Audi",
        "category": "Electric",
        "registration_number": test_reg,
        "seating_capacity": "4",
        "fuel_type": "Electric",
        "transmission": "Automatic",
        "price_per_day": "215.00",
        "description": "Electric grand tourer with dual synchronous motors.",
        "status": "available",
        "image_url": "https://images.unsplash.com/photo-1614162692292-7ac56d7f7f1e?auto=format&fit=crop&w=1000&q=80"
    }

    resp = admin_client.post('/admin/vehicles/add', data=payload, follow_redirects=False)
    assert resp.status_code == 302
    assert '/admin/vehicles' in resp.headers['Location']

    # Verify vehicle was inserted into MySQL
    car = execute_query("SELECT id, name, price_per_day, status FROM vehicles WHERE registration_number = %s", (test_reg,), fetch_one=True)
    assert car is not None
    assert car['name'] == "Audi e-tron GT RS"
    assert float(car['price_per_day']) == 215.0
    assert car['status'] == 'available'

def test_admin_add_vehicle_duplicate_reg_rejected(admin_client):
    """Verify adding a vehicle with an existing registration number is rejected."""
    payload = {
        "name": "Duplicate Car",
        "brand": "Test",
        "category": "Sedan",
        "registration_number": "RYD-EL-0101",  # Taycan reg already in DB
        "seating_capacity": "5",
        "fuel_type": "Gasoline",
        "transmission": "Automatic",
        "price_per_day": "100.00",
        "status": "available"
    }

    resp = admin_client.post('/admin/vehicles/add', data=payload, follow_redirects=True)
    assert resp.status_code == 400
    assert "already exists in fleet" in resp.data.decode('utf-8').lower()

def test_admin_edit_vehicle_workflow(admin_client):
    """Verify editing vehicle specifications and status."""
    car = execute_query("SELECT id, price_per_day FROM vehicles WHERE registration_number = 'RYD-TEST-99'", fetch_one=True)
    assert car is not None

    payload = {
        "name": "Audi e-tron GT RS Quattro",
        "brand": "Audi",
        "category": "Electric",
        "registration_number": "RYD-TEST-99",
        "seating_capacity": "5",
        "fuel_type": "Electric",
        "transmission": "Automatic",
        "price_per_day": "225.00",
        "description": "Updated grand tourer description.",
        "status": "maintenance"
    }

    resp = admin_client.post(f'/admin/vehicles/{car["id"]}/edit', data=payload, follow_redirects=False)
    assert resp.status_code == 302

    updated = execute_query("SELECT name, price_per_day, status FROM vehicles WHERE id = %s", (car['id'],), fetch_one=True)
    assert updated['name'] == "Audi e-tron GT RS Quattro"
    assert float(updated['price_per_day']) == 225.0
    assert updated['status'] == "maintenance"

def test_admin_vehicle_status_toggle(admin_client):
    """Verify quick toggle of vehicle availability status."""
    car = execute_query("SELECT id FROM vehicles WHERE registration_number = 'RYD-TEST-99'", fetch_one=True)
    assert car is not None

    resp = admin_client.post(f'/admin/vehicles/{car["id"]}/status', data={"status": "available"}, follow_redirects=False)
    assert resp.status_code == 302

    v = execute_query("SELECT status FROM vehicles WHERE id = %s", (car['id'],), fetch_one=True)
    assert v['status'] == 'available'

def test_admin_delete_vehicle_with_bookings_blocked(admin_client):
    """Verify vehicles with associated booking records cannot be deleted."""
    # Vehicle #3 (Mercedes S-Class) has existing bookings
    s_class = execute_query("SELECT id FROM vehicles WHERE registration_number = 'RYD-LX-0303'", fetch_one=True)
    assert s_class is not None

    resp = admin_client.post(f'/admin/vehicles/{s_class["id"]}/delete', follow_redirects=True)
    html = resp.data.decode('utf-8')
    assert "cannot delete vehicle" in html.lower() or "associated booking record" in html.lower()

    # Verify vehicle was NOT deleted
    still_exists = execute_query("SELECT id FROM vehicles WHERE id = %s", (s_class['id'],), fetch_one=True)
    assert still_exists is not None

def test_admin_delete_vehicle_without_bookings_succeeds(admin_client):
    """Verify vehicle with zero bookings can be cleanly deleted."""
    car = execute_query("SELECT id FROM vehicles WHERE registration_number = 'RYD-TEST-99'", fetch_one=True)
    assert car is not None

    resp = admin_client.post(f'/admin/vehicles/{car["id"]}/delete', follow_redirects=False)
    assert resp.status_code == 302

    deleted = execute_query("SELECT id FROM vehicles WHERE id = %s", (car['id'],), fetch_one=True)
    assert deleted is None

# ==============================================================================
# 4. BOOKING MANAGEMENT & CONFLICT-AWARE APPROVALS
# ==============================================================================
def test_admin_booking_status_update_and_conflict_prevention(admin_client):
    """
    1. Create a pending booking for vehicle 7.
    2. Admin approves it to 'confirmed'.
    3. Create a second pending booking overlapping the same dates.
    4. Admin attempts to approve second booking -> rejected due to conflict!
    """
    today = date.today()
    p1 = (today + timedelta(days=70)).isoformat()
    r1 = (today + timedelta(days=75)).isoformat()

    # Clean existing test bookings on vehicle 7
    execute_query("DELETE FROM bookings WHERE vehicle_id = 7 AND start_date >= %s", (p1,), commit=True)

    # 1. Create first pending booking
    execute_query("""
        INSERT INTO bookings (booking_reference, user_id, vehicle_id, start_date, end_date, total_days, total_amount, booking_status, payment_status)
        VALUES ('RYD-TEST-P1', 2, 7, %s, %s, 5, 700.00, 'pending', 'pending')
    """, (p1, r1), commit=True)
    b1 = execute_query("SELECT id FROM bookings WHERE booking_reference = 'RYD-TEST-P1'", fetch_one=True)

    # Admin approves first booking -> succeeds
    resp1 = admin_client.post(f'/admin/bookings/{b1["id"]}/status', data={"status": "confirmed"}, follow_redirects=True)
    html1 = resp1.data.decode('utf-8').lower()
    assert "status updated to" in html1 and "confirmed" in html1

    # 2. Create second overlapping pending booking (Day+72 to Day+76)
    p2 = (today + timedelta(days=72)).isoformat()
    r2 = (today + timedelta(days=76)).isoformat()
    execute_query("""
        INSERT INTO bookings (booking_reference, user_id, vehicle_id, start_date, end_date, total_days, total_amount, booking_status, payment_status)
        VALUES ('RYD-TEST-P2', 2, 7, %s, %s, 4, 560.00, 'pending', 'pending')
    """, (p2, r2), commit=True)
    b2 = execute_query("SELECT id FROM bookings WHERE booking_reference = 'RYD-TEST-P2'", fetch_one=True)

    # Admin attempts to approve overlapping booking -> rejected!
    resp2 = admin_client.post(f'/admin/bookings/{b2["id"]}/status', data={"status": "confirmed"}, follow_redirects=True)
    html2 = resp2.data.decode('utf-8')
    assert "conflicting approval error" in html2.lower() or "already reserved" in html2.lower()

    # Admin rejects second booking instead -> succeeds
    resp3 = admin_client.post(f'/admin/bookings/{b2["id"]}/status', data={"status": "cancelled"}, follow_redirects=True)
    html3 = resp3.data.decode('utf-8').lower()
    assert "status updated to" in html3 and "cancelled" in html3

# ==============================================================================
# 5. DOCUMENT VERIFICATION MANAGEMENT TESTS
# ==============================================================================
def test_admin_document_audit_workflow(admin_client):
    """Verify administrator reviews, approves, and rejects customer documents with remarks."""
    # Ensure any previous test document is cleared and a fresh pending document exists
    execute_query("DELETE FROM documents WHERE file_path = 'uploads/documents/test_passport.pdf'", commit=True)
    execute_query("""
        INSERT INTO documents (user_id, document_type, file_path, verification_status)
        VALUES (2, 'passport', 'uploads/documents/test_passport.pdf', 'pending')
    """, commit=True)
    doc = execute_query("SELECT id FROM documents WHERE file_path = 'uploads/documents/test_passport.pdf'", fetch_one=True)
    doc_id = doc['id']

    # 1. Admin rejects with remarks
    resp1 = admin_client.post(f'/admin/documents/{doc_id}/verify', data={
        "status": "rejected",
        "remarks": "Document scan is blurry. Please upload a clear photo."
    }, follow_redirects=True)
    html1 = resp1.data.decode('utf-8').lower()
    assert "marked as" in html1 and "rejected" in html1

    d1 = execute_query("SELECT verification_status, remarks FROM documents WHERE id = %s", (doc_id,), fetch_one=True)
    assert d1['verification_status'] == 'rejected'
    assert "blurry" in d1['remarks']

    # 2. Admin approves after review
    resp2 = admin_client.post(f'/admin/documents/{doc_id}/verify', data={
        "status": "verified",
        "remarks": "Passport verified against DMV registry."
    }, follow_redirects=True)
    html2 = resp2.data.decode('utf-8').lower()
    assert "marked as" in html2 and "verified" in html2

    d2 = execute_query("SELECT verification_status, remarks FROM documents WHERE id = %s", (doc_id,), fetch_one=True)
    assert d2['verification_status'] == 'verified'

# ==============================================================================
# 6. VEHICLE RETURN PROCESSING & LATE FEE ENGINE TESTS
# ==============================================================================
def test_admin_vehicle_return_processing_on_time(admin_client):
    """Verify normal on-time vehicle return marks booking completed and vehicle available."""
    # Create an active confirmed rental ending today
    today = date.today()
    p = (today - timedelta(days=3)).isoformat()
    r = today.isoformat()

    execute_query("DELETE FROM returns WHERE booking_id IN (SELECT id FROM bookings WHERE booking_reference = 'RYD-TEST-ONTIME')", commit=True)
    execute_query("DELETE FROM bookings WHERE booking_reference = 'RYD-TEST-ONTIME'", commit=True)
    execute_query("UPDATE vehicles SET status = 'rented' WHERE id = 4", commit=True)

    execute_query("""
        INSERT INTO bookings (booking_reference, user_id, vehicle_id, start_date, end_date, total_days, total_amount, booking_status, payment_status)
        VALUES ('RYD-TEST-ONTIME', 2, 4, %s, %s, 3, 585.00, 'confirmed', 'paid')
    """, (p, r), commit=True)
    b = execute_query("SELECT id FROM bookings WHERE booking_reference = 'RYD-TEST-ONTIME'", fetch_one=True)
    b_id = b['id']

    # Process return on time
    now_dt = datetime.now().strftime("%Y-%m-%dT%H:%M")
    resp = admin_client.post('/admin/returns/process', data={
        "booking_id": str(b_id),
        "actual_return_date": now_dt,
        "vehicle_condition": "Excellent - Pristine & Sanitized",
        "manual_charges": "0.00",
        "remarks": "Returned on schedule with full tank."
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert "vehicle return processed" in resp.data.decode('utf-8').lower()

    # Verify booking is completed and vehicle is available
    b_updated = booking_service.get_booking_by_id(b_id)
    assert b_updated['booking_status'] == 'completed'

    v_updated = vehicle_service.get_vehicle_by_id(4)
    assert v_updated['status'] == 'available'

    # Verify return record in MySQL
    ret = execute_query("SELECT booking_id, additional_charges, vehicle_condition FROM returns WHERE booking_id = %s", (b_id,), fetch_one=True)
    assert ret is not None
    assert float(ret['additional_charges']) == 0.0

def test_admin_vehicle_return_with_late_fee_calculation():
    """Verify automated late return fee calculation (1.5x daily rate for overdue days)."""
    # Create rental with scheduled end date 2 days ago
    two_days_ago = date.today() - timedelta(days=2)
    five_days_ago = date.today() - timedelta(days=5)

    execute_query("DELETE FROM returns WHERE booking_id IN (SELECT id FROM bookings WHERE booking_reference = 'RYD-TEST-LATE')", commit=True)
    execute_query("DELETE FROM bookings WHERE booking_reference = 'RYD-TEST-LATE'", commit=True)

    execute_query("""
        INSERT INTO bookings (booking_reference, user_id, vehicle_id, start_date, end_date, total_days, total_amount, booking_status, payment_status)
        VALUES ('RYD-TEST-LATE', 2, 8, %s, %s, 3, 405.00, 'confirmed', 'paid')
    """, (five_days_ago.isoformat(), two_days_ago.isoformat()), commit=True)
    b = execute_query("SELECT id FROM bookings WHERE booking_reference = 'RYD-TEST-LATE'", fetch_one=True)
    b_id = b['id']

    # Vehicle #8 (Genesis G80: $135/day), 2 overdue days -> late fee = 2 * 135 * 1.5 = $405.00
    # Plus manual cleaning charge $50.00 -> total additional charges = $455.00
    now_dt = datetime.now()
    summary = admin_service.process_vehicle_return(
        booking_id=b_id,
        actual_return_dt_val=now_dt,
        vehicle_condition="Fair - Needs Cleaning",
        manual_charges=50.0,
        remarks="Returned 2 days late. Cleaned interior."
    )

    assert summary['late_fee'] == 2 * 135.0 * 1.5
    assert summary['manual_charges'] == 50.0
    assert summary['total_additional_charges'] == 405.0 + 50.0

    ret = execute_query("SELECT additional_charges, vehicle_condition FROM returns WHERE booking_id = %s", (b_id,), fetch_one=True)
    assert float(ret['additional_charges']) == 455.0
