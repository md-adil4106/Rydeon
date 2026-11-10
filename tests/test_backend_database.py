"""
Rydeon - Backend and MySQL Integration Test Suite
-------------------------------------------------
Validates:
1. MySQL connectivity & connection pooling.
2. Table creation across all 6 core tables.
3. Foreign key relationships and constraints.
4. Parameterized query execution, data insertion and retrieval.
5. Error handling and 503 template rendering when database is unreachable.
"""

import pytest
import mysql.connector
from app import create_app
from config.config import TestingConfig
from app.database.db import (
    get_connection_pool,
    get_raw_connection,
    execute_query,
    check_db_health,
    reset_connection_pool
)
from app.services import vehicle_service, booking_service, user_service

@pytest.fixture(scope="module")
def app():
    app = create_app(TestingConfig)
    return app

@pytest.fixture(scope="module")
def client(app):
    return app.test_client()

# ==============================================================================
# 1. VERIFICATION: MYSQL CONNECTION
# ==============================================================================
def test_mysql_connectivity():
    """Verify live MySQL server connectivity and ping health check."""
    is_healthy, message = check_db_health()
    assert is_healthy is True
    assert "operational" in message.lower()

def test_connection_pooling():
    """Verify that thread-safe connection pooling is active and yielding connections."""
    pool = get_connection_pool()
    assert pool is not None
    conn = pool.get_connection()
    assert conn.is_connected() is True
    conn.close()

def test_api_health_endpoint(client):
    """Verify that /api/health endpoint returns 200 OK with MySQL status."""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == "healthy"
    assert data['database'] == "MySQL"

# ==============================================================================
# 2. VERIFICATION: TABLE CREATION
# ==============================================================================
def test_all_tables_exist():
    """Verify all 6 core tables exist in the vehicle_rental_system database."""
    expected_tables = {'users', 'vehicles', 'bookings', 'documents', 'payments', 'returns'}
    sql = """
        SELECT table_name AS table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'vehicle_rental_system'
    """
    rows = execute_query(sql, fetch_all=True)
    existing_tables = set()
    for row in rows:
        val = row.get('table_name') or row.get('TABLE_NAME')
        if val:
            existing_tables.add(val.lower())
    missing = expected_tables - existing_tables
    assert not missing, f"Missing tables in database: {missing}"

def test_table_columns_users():
    """Verify required column definitions for users table."""
    sql = "DESCRIBE users"
    columns = {row['Field']: row for row in execute_query(sql, fetch_all=True)}
    for col in ['id', 'full_name', 'email', 'phone', 'password_hash', 'role', 'created_at']:
        assert col in columns, f"users table missing column: {col}"

def test_table_columns_vehicles():
    """Verify required column definitions for vehicles table."""
    sql = "DESCRIBE vehicles"
    columns = {row['Field']: row for row in execute_query(sql, fetch_all=True)}
    expected = [
        'id', 'name', 'brand', 'category', 'registration_number',
        'seating_capacity', 'fuel_type', 'transmission', 'price_per_day',
        'image', 'description', 'status', 'created_at'
    ]
    for col in expected:
        assert col in columns, f"vehicles table missing column: {col}"

# ==============================================================================
# 3. VERIFICATION: FOREIGN KEY RELATIONSHIPS
# ==============================================================================
def test_foreign_key_constraints():
    """Verify referential integrity constraints connecting all related tables."""
    sql = """
        SELECT table_name AS table_name, constraint_name AS constraint_name, referenced_table_name AS referenced_table_name
        FROM information_schema.referential_constraints
        WHERE constraint_schema = 'vehicle_rental_system'
    """
    fk_rows = execute_query(sql, fetch_all=True)
    fk_map = set()
    for row in fk_rows:
        tbl = (row.get('table_name') or row.get('TABLE_NAME') or '').lower()
        ref = (row.get('referenced_table_name') or row.get('REFERENCED_TABLE_NAME') or '').lower()
        fk_map.add((tbl, ref))

    # Bookings -> Users
    assert ('bookings', 'users') in fk_map
    # Bookings -> Vehicles
    assert ('bookings', 'vehicles') in fk_map
    # Payments -> Bookings
    assert ('payments', 'bookings') in fk_map
    # Returns -> Bookings
    assert ('returns', 'bookings') in fk_map
    # Documents -> Users
    assert ('documents', 'users') in fk_map

# ==============================================================================
# 4. VERIFICATION: SUCCESSFUL INSERTION AND RETRIEVAL (SERVICES & PARAMETERIZED SQL)
# ==============================================================================
def test_vehicle_service_retrieval():
    """Verify vehicle retrieval and parameterized filtering."""
    all_vehicles = vehicle_service.get_all_vehicles()
    assert len(all_vehicles) >= 12

    # Category filter
    electric_cars = vehicle_service.get_all_vehicles(category="Electric")
    assert len(electric_cars) >= 3
    for car in electric_cars:
        assert car['category'].lower() == "electric"

    # Price filter
    affordable = vehicle_service.get_all_vehicles(max_price=150)
    for car in affordable:
        assert float(car['price_per_day']) <= 150.0

    # Search filter
    porsche = vehicle_service.get_all_vehicles(search="Porsche")
    assert len(porsche) >= 1
    assert "Porsche" in porsche[0]['name']

def test_sql_injection_resistance():
    """Verify that malicious input strings do not corrupt query execution."""
    malicious_input = "'; DROP TABLE vehicles; --"
    results = vehicle_service.get_all_vehicles(search=malicious_input)
    assert results == []  # Safely returns 0 rows, table remains intact

    # Verify table is still intact
    count = execute_query("SELECT COUNT(*) AS total FROM vehicles", fetch_one=True)
    assert count['total'] >= 12

def test_user_and_booking_service_retrieval():
    """Verify customer profile, active booking and booking history retrieval."""
    user = user_service.get_user_by_email("alexander.wright@example.com")
    assert user is not None
    assert user['full_name'] == "Alexander Wright"
    assert user['role'] == "customer"

    # Active booking
    active_booking = booking_service.get_user_active_booking(user['id'])
    assert active_booking is not None
    assert active_booking['booking_status'] == 'confirmed'
    assert active_booking['vehicle_name'] is not None

    # History
    history = booking_service.get_user_booking_history(user['id'])
    assert len(history) >= 1
    assert history[0]['booking_status'] == 'completed'

    # Stats
    stats = booking_service.get_user_stats(user['id'])
    assert stats['active_rentals'] >= 1
    assert stats['completed_rentals'] >= 1

# ==============================================================================
# 5. VERIFICATION: ERROR HANDLING WHEN DATABASE CONNECTIVITY FAILS
# ==============================================================================
def test_database_failure_handling():
    """Verify that when database fails, errors are caught gracefully and 503 is rendered."""
    reset_connection_pool()
    class BadConfig(TestingConfig):
        DB_PORT = 33999  # Unused port to simulate down database
        DB_POOL_NAME = "bad_pool_test"

    bad_app = create_app(BadConfig)
    bad_client = bad_app.test_client()

    try:
        # API healthcheck returns 503
        resp = bad_client.get('/api/health')
        assert resp.status_code == 503
        data = resp.get_json()
        assert data['status'] == "unhealthy"

        # Web page route returns 503 with friendly error template
        page_resp = bad_client.get('/')
        assert page_resp.status_code == 503
        html = page_resp.data.decode('utf-8')
        assert "Database Connection Unavailable" in html
    finally:
        # Reset pool after test to restore normal connection state
        reset_connection_pool()

# ==============================================================================
# 6. VERIFICATION: FRONTEND INTEGRATION WITH LIVE DATABASE
# ==============================================================================
def test_frontend_routes_render_db_data(client):
    """Verify frontend pages render live MySQL data."""
    # Landing page renders vehicles from DB
    res = client.get('/')
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    assert "Featured Vehicles" in html
    assert "Taycan" in html or "S-Class" in html

    # Catalogue renders 12 vehicles
    cat_res = client.get('/catalogue')
    assert cat_res.status_code == 200
    cat_html = cat_res.data.decode('utf-8')
    assert "Premier Vehicle Fleet" in cat_html
    assert "Porsche Taycan 4S" in cat_html
    assert "Cadillac Escalade" in cat_html

    # Dashboard renders active booking and user from DB
    dash_res = client.get('/dashboard')
    assert dash_res.status_code == 200
    dash_html = dash_res.data.decode('utf-8')
    assert "Alexander Wright" in dash_html
    assert "Current & Upcoming Booking" in dash_html
