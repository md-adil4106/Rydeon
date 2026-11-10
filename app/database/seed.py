"""
Rydeon - Database Seeding Script
--------------------------------
Populates vehicle_rental_system with 12 diverse sample vehicles across
multiple categories, test customer and admin users, and sample booking records.
Safe to execute repeatedly without generating duplicate records.
"""

import os
import sys
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash

# Ensure project root is in sys.path for direct script execution
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.database.db import get_db_cursor, init_db

SAMPLE_VEHICLES_DATA = [
    {
        "name": "Porsche Taycan 4S",
        "brand": "Porsche",
        "category": "Electric",
        "registration_number": "RYD-EL-0101",
        "seating_capacity": 4,
        "fuel_type": "Electric",
        "transmission": "Automatic",
        "price_per_day": 195.00,
        "image": "https://images.unsplash.com/photo-1614162692292-7ac56d7f7f1e?auto=format&fit=crop&w=1000&q=80",
        "description": "Pure electric soul with dual-motor all-wheel drive, adaptive air suspension, and 285 miles of range.",
        "status": "available"
    },
    {
        "name": "BMW M4 Competition Coupé",
        "brand": "BMW",
        "category": "Sports",
        "registration_number": "RYD-SP-0202",
        "seating_capacity": 4,
        "fuel_type": "Gasoline",
        "transmission": "Automatic",
        "price_per_day": 185.00,
        "image": "https://images.unsplash.com/photo-1580273916550-e323be2ae537?auto=format&fit=crop&w=1000&q=80",
        "description": "503-horsepower twin-turbo inline-six, carbon fiber roof, and M xDrive motorsport precision.",
        "status": "available"
    },
    {
        "name": "Mercedes-Benz S-Class S 580",
        "brand": "Mercedes-Benz",
        "category": "Luxury",
        "registration_number": "RYD-LX-0303",
        "seating_capacity": 5,
        "fuel_type": "Mild Hybrid",
        "transmission": "Automatic",
        "price_per_day": 220.00,
        "image": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=1000&q=80",
        "description": "Executive flagship with Burmester 4D surround sound, rear-axle steering, and active massaging seats.",
        "status": "rented"
    },
    {
        "name": "Range Rover Sport Dynamic",
        "brand": "Land Rover",
        "category": "SUV",
        "registration_number": "RYD-SU-0404",
        "seating_capacity": 5,
        "fuel_type": "Hybrid",
        "transmission": "Automatic",
        "price_per_day": 175.00,
        "image": "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=1000&q=80",
        "description": "All-terrain dynamic air suspension, pixel LED lighting, and refined peerless British luxury.",
        "status": "available"
    },
    {
        "name": "Tesla Model S Plaid",
        "brand": "Tesla",
        "category": "Electric",
        "registration_number": "RYD-EL-0505",
        "seating_capacity": 5,
        "fuel_type": "Electric",
        "transmission": "Automatic",
        "price_per_day": 170.00,
        "image": "https://images.unsplash.com/photo-1536700503339-1e4b06520771?auto=format&fit=crop&w=1000&q=80",
        "description": "Tri-motor AWD hyper-acceleration (0-60 in 1.99s), 396 miles range, and panoramic glass canopy.",
        "status": "available"
    },
    {
        "name": "Audi RS6 Avant Performance",
        "brand": "Audi",
        "category": "Sports",
        "registration_number": "RYD-SP-0606",
        "seating_capacity": 5,
        "fuel_type": "Gasoline",
        "transmission": "Automatic",
        "price_per_day": 190.00,
        "image": "https://images.unsplash.com/photo-1603584173870-7f23fdae1b7a?auto=format&fit=crop&w=1000&q=80",
        "description": "Twin-turbo 621 HP V8 super-wagon with quattro permanent all-wheel drive and ceramic brake package.",
        "status": "available"
    },
    {
        "name": "Volvo XC90 Recharge Ultimate",
        "brand": "Volvo",
        "category": "SUV",
        "registration_number": "RYD-SU-0707",
        "seating_capacity": 7,
        "fuel_type": "Plug-in Hybrid",
        "transmission": "Automatic",
        "price_per_day": 140.00,
        "image": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1000&q=80",
        "description": "Spacious Scandinavian 7-passenger plug-in hybrid SUV featuring Pilot Assist and Bowers & Wilkins audio.",
        "status": "available"
    },
    {
        "name": "Genesis G80 Electrified",
        "brand": "Genesis",
        "category": "Luxury",
        "registration_number": "RYD-LX-0808",
        "seating_capacity": 5,
        "fuel_type": "Electric",
        "transmission": "Automatic",
        "price_per_day": 135.00,
        "image": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1000&q=80",
        "description": "Ultra-quiet luxury electric sedan with solar roof panel and electronically controlled preview suspension.",
        "status": "available"
    },
    {
        "name": "Ford Mustang GT Premium",
        "brand": "Ford",
        "category": "Sports",
        "registration_number": "RYD-SP-0909",
        "seating_capacity": 4,
        "fuel_type": "Gasoline",
        "transmission": "Automatic",
        "price_per_day": 125.00,
        "image": "https://images.unsplash.com/photo-1584345604476-8ec5e12e42dd?auto=format&fit=crop&w=1000&q=80",
        "description": "480 HP 5.0L Coyote V8 engine with active valve performance exhaust and Brembo braking.",
        "status": "available"
    },
    {
        "name": "BMW 530i M Sport",
        "brand": "BMW",
        "category": "Sedan",
        "registration_number": "RYD-SD-1010",
        "seating_capacity": 5,
        "fuel_type": "Mild Hybrid",
        "transmission": "Automatic",
        "price_per_day": 115.00,
        "image": "https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=1000&q=80",
        "description": "Sleek executive sport sedan delivering balanced agility, refined leather cabin, and BMW Live Cockpit.",
        "status": "available"
    },
    {
        "name": "Cadillac Escalade Premium Luxury",
        "brand": "Cadillac",
        "category": "SUV",
        "registration_number": "RYD-SU-1111",
        "seating_capacity": 7,
        "fuel_type": "Gasoline",
        "transmission": "Automatic",
        "price_per_day": 210.00,
        "image": "https://images.unsplash.com/photo-1570125909232-eb263c188f7e?auto=format&fit=crop&w=1000&q=80",
        "description": "Full-size commanding presence with curved 38-inch OLED display, AKG Studio sound, and Super Cruise.",
        "status": "available"
    },
    {
        "name": "Lucid Air Grand Touring",
        "brand": "Lucid",
        "category": "Electric",
        "registration_number": "RYD-EL-1212",
        "seating_capacity": 5,
        "fuel_type": "Electric",
        "transmission": "Automatic",
        "price_per_day": 205.00,
        "image": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1000&q=80",
        "description": "819 HP state-of-the-art electric architecture with 516 miles EPA range and surreal glass cockpit.",
        "status": "available"
    }
]

def seed_database():
    """Initializes tables and seeds initial users, vehicles, and test bookings idempotently."""
    print("-> Ensuring schema exists...")
    init_db()

    with get_db_cursor(commit=True) as (conn, cursor):
        # 1. Seed Users
        print("-> Seeding default users...")
        users_to_seed = [
            ("Admin User", "admin@rydeon-rentals.com", "+1-800-555-0100", generate_password_hash("AdminSecret2026!"), "admin"),
            ("Alexander Wright", "alexander.wright@example.com", "+1-555-389-7241", generate_password_hash("CustomerSecret2026!"), "customer")
        ]
        user_insert_sql = """
            INSERT INTO users (full_name, email, phone, password_hash, role)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                full_name=VALUES(full_name),
                phone=VALUES(phone),
                role=VALUES(role);
        """
        for u in users_to_seed:
            cursor.execute(user_insert_sql, u)

        # 2. Seed Vehicles
        print(f"-> Seeding {len(SAMPLE_VEHICLES_DATA)} vehicles...")
        vehicle_insert_sql = """
            INSERT INTO vehicles (name, brand, category, registration_number, seating_capacity, 
                                  fuel_type, transmission, price_per_day, image, description, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name=VALUES(name),
                brand=VALUES(brand),
                category=VALUES(category),
                seating_capacity=VALUES(seating_capacity),
                fuel_type=VALUES(fuel_type),
                transmission=VALUES(transmission),
                price_per_day=VALUES(price_per_day),
                image=VALUES(image),
                description=VALUES(description),
                status=VALUES(status);
        """
        for v in SAMPLE_VEHICLES_DATA:
            cursor.execute(vehicle_insert_sql, (
                v["name"], v["brand"], v["category"], v["registration_number"],
                v["seating_capacity"], v["fuel_type"], v["transmission"],
                v["price_per_day"], v["image"], v["description"], v["status"]
            ))

        # 3. Retrieve seeded customer and vehicle for sample bookings
        cursor.execute("SELECT id FROM users WHERE email = %s", ("alexander.wright@example.com",))
        user_row = cursor.fetchone()
        user_id = user_row['id'] if user_row else None

        cursor.execute("SELECT id, price_per_day FROM vehicles WHERE registration_number = %s", ("RYD-LX-0303",))
        s_class = cursor.fetchone()

        cursor.execute("SELECT id, price_per_day FROM vehicles WHERE registration_number = %s", ("RYD-EL-0101",))
        taycan = cursor.fetchone()

        # 4. Seed Active Booking if not already present
        if user_id and s_class:
            cursor.execute("""
                SELECT id FROM bookings WHERE user_id = %s AND vehicle_id = %s AND booking_status = 'confirmed'
            """, (user_id, s_class['id']))
            existing_booking = cursor.fetchone()

            if not existing_booking:
                print("-> Seeding sample active booking...")
                today = date.today()
                start_date = today + timedelta(days=2)
                end_date = today + timedelta(days=6)
                total_days = 4
                total_amount = float(s_class['price_per_day']) * total_days

                cursor.execute("""
                    INSERT INTO bookings (booking_reference, user_id, vehicle_id, start_date, end_date, total_days, total_amount, booking_status, payment_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'confirmed', 'paid')
                """, ("RYD-BK-0001", user_id, s_class['id'], start_date, end_date, total_days, total_amount))
                booking_id = cursor.lastrowid

                # Seed corresponding payment
                cursor.execute("""
                    INSERT INTO payments (booking_id, amount, transaction_reference, payment_method, payment_status)
                    VALUES (%s, %s, %s, %s, 'completed')
                    ON DUPLICATE KEY UPDATE amount=VALUES(amount);
                """, (booking_id, total_amount, f"TXN-RYD-{booking_id}-CONF", "Credit Card (Visa)"))

                # Seed sample document
                cursor.execute("""
                    INSERT INTO documents (user_id, booking_id, document_type, file_path, verification_status)
                    VALUES (%s, %s, 'drivers_license', 'uploads/licenses/sample_license.pdf', 'verified')
                """, (user_id, booking_id))

        # 5. Seed Past Completed Booking for History
        if user_id and taycan:
            cursor.execute("""
                SELECT id FROM bookings WHERE user_id = %s AND vehicle_id = %s AND booking_status = 'completed'
            """, (user_id, taycan['id']))
            existing_past = cursor.fetchone()

            if not existing_past:
                print("-> Seeding sample completed booking with return record...")
                past_start = date.today() - timedelta(days=20)
                past_end = date.today() - timedelta(days=17)
                past_days = 3
                past_amount = float(taycan['price_per_day']) * past_days

                cursor.execute("""
                    INSERT INTO bookings (booking_reference, user_id, vehicle_id, start_date, end_date, total_days, total_amount, booking_status, payment_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'completed', 'paid')
                """, ("RYD-BK-0002", user_id, taycan['id'], past_start, past_end, past_days, past_amount))
                past_booking_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO payments (booking_id, amount, transaction_reference, payment_method, payment_status)
                    VALUES (%s, %s, %s, %s, 'completed')
                    ON DUPLICATE KEY UPDATE amount=VALUES(amount);
                """, (past_booking_id, past_amount, f"TXN-RYD-{past_booking_id}-PAST", "Apple Pay"))

                # Seed return record
                cursor.execute("""
                    INSERT INTO returns (booking_id, actual_return_date, additional_charges, vehicle_condition, remarks)
                    VALUES (%s, %s, 0.00, 'Excellent', 'Returned on time with 92% battery SOC. Inspection passed.')
                    ON DUPLICATE KEY UPDATE vehicle_condition=VALUES(vehicle_condition);
                """, (past_booking_id, datetime.now() - timedelta(days=17)))

    print("[OK] Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()
