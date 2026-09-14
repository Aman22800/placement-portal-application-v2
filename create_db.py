"""
Run this ONCE to create the database and seed the single admin user.
Usage: python3 create_db.py
"""
from werkzeug.security import generate_password_hash
from app import app
from models import db, User

with app.app_context():
    db.create_all()
    print("Tables created.")

    existing_admin = User.query.filter_by(role='admin').first()
    if existing_admin:
        print("Admin already exists, skipping seed.")
    else:
        admin = User(
            email='admin@placementportal.com',
            password_hash=generate_password_hash('admin123'),  # change this before submission
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created -> email: admin@placementportal.com | password: admin123")
