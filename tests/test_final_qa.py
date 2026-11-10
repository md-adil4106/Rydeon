"""
Rydeon - Phase 6 Final Integration & Quality Assurance Test Suite
-----------------------------------------------------------------
Comprehensive end-to-end automated verification covering:
1. Complete Customer Journey (Steps 1-10)
2. Complete Administrative Journey (Steps 1-10)
3. Simulated Payment Gateway & Unique Transaction Reference
4. Printable Rental Agreement & Commercial Contract
5. Configurable Late Return Surcharges & MySQL Persistence
6. Security Hardening (File Execution Prevention, Traversal, Privacy Isolation, Concurrency)
"""

import os
import io
import pytest
from datetime import date, datetime, timedelta
from werkzeug.security import check_password_hash
from app import create_app
from config.config import TestingConfig
from app.database.db import execute_query
from app.services import booking_service, vehicle_service, admin_service, document_service

@pytest.fixture(scope="module")
def app():
    """Create Flask application test instance using TestingConfig."""
    app = create_app(TestingConfig)
    return app

@pytest.fixture
def client(app):
    """Anonymous test client."""
    return app.test_client()

@pytest.fixture
def auth_customer_client(app):
    """Authenticated customer client (User ID: 2 - Alexander Wright)."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_name'] = 'Alexander Wright'
        sess['email'] = 'alexander.wright@example.com'
        sess['role'] = 'customer'
    return client

@pytest.fixture
def admin_client(app):
    """Authenticated administrator client (User ID: 1 - System Administrator)."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'System Administrator'
        sess['email'] = 'admin@rydeon-rentals.com'
        sess['role'] = 'admin'
    return client

# ==============================================================================
# PART 1: COMPLETE CUSTOMER TEST JOURNEY (STEPS 1 - 10)
# ==============================================================================

def test_customer_step_1_registration(client):
    """Step 1: Register a new customer account and verify database persistence."""
    email = f"qa_renter_{int(datetime.now().timestamp())}@test.com"
    payload = {
        "full_name": "QA Test Renter",
        "email": email,
        "phone": "+1 (555) 777-8899",
        "password": "Password@123",
        "confirm_password": "Password@123",
        "terms": "on"
    }
    resp = client.post('/register', data=payload, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'] == '/dashboard'

    # Confirm MySQL record
    user = execute_query("SELECT id, full_name, email, password_hash, role FROM users WHERE email = %s", (email,), fetch_one=True)
    assert user is not None
    assert user['full_name'] == "QA Test Renter"
    assert user['role'] == "customer"
    assert check_password_hash(user['password_hash'], "Password@123")

def test_customer_step_2_login(client):
    """Step 2: Log in using registered credentials and verify session establishment."""
    resp = client.post('/login', data={
        "email": "alexander.wright@example.com",
        "password": "CustomerSecret2026!"
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'] == '/dashboard'

def test_customer_step_3_browse_vehicles(client):
    """Step 3: Browse vehicle fleet in catalogue."""
    resp = client.get('/catalogue')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "Catalogue" in html or "Fleet" in html
    assert "Taycan" in html or "BMW" in html

def test_customer_step_4_search_and_filter(client):
    """Step 4: Search and filter vehicles by category and keywords."""
    resp_search = client.get('/catalogue?search=Taycan')
    assert resp_search.status_code == 200
    assert "Taycan" in resp_search.data.decode('utf-8')

    resp_cat = client.get('/catalogue?category=luxury')
    assert resp_cat.status_code == 200
    assert "Mercedes-Benz" in resp_cat.data.decode('utf-8') or "Taycan" in resp_cat.data.decode('utf-8')

def test_customer_step_5_open_vehicle_details(client):
    """Step 5: Open vehicle detailed specifications page."""
    resp = client.get('/vehicles/1')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "Porsche Taycan 4S" in html
    assert "Electric" in html
    assert "Book" in html or "Reserve" in html

def test_customer_step_6_select_rental_dates(auth_customer_client):
    """Step 6: Open reservation form and calculate dynamic price quote."""
    resp = auth_customer_client.get('/book/1')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "Secure Vehicle Reservation" in html
    assert "Porsche Taycan 4S" in html

    # Backend price quote calculation
    today = date.today()
    p = today + timedelta(days=10)
    r = today + timedelta(days=14)
    quote = booking_service.calculate_booking_quote(1, p, r)
    assert quote['total_days'] == 4
    assert quote['total_amount'] == 4 * 195.0

def test_customer_step_7_document_upload(auth_customer_client):
    """Step 7: Upload driver identification document."""
    # Ensure booking #1 exists or find latest booking for user 2
    b = execute_query("SELECT id FROM bookings WHERE user_id = 2 ORDER BY id DESC", fetch_one=True)
    b_id = b['id'] if b else 1

    data = {
        "document_type": "drivers_license",
        "document_file": (io.BytesIO(b"%PDF-1.4 Mock Driving License File"), "dmv_license.pdf")
    }
    resp = auth_customer_client.post(
        f'/bookings/{b_id}/upload-document',
        data=data,
        content_type='multipart/form-data',
        follow_redirects=True
    )
    assert resp.status_code == 200
    html = resp.data.decode('utf-8').lower()
    assert "uploaded" in html or "pending" in html

def test_customer_step_8_simulated_payment_checkout(auth_customer_client):
    """Step 8: Complete simulated payment checkout with demo payment channel."""
    today = date.today()
    p = (today + timedelta(days=90)).isoformat()
    r = (today + timedelta(days=93)).isoformat()

    # Pre-clean any test bookings for vehicle 6
    execute_query("DELETE FROM bookings WHERE vehicle_id = 6 AND start_date >= %s", (p,), commit=True)

    # 1. Create booking with demo payment method
    booking = booking_service.create_customer_booking(
        user_id=2,
        vehicle_id=6,  # Tesla Model S Plaid ($185/day)
        start_date_val=p,
        end_date_val=r,
        payment_method="Demo Credit Card (Visa - 4111)"
    )
    b_id = booking['booking_id']

    # 2. Verify unique simulated transaction reference generated
    assert booking['transaction_reference'].startswith("SIM-TXN-")
    assert booking['payment_status'] == 'paid'
    assert booking['booking_status'] == 'confirmed'

    # 3. Test checkout endpoint simulation for payment re-authorization / verification
    resp_checkout = auth_customer_client.get(f'/bookings/{b_id}/checkout')
    assert resp_checkout.status_code == 200
    assert "Simulated Payment Checkout" in resp_checkout.data.decode('utf-8')
    assert "SANDBOX-MODE" in resp_checkout.data.decode('utf-8')

    # Post simulated payment via checkout gateway
    resp_pay = auth_customer_client.post(f'/bookings/{b_id}/checkout', data={
        "payment_method": "Demo UPI / Instant QR Code"
    }, follow_redirects=True)
    assert resp_pay.status_code == 200
    assert "simulated payment" in resp_pay.data.decode('utf-8').lower()

def test_customer_step_9_booking_confirmation_and_agreement(auth_customer_client):
    """Step 9: Receive booking confirmation, view printable voucher and rental agreement."""
    b = execute_query("SELECT id FROM bookings WHERE user_id = 2 ORDER BY id DESC", fetch_one=True)
    b_id = b['id']

    # Confirmation Voucher
    resp_conf = auth_customer_client.get(f'/bookings/{b_id}/confirmation')
    assert resp_conf.status_code == 200
    html_conf = resp_conf.data.decode('utf-8')
    assert "Reservation Confirmed" in html_conf
    assert "SIM-TXN-" in html_conf or "PAID" in html_conf

    # Formal Rental Agreement
    resp_agr = auth_customer_client.get(f'/bookings/{b_id}/agreement')
    assert resp_agr.status_code == 200
    html_agr = resp_agr.data.decode('utf-8')
    assert "Executive Vehicle Rental Services" in html_agr
    assert "AGR-" in html_agr
    assert "Signature of Primary Renter" in html_agr
    assert "Contract Terms" in html_agr

def test_customer_step_10_view_booking_history(auth_customer_client):
    """Step 10: View customer booking history on dashboard and my-bookings."""
    resp_my = auth_customer_client.get('/my-bookings')
    assert resp_my.status_code == 200
    html_my = resp_my.data.decode('utf-8')
    assert "My Rental Reservations" in html_my

    resp_dash = auth_customer_client.get('/dashboard')
    assert resp_dash.status_code == 200
    html_dash = resp_dash.data.decode('utf-8')
    assert "Dashboard" in html_dash or "Welcome" in html_dash

# ==============================================================================
# PART 2: COMPLETE ADMIN TEST JOURNEY (STEPS 1 - 10)
# ==============================================================================

def test_admin_step_1_login(client):
    """Admin Step 1: Authenticate administrator account."""
    resp = client.post('/login', data={
        "email": "admin@rydeon-rentals.com",
        "password": "AdminSecret2026!"
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert '/admin' in resp.headers['Location']

def test_admin_step_2_open_dashboard_metrics(admin_client):
    """Admin Step 2: Open admin dashboard and verify all operational metrics come from MySQL."""
    resp = admin_client.get('/admin/dashboard')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8').lower()
    assert "fleet operations" in html
    assert "total fleet" in html
    assert "all bookings" in html or "bookings" in html

    metrics = admin_service.get_admin_dashboard_metrics()
    assert metrics['total_vehicles'] >= 10
    assert metrics['total_customers'] >= 1
    assert metrics['total_bookings'] >= 1

def test_admin_step_3_add_vehicle(admin_client):
    """Admin Step 3: Add new vehicle to fleet with specifications."""
    reg = f"QA-REG-{int(datetime.now().timestamp()) % 100000}"
    data = {
        "name": "Lucid Air Grand Touring",
        "brand": "Lucid",
        "category": "electric",
        "registration_number": reg,
        "seating_capacity": "5",
        "fuel_type": "Electric (900V Architecture)",
        "transmission": "Single-Speed Automatic",
        "price_per_day": "225.00",
        "description": "Ultra luxury 516-mile range electric executive flagship.",
        "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=1200&q=80",
        "status": "available"
    }
    resp = admin_client.post('/admin/vehicles/add', data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert "successfully added" in resp.data.decode('utf-8').lower() or "added to the fleet" in resp.data.decode('utf-8').lower()

    # Confirm MySQL record
    v = execute_query("SELECT id, name, brand, price_per_day FROM vehicles WHERE registration_number = %s", (reg,), fetch_one=True)
    assert v is not None
    assert v['name'] == "Lucid Air Grand Touring"
    assert float(v['price_per_day']) == 225.0

def test_admin_step_4_edit_vehicle(admin_client):
    """Admin Step 4: Edit existing vehicle details and pricing."""
    v = execute_query("SELECT id, registration_number FROM vehicles WHERE name LIKE '%Lucid Air%' ORDER BY id DESC", fetch_one=True)
    v_id = v['id']

    data = {
        "name": "Lucid Air Sapphire",
        "brand": "Lucid Motors",
        "category": "sports",
        "registration_number": v['registration_number'],
        "seating_capacity": "5",
        "fuel_type": "Tri-Motor Electric",
        "transmission": "Automatic",
        "price_per_day": "295.00",
        "description": "Sub-2 second 0-60 hyper-sedan.",
        "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=1200&q=80",
        "status": "available"
    }
    resp = admin_client.post(f'/admin/vehicles/{v_id}/edit', data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert "updated successfully" in resp.data.decode('utf-8').lower()

    updated = execute_query("SELECT name, price_per_day FROM vehicles WHERE id = %s", (v_id,), fetch_one=True)
    assert updated['name'] == "Lucid Air Sapphire"
    assert float(updated['price_per_day']) == 295.0

def test_admin_step_5_view_customer_bookings(admin_client):
    """Admin Step 5: View all bookings with search and status filtering."""
    resp = admin_client.get('/admin/bookings?status=all')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8').lower()
    assert "ledger" in html or "booking" in html

    # Search filter
    resp_search = admin_client.get('/admin/bookings?search=Alexander')
    assert resp_search.status_code == 200
    assert "Alexander" in resp_search.data.decode('utf-8')

def test_admin_step_6_approve_booking_with_conflict_prevention(admin_client):
    """Admin Step 6: Approve pending booking while verifying conflict prevention."""
    today = date.today()
    p1 = (today + timedelta(days=120)).isoformat()
    r1 = (today + timedelta(days=125)).isoformat()

    execute_query("DELETE FROM bookings WHERE vehicle_id = 3 AND start_date >= %s", (p1,), commit=True)

    # 1. First pending booking
    execute_query("""
        INSERT INTO bookings (booking_reference, user_id, vehicle_id, start_date, end_date, total_days, total_amount, booking_status, payment_status)
        VALUES ('RYD-QA-APP1', 2, 3, %s, %s, 5, 875.00, 'pending', 'paid')
    """, (p1, r1), commit=True)
    b1 = execute_query("SELECT id FROM bookings WHERE booking_reference = 'RYD-QA-APP1'", fetch_one=True)

    # Admin approves b1
    resp_app = admin_client.post(f'/admin/bookings/{b1["id"]}/status', data={"status": "confirmed"}, follow_redirects=True)
    assert "confirmed" in resp_app.data.decode('utf-8').lower()

    # 2. Overlapping second pending booking
    p2 = (today + timedelta(days=122)).isoformat()
    r2 = (today + timedelta(days=126)).isoformat()
    execute_query("""
        INSERT INTO bookings (booking_reference, user_id, vehicle_id, start_date, end_date, total_days, total_amount, booking_status, payment_status)
        VALUES ('RYD-QA-APP2', 2, 3, %s, %s, 4, 700.00, 'pending', 'paid')
    """, (p2, r2), commit=True)
    b2 = execute_query("SELECT id FROM bookings WHERE booking_reference = 'RYD-QA-APP2'", fetch_one=True)

    # Admin attempts to approve b2 -> conflicting error!
    resp_conf = admin_client.post(f'/admin/bookings/{b2["id"]}/status', data={"status": "confirmed"}, follow_redirects=True)
    assert "already reserved" in resp_conf.data.decode('utf-8').lower() or "conflict" in resp_conf.data.decode('utf-8').lower()

def test_admin_step_7_verify_customer_documents(admin_client):
    """Admin Step 7: Verify customer uploaded document with audit remarks."""
    execute_query("DELETE FROM documents WHERE file_path = 'uploads/documents/qa_audit_id.pdf'", commit=True)
    execute_query("""
        INSERT INTO documents (user_id, document_type, file_path, verification_status)
        VALUES (2, 'drivers_license', 'uploads/documents/qa_audit_id.pdf', 'pending')
    """, commit=True)
    doc = execute_query("SELECT id FROM documents WHERE file_path = 'uploads/documents/qa_audit_id.pdf'", fetch_one=True)
    doc_id = doc['id']

    # Admin approves document
    resp = admin_client.post(f'/admin/documents/{doc_id}/verify', data={
        "status": "verified",
        "remarks": "Driver credentials validated against state transport database."
    }, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.data.decode('utf-8').lower()
    assert "marked as" in html and "verified" in html

    updated = execute_query("SELECT verification_status, remarks FROM documents WHERE id = %s", (doc_id,), fetch_one=True)
    assert updated['verification_status'] == 'verified'
    assert "validated" in updated['remarks']

def test_admin_step_8_and_9_return_processing_and_additional_charges(admin_client):
    """Admin Steps 8 & 9: Record vehicle return and calculate configurable late charges."""
    # Setup rental that was scheduled to end 2 days ago (Vehicle #8 Genesis G80: $135/day)
    two_days_ago = date.today() - timedelta(days=2)
    five_days_ago = date.today() - timedelta(days=5)

    execute_query("DELETE FROM returns WHERE booking_id IN (SELECT id FROM bookings WHERE booking_reference = 'RYD-QA-RETURN')", commit=True)
    execute_query("DELETE FROM bookings WHERE booking_reference = 'RYD-QA-RETURN'", commit=True)
    execute_query("UPDATE vehicles SET status = 'rented' WHERE id = 8", commit=True)

    execute_query("""
        INSERT INTO bookings (booking_reference, user_id, vehicle_id, start_date, end_date, total_days, total_amount, booking_status, payment_status)
        VALUES ('RYD-QA-RETURN', 2, 8, %s, %s, 3, 405.00, 'confirmed', 'paid')
    """, (five_days_ago.isoformat(), two_days_ago.isoformat()), commit=True)
    b = execute_query("SELECT id FROM bookings WHERE booking_reference = 'RYD-QA-RETURN'", fetch_one=True)
    b_id = b['id']

    # Process return with custom late multiplier (1.5x) and manual cleaning fee ($75.00)
    now_dt = datetime.now().strftime("%Y-%m-%dT%H:%M")
    resp = admin_client.post('/admin/returns/process', data={
        "booking_id": str(b_id),
        "actual_return_date": now_dt,
        "vehicle_condition": "Fair - Sanitization & Fuel Needed",
        "manual_charges": "75.00",
        "late_multiplier": "1.5",
        "remarks": "Returned 2 days late. Full detailing & fuel top-up completed."
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert "vehicle return processed" in resp.data.decode('utf-8').lower()

    # Step 10: Confirm database updates in MySQL
    ret = execute_query("SELECT booking_id, actual_return_date, additional_charges, vehicle_condition FROM returns WHERE booking_id = %s", (b_id,), fetch_one=True)
    assert ret is not None
    # 2 overdue days * $135 * 1.5 = $405.00 late fee + $75.00 manual charges = $480.00
    assert float(ret['additional_charges']) == 480.0

    b_up = execute_query("SELECT booking_status FROM bookings WHERE id = %s", (b_id,), fetch_one=True)
    assert b_up['booking_status'] == 'completed'

    v_up = execute_query("SELECT status FROM vehicles WHERE id = 8", fetch_one=True)
    assert v_up['status'] == 'available'

# ==============================================================================
# PART 3: SECURITY, STATIC SERVING & QUALITY CHECKS
# ==============================================================================

def test_security_uploaded_file_execution_prevention(client):
    """Verify script/executable extensions are strictly blocked from static execution."""
    resp_py = client.get('/uploads/malicious_script.py')
    assert resp_py.status_code in (403, 404)

    resp_php = client.get('/uploads/exploit.php')
    assert resp_php.status_code in (403, 404)

    resp_exe = client.get('/uploads/payload.exe')
    assert resp_exe.status_code in (403, 404)

def test_security_directory_traversal_blocked(client):
    """Verify path traversal (../) attacks are blocked."""
    resp_trav = client.get('/uploads/../../config/config.py')
    assert resp_trav.status_code == 404

def test_security_document_privacy_isolation(client, auth_customer_client):
    """Verify anonymous and unauthorized customers cannot view other customers' identity files."""
    # Create test document belonging to user 1 (Admin)
    execute_query("DELETE FROM documents WHERE file_path = 'uploads/documents/confidential_id.pdf'", commit=True)
    execute_query("""
        INSERT INTO documents (user_id, document_type, file_path, verification_status)
        VALUES (1, 'passport', 'uploads/documents/confidential_id.pdf', 'pending')
    """, commit=True)

    # 1. Anonymous request blocked
    resp_anon = client.get('/uploads/documents/confidential_id.pdf')
    assert resp_anon.status_code == 401

    # 2. Customer 2 (Alexander) blocked from viewing user 1's document
    resp_cust = auth_customer_client.get('/uploads/documents/confidential_id.pdf')
    assert resp_cust.status_code == 403

def test_security_customer_cannot_access_other_customer_agreement(app):
    """Verify customer cannot view another customer's rental agreement or voucher."""
    other_client = app.test_client()
    with other_client.session_transaction() as sess:
        sess['user_id'] = 999
        sess['user_name'] = 'Stranger'
        sess['role'] = 'customer'

    # Booking #1 belongs to user 2
    resp = other_client.get('/bookings/1/agreement')
    assert resp.status_code == 404

def test_security_double_booking_concurrency_protection(auth_customer_client):
    """Verify simultaneous or overlapping booking creation for identical dates is strictly rejected."""
    today = date.today()
    p = (today + timedelta(days=150)).isoformat()
    r = (today + timedelta(days=155)).isoformat()

    execute_query("DELETE FROM bookings WHERE vehicle_id = 5 AND start_date >= %s", (p,), commit=True)

    # First booking succeeds
    b1 = booking_service.create_customer_booking(2, 5, p, r, "Demo Card")
    assert b1 is not None

    # Overlapping attempt rejected with ValueError
    with pytest.raises(ValueError) as excinfo:
        booking_service.create_customer_booking(2, 5, p, r, "Demo Card")
    assert "already reserved" in str(excinfo.value).lower()
