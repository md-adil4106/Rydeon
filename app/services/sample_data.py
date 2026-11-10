"""
Rydeon - Temporary Sample Data for Frontend Previews Only
---------------------------------------------------------
NOTICE: This data is temporary mockup data strictly intended for Phase 1
frontend layout, design review, and component validation.
In subsequent phases, all data will be served dynamically from the MySQL database.
"""

SAMPLE_VEHICLES = [
    {
        "id": 1,
        "name": "Porsche Taycan 4S",
        "category": "Electric",
        "tagline": "Pure electric soul with iconic sports car precision",
        "seats": 4,
        "transmission": "Automatic",
        "fuel_type": "Electric",
        "price_per_day": 195,
        "horsepower": "522 HP",
        "range_or_mileage": "285 mi range",
        "featured": True,
        "image_url": "https://images.unsplash.com/photo-1614162692292-7ac56d7f7f1e?auto=format&fit=crop&w=1000&q=80",
        "features": ["All-Wheel Drive", "Adaptive Air Suspension", "Fast DC Charging", "Burmester 3D Surround", "Porsche InnoDrive"]
    },
    {
        "id": 2,
        "name": "BMW M4 Competition Coupé",
        "category": "Sports",
        "tagline": "Uncompromising high-performance motorsport heritage",
        "seats": 4,
        "transmission": "Automatic",
        "fuel_type": "Gasoline",
        "price_per_day": 185,
        "horsepower": "503 HP",
        "range_or_mileage": "23 MPG",
        "featured": True,
        "image_url": "https://images.unsplash.com/photo-1580273916550-e323be2ae537?auto=format&fit=crop&w=1000&q=80",
        "features": ["M xDrive AWD", "Harman Kardon Sound", "Carbon Fiber Roof", "M Sport Exhaust", "Heads-Up Display"]
    },
    {
        "id": 3,
        "name": "Mercedes-Benz S-Class S 580",
        "category": "Luxury",
        "tagline": "The ultimate benchmark of executive luxury travel",
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Mild Hybrid",
        "price_per_day": 220,
        "horsepower": "496 HP",
        "range_or_mileage": "25 MPG",
        "featured": True,
        "image_url": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=1000&q=80",
        "features": ["Executive Rear Seating", "Burmester High-End 4D", "MBUX Interior Assistant", "Rear-Axle Steering", "Active Ambient Lighting"]
    },
    {
        "id": 4,
        "name": "Range Rover Sport Dynamic",
        "category": "SUV",
        "tagline": "Dynamic capability meets peerless British luxury",
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Hybrid",
        "price_per_day": 175,
        "horsepower": "395 HP",
        "range_or_mileage": "22 MPG",
        "featured": True,
        "image_url": "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=1000&q=80",
        "features": ["All-Terrain Progress Control", "Panoramic Sunroof", "Pixel LED Headlights", "Air Suspension", "3D Surround Camera"]
    },
    {
        "id": 5,
        "name": "Tesla Model S Plaid",
        "category": "Electric",
        "tagline": "Hypercar acceleration with effortless everyday luxury",
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Electric",
        "price_per_day": 170,
        "horsepower": "1020 HP",
        "range_or_mileage": "396 mi range",
        "featured": False,
        "image_url": "https://images.unsplash.com/photo-1536700503339-1e4b06520771?auto=format&fit=crop&w=1000&q=80",
        "features": ["Tri-Motor All-Wheel Drive", "0-60 in 1.99s", "Yoke Steering", "Supercharging Network", "Autopilot Hardware"]
    },
    {
        "id": 6,
        "name": "Audi RS6 Avant Performance",
        "category": "Sports",
        "tagline": "Twin-turbo V8 super-wagon with racetrack DNA",
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Gasoline",
        "price_per_day": 190,
        "horsepower": "621 HP",
        "range_or_mileage": "21 MPG",
        "featured": False,
        "image_url": "https://images.unsplash.com/photo-1603584173870-7f23fdae1b7a?auto=format&fit=crop&w=1000&q=80",
        "features": ["Quattro Permanent AWD", "RS Ceramic Brakes", "Bang & Olufsen 3D Sound", "HD Matrix LED", "Sport Differential"]
    },
    {
        "id": 7,
        "name": "Volvo XC90 Recharge Ultimate",
        "category": "SUV",
        "tagline": "Scandinavian 7-passenger hybrid excellence and safety",
        "seats": 7,
        "transmission": "Automatic",
        "fuel_type": "Plug-in Hybrid",
        "price_per_day": 140,
        "horsepower": "455 HP",
        "range_or_mileage": "32 mi EV / 27 MPG",
        "featured": False,
        "image_url": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1000&q=80",
        "features": ["7 Passenger Seating", "Pilot Assist", "Bowers & Wilkins Audio", "Air Purifier", "Nappa Leather"]
    },
    {
        "id": 8,
        "name": "Genesis G80 Electrified",
        "category": "Luxury",
        "tagline": "Serene acoustic refinement with refined electric agility",
        "seats": 5,
        "transmission": "Automatic",
        "fuel_type": "Electric",
        "price_per_day": 135,
        "horsepower": "365 HP",
        "range_or_mileage": "282 mi range",
        "featured": False,
        "image_url": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1000&q=80",
        "features": ["Dual Motor AWD", "Solar Roof Panel", "Lexicon Sound System", "Electronically Controlled Suspension"]
    },
    {
        "id": 9,
        "name": "Ford Mustang GT Premium",
        "category": "Sports",
        "tagline": "Thundering American 5.0L V8 convertible adventure",
        "seats": 4,
        "transmission": "Automatic",
        "fuel_type": "Gasoline",
        "price_per_day": 125,
        "horsepower": "480 HP",
        "range_or_mileage": "24 MPG",
        "featured": False,
        "image_url": "https://images.unsplash.com/photo-1584345604476-8ec5e12e42dd?auto=format&fit=crop&w=1000&q=80",
        "features": ["Active Valve Performance Exhaust", "Brembo 6-Piston Brakes", "MagneRide Damping", "Drop-top Convertible"]
    }
]

SAMPLE_USER = {
    "name": "Alexander Wright",
    "email": "alexander.wright@example.com",
    "phone": "+1 (555) 389-7241",
    "tier": "Executive Gold",
    "stats": {
        "active_rentals": 1,
        "completed_rentals": 8,
        "miles_driven": "2,450 mi",
        "reward_points": "1,200 pts"
    }
}

SAMPLE_CURRENT_BOOKING = {
    "booking_id": "RYD-2026-8812",
    "vehicle_name": "Mercedes-Benz S-Class S 580",
    "vehicle_category": "Luxury",
    "image_url": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=600&q=80",
    "pickup_date": "Nov 14, 2026",
    "return_date": "Nov 18, 2026",
    "pickup_location": "Central Metro Executive Hub",
    "daily_rate": 220,
    "total_days": 4,
    "total_amount": 880,
    "status": "Confirmed",
    "insurance": "Premium Full Protection",
    "reference_no": "CONF-983210"
}

SAMPLE_BOOKING_HISTORY = [
    {
        "booking_id": "RYD-2026-7419",
        "vehicle_name": "Porsche Taycan 4S",
        "rental_period": "Oct 20, 2026 - Oct 23, 2026",
        "duration": "3 Days",
        "total_amount": 585,
        "pickup_location": "Airport Terminal 1 Hub",
        "status": "Completed"
    },
    {
        "booking_id": "RYD-2026-6190",
        "vehicle_name": "Range Rover Sport Dynamic",
        "rental_period": "Sep 12, 2026 - Sep 16, 2026",
        "duration": "4 Days",
        "total_amount": 700,
        "pickup_location": "Downtown Central Hub",
        "status": "Completed"
    },
    {
        "booking_id": "RYD-2026-4831",
        "vehicle_name": "BMW M4 Competition Coupé",
        "rental_period": "Aug 02, 2026 - Aug 05, 2026",
        "duration": "3 Days",
        "total_amount": 555,
        "pickup_location": "Airport Terminal 1 Hub",
        "status": "Completed"
    }
]
