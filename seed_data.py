"""
Seed Data Script
----------------
Quickly populate the database with initial hostels, rooms, and a few sample students.
Useful for demonstrating and testing the system.
"""

from app import create_app
from models import db, Hostel, Room, User

def seed():
    app = create_app()
    with app.app_context():
        # Clear existing data if needed (optional)
        # db.drop_all()
        # db.create_all()

        # 1. Create Hostels
        if not Hostel.query.filter_by(name="Phoenix Boys Hall").first():
            h1 = Hostel(name="Phoenix Boys Hall", gender_type="boys", total_capacity=200, warden_name="Dr. Richards")
            db.session.add(h1)
        else:
            h1 = Hostel.query.filter_by(name="Phoenix Boys Hall").first()

        if not Hostel.query.filter_by(name="Sapphire Girls Annex").first():
            h2 = Hostel(name="Sapphire Girls Annex", gender_type="girls", total_capacity=150, warden_name="Prof. Sarah")
            db.session.add(h2)
        else:
            h2 = Hostel.query.filter_by(name="Sapphire Girls Annex").first()
        
        db.session.commit()

        # 2. & 3. Create Rooms if hostel has no rooms
        if h1.rooms.count() == 0:
            rooms_boys = [
                Room(hostel_id=h1.id, room_number="P101", floor=1, capacity=1, available_beds=1, room_type="single", ac=True),
                Room(hostel_id=h1.id, room_number="P102", floor=1, capacity=2, available_beds=2, room_type="double", ac=False),
                Room(hostel_id=h1.id, room_number="P201", floor=2, capacity=1, available_beds=1, room_type="single", ac=False),
                Room(hostel_id=h1.id, room_number="P202", floor=2, capacity=3, available_beds=3, room_type="triple", ac=True),
            ]
            db.session.add_all(rooms_boys)

        if h2.rooms.count() == 0:
            rooms_girls = [
                Room(hostel_id=h2.id, room_number="S101", floor=1, capacity=1, available_beds=1, room_type="single", ac=True),
                Room(hostel_id=h2.id, room_number="S201", floor=2, capacity=2, available_beds=2, room_type="double", ac=False),
            ]
            db.session.add_all(rooms_girls)
        
        db.session.commit()

        # 4. Create an Admin
        admin_email = "admin@hostel.com"
        if not User.query.filter_by(email=admin_email).first():
            admin = User(email=admin_email, name="System Admin", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)

        # 5. Create some Students (Unallocated)
        if not User.query.filter_by(email="ryan@student.com").first():
            s1 = User(
                email="ryan@student.com", name="Ryan Gosling", roll_number="CS202401",
                year="1st", branch="CS", gender="male", parent_phone="9876543210", 
                address="Hollywood Hills, LA", eating_preference="Non-Veg",
                preferred_ac=True, preferred_room_type="single"
            )
            s1.set_password("student123")
            db.session.add(s1)

        if not User.query.filter_by(email="emma@student.com").first():
            s2 = User(
                email="emma@student.com", name="Emma Stone", roll_number="EC202305",
                year="2nd", branch="EC", gender="female", parent_phone="9123456789", 
                address="Sunset Blvd, LA", eating_preference="Veg",
                preferred_ac=False, preferred_room_type="double"
            )
            s2.set_password("student123")
            db.session.add(s2)

        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed()