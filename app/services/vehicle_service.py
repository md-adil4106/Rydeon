"""
Rydeon - Vehicle Service Layer
------------------------------
Handles vehicle queries, filtering, and data retrieval from MySQL using
parameterized SQL queries.
"""

from app.database.db import execute_query

def get_all_vehicles(category=None, status=None, max_price=None, search=None):
    """
    Retrieves vehicles from MySQL with optional filtering.
    Guarantees SQL injection safety via parameterized queries.
    """
    sql = """
        SELECT id, name, brand, category, registration_number, seating_capacity,
               fuel_type, transmission, price_per_day, image, description, status, created_at
        FROM vehicles
        WHERE 1=1
    """
    params = []

    if category and category.lower() != 'all':
        sql += " AND LOWER(category) = LOWER(%s)"
        params.append(category)

    if status:
        sql += " AND status = %s"
        params.append(status)

    if max_price:
        sql += " AND price_per_day <= %s"
        params.append(float(max_price))

    if search:
        sql += " AND (LOWER(name) LIKE %s OR LOWER(brand) LIKE %s OR LOWER(description) LIKE %s)"
        wildcard = f"%{search.lower()}%"
        params.extend([wildcard, wildcard, wildcard])

    sql += " ORDER BY price_per_day DESC"
    return execute_query(sql, tuple(params), fetch_all=True)

def get_featured_vehicles(limit=4):
    """Retrieves top-tier featured vehicles for landing page display."""
    sql = """
        SELECT id, name, brand, category, registration_number, seating_capacity,
               fuel_type, transmission, price_per_day, image, description, status, created_at
        FROM vehicles
        ORDER BY price_per_day DESC
        LIMIT %s
    """
    return execute_query(sql, (limit,), fetch_all=True)

def get_vehicle_by_id(vehicle_id):
    """Retrieves a single vehicle by its primary key ID."""
    sql = """
        SELECT id, name, brand, category, registration_number, seating_capacity,
               fuel_type, transmission, price_per_day, image, description, status, created_at
        FROM vehicles
        WHERE id = %s
    """
    return execute_query(sql, (vehicle_id,), fetch_one=True)

def get_vehicle_by_registration(reg_number):
    """Retrieves a single vehicle by its unique registration number."""
    sql = """
        SELECT id, name, brand, category, registration_number, seating_capacity,
               fuel_type, transmission, price_per_day, image, description, status, created_at
        FROM vehicles
        WHERE registration_number = %s
    """
    return execute_query(sql, (reg_number,), fetch_one=True)
