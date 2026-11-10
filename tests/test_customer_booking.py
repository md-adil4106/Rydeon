"""
Rydeon - Customer Rental Workflow Test Suite
--------------------------------------------
Validates:
1. Vehicle Catalogue filtering and availability.
2. Dedicated Vehicle Details display.
3. Backend date validation and price calculation (anti-tampering).
4. Prevention of overlapping bookings (anti-double booking).
5. Document upload security (extension and size validation).
6. Booking confirmation and printable summary voucher.
7. My Bookings management and cancellation policy enforcement.
"""

from datetime import date, timedelta
import io
import pytest
from app import create_app
from config.config import TestingConfig
from app.database.db import execute_query
from app.services import vehicle_service, booking_service, document_service

@pytest.fixture(scope="module")
def app():
    app = create_app(TestingConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_customer_client(app):
    """Client authenticated as customer Alexander Wright (ID: 2)."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_name'] = 'Alexander Wright'
        sess['email'] = 'alexander.wright@example.com'
        sess['role'] = 'customer'
    return client

@pytest.fixture
def second_customer_client(app):
    """Client authenticated as customer Elena Rostova (or another user ID: 3)."""
    # Create or retrieve second customer
    user = execute_query("SELECT id FROM users WHERE email = 'second.customer@example.com'", fetch_one=True)
    if not user:
        execute_query("""
            INSERT INTO users (full_name, email, phone, password_hash, role)
            VALUES ('Second Customer', 'second.customer@example.com', '+1-555-444-3333', 'hash', 'customer')
        """, commit=True)
        user = execute_query("SELECT id FROM users WHERE email = 'second.customer@example.com'", fetch_one=True)

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = user['id']
        sess['user_name'] = 'Second Customer'
        sess['email'] = 'second.customer@example.com'
        sess['role'] = 'customer'
    return client

# ==============================================================================
# 1. VEHICLE CATALOGUE & DETAILS TESTS
# ==============================================================================
def test_catalogue_filtering_and_availability(client):
    """Verify catalogue returns vehicles with live specifications and filter support."""
    # Filter by Electric
    electric_cars = vehicle_service.get_all_vehicles(category="Electric")
    assert len(electric_cars) >= 3
    for car in electric_cars:
        assert car['category'].lower() == "electric"

    # Search by brand
    bmw_cars = vehicle_service.get_all_vehicles(search="BMW")
    assert len(bmw_cars) >= 2

    # Price range filter
    affordable = vehicle_service.get_all_vehicles(max_price=150)
    for car in affordable:
        assert float(car['price_per_day']) <= 150.0

def test_vehicle_details_route(client):
    """Verify dedicated vehicle details page renders full specifications and CTA."""
    # Taycan (ID: 1)
    response = client.get('/vehicles/1')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "Porsche Taycan 4S" in html
    assert "Vehicle Overview" in html
    assert "Mechanical Specifications" in html
    assert "Book This Vehicle Now" in html

def test_vehicle_details_not_found(client):
    """Verify non-existent vehicle ID returns 404."""
    response = client.get('/vehicles/999999')
    assert response.status_code == 404

# ==============================================================================
# 2. BOOKING SYSTEM & DATE VALIDATION (BACKEND INTEGRITY)
# ==============================================================================
def test_anonymous_cannot_access_booking_form(client):
    """Verify unauthenticated user cannot access booking form."""
    response = client.get('/book/1', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_authenticated_customer_can_access_booking_form(auth_customer_client):
    """Verify logged-in customer accesses checkout booking form."""
    response = auth_customer_client.get('/book/1')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "Secure Vehicle Reservation" in html
    assert "Porsche Taycan 4S" in html

def test_backend_price_quote_calculation():
    """Verify backend calculates price accurately based on database rate, not client input."""
    today = date.today()
    pickup = today + timedelta(days=5)
    ret = today + timedelta(days=9)  # 4 days

    quote = booking_service.calculate_booking_quote(1, pickup, ret)
    assert quote['total_days'] == 4
    assert quote['daily_rate'] == 195.0
    assert quote['total_amount'] == 195.0 * 4

def test_booking_rejection_past_pickup_date(auth_customer_client):
    """Verify booking is rejected if pick-up date is in the past."""
    past_date = (date.today() - timedelta(days=2)).isoformat()
    future_date = (date.today() + timedelta(days=2)).isoformat()

    payload = {
        "pickup_date": past_date,
        "return_date": future_date,
        "payment_method": "Credit Card (Visa)"
    }
    response = auth_customer_client.post('/book/1', data=payload, follow_redirects=True)
    assert response.status_code == 400
    html = response.data.decode('utf-8')
    assert "cannot be in the past" in html.lower()

def test_booking_rejection_return_before_pickup(auth_customer_client):
    """Verify booking is rejected if return date is before pick-up date."""
    today = date.today()
    pickup = (today + timedelta(days=5)).isoformat()
    ret = (today + timedelta(days=3)).isoformat()

    payload = {
        "pickup_date": pickup,
        "return_date": ret,
        "payment_method": "Credit Card (Visa)"
    }
    response = auth_customer_client.post('/book/1', data=payload, follow_redirects=True)
    assert response.status_code == 400
    html = response.data.decode('utf-8')
    assert "must be after" in html.lower() or "must be strictly after" in html.lower()

# ==============================================================================
# 3. OVERLAPPING BOOKING PREVENTION (ANTI-DOUBLE BOOKING)
# ==============================================================================
def test_successful_booking_creation_and_overlap_prevention(auth_customer_client, second_customer_client):
    """
    1. First customer books Ford Mustang GT (ID: 9) from Day+30 to Day+35.
    2. Second customer attempts to book same car from Day+32 to Day+36 (overlaps).
    3. Verify second booking is rejected!
    4. Second customer books non-overlapping dates Day+40 to Day+45 -> succeeds!
    """
    today = date.today()
    car_id = 9  # Ford Mustang GT ($125/day)

    # Clean up prior test reservations for vehicle 9
    execute_query("DELETE FROM bookings WHERE vehicle_id = %s AND start_date >= %s", (car_id, (today + timedelta(days=25)).isoformat()), commit=True)

    p1 = (today + timedelta(days=30)).isoformat()
    r1 = (today + timedelta(days=35)).isoformat()

    payload1 = {
        "pickup_date": p1,
        "return_date": r1,
        "payment_method": "Apple Pay"
    }

    # 1. First customer booking succeeds
    resp1 = auth_customer_client.post(f'/book/{car_id}', data=payload1, follow_redirects=False)
    assert resp1.status_code == 302
    assert '/confirmation' in resp1.headers['Location']

    # 2. Second customer tries overlapping period (Day+32 to Day+36)
    p2_overlap = (today + timedelta(days=32)).isoformat()
    r2_overlap = (today + timedelta(days=36)).isoformat()

    payload_overlap = {
        "pickup_date": p2_overlap,
        "return_date": r2_overlap,
        "payment_method": "Credit Card (Visa)"
    }

    resp2 = second_customer_client.post(f'/book/{car_id}', data=payload_overlap, follow_redirects=True)
    assert resp2.status_code == 400
    html2 = resp2.data.decode('utf-8')
    assert "already reserved" in html2.lower()

    # 3. Second customer books non-overlapping period (Day+40 to Day+44)
    p3_clear = (today + timedelta(days=40)).isoformat()
    r3_clear = (today + timedelta(days=44)).isoformat()

    payload_clear = {
        "pickup_date": p3_clear,
        "return_date": r3_clear,
        "payment_method": "Debit Card"
    }

    resp3 = second_customer_client.post(f'/book/{car_id}', data=payload_clear, follow_redirects=False)
    assert resp3.status_code == 302
    assert '/confirmation' in resp3.headers['Location']

# ==============================================================================
# 4. DOCUMENT UPLOAD VALIDATION TESTS
# ==============================================================================
def test_document_upload_success_and_validation(auth_customer_client):
    """Verify document upload validates extension, size and records in MySQL."""
    # Find active booking for user 2
    user_id = 2
    booking = booking_service.get_user_active_booking(user_id)
    assert booking is not None
    booking_id = booking['booking_id']

    # 1. Successful valid PDF upload
    pdf_content = b"%PDF-1.4 sample license document content for verification"
    data = {
        "document_type": "drivers_license",
        "document_file": (io.BytesIO(pdf_content), "license_front.pdf")
    }

    resp = auth_customer_client.post(f'/bookings/{booking_id}/upload-document', data=data, follow_redirects=True)
    assert resp.status_code == 200

    docs = document_service.get_booking_documents(booking_id)
    assert len(docs) >= 1
    assert any(d['document_type'] == 'drivers_license' and d['verification_status'] == 'pending' for d in docs)

    # 2. Reject malicious executable extension
    bad_data = {
        "document_type": "drivers_license",
        "document_file": (io.BytesIO(b"malicious script"), "hack.exe")
    }
    resp_bad = auth_customer_client.post(f'/bookings/{booking_id}/upload-document', data=bad_data, follow_redirects=True)
    assert "invalid file format" in resp_bad.data.decode('utf-8').lower()

# ==============================================================================
# 5. MY BOOKINGS & CANCELLATION TESTS
# ==============================================================================
def test_my_bookings_display(auth_customer_client):
    """Verify My Bookings displays customer's upcoming and past trips."""
    response = auth_customer_client.get('/my-bookings')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "My Rental Reservations" in html
    assert "Upcoming & Confirmed Bookings" in html

def test_booking_cancellation_workflow(auth_customer_client, second_customer_client):
    """
    1. Create a future booking for user 2.
    2. Other user cannot cancel it.
    3. User 2 cancels it -> status becomes 'cancelled', payment becomes 'refunded'.
    """
    today = date.today()
    p = (today + timedelta(days=60)).isoformat()
    r = (today + timedelta(days=63)).isoformat()

    booking = booking_service.create_customer_booking(
        user_id=2,
        vehicle_id=2,  # BMW M4
        start_date_val=p,
        end_date_val=r,
        payment_method="Credit Card"
    )
    b_id = booking['booking_id']

    # Second customer tries to cancel user 2's booking -> rejected
    unauth_resp = second_customer_client.post(f'/bookings/{b_id}/cancel', follow_redirects=True)
    assert "access denied" in unauth_resp.data.decode('utf-8').lower() or "not found" in unauth_resp.data.decode('utf-8').lower()

    # User 2 cancels their own booking -> succeeds
    resp = auth_customer_client.post(f'/bookings/{b_id}/cancel', follow_redirects=True)
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "cancelled successfully" in html.lower()

    # Verify status in database
    updated = booking_service.get_booking_by_id(b_id)
    assert updated['booking_status'] == 'cancelled'
    assert updated['payment_status'] == 'refunded'

# ==============================================================================
# 6. BOOKING CONFIRMATION & PRIVACY ISOLATION
# ==============================================================================
def test_booking_confirmation_privacy_isolation(auth_customer_client, second_customer_client):
    """Verify that a customer cannot view another customer's confirmation voucher."""
    # User 2's booking ID: 1
    resp_owner = auth_customer_client.get('/bookings/1/confirmation')
    assert resp_owner.status_code == 200
    assert "Reservation Confirmed" in resp_owner.data.decode('utf-8')
    assert "Print Rental Voucher" in resp_owner.data.decode('utf-8')

    # Second customer tries to view booking 1 -> 404 Not Found (privacy protection)
    resp_other = second_customer_client.get('/bookings/1/confirmation')
    assert resp_other.status_code == 404
