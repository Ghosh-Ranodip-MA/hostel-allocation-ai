"""
Admin User Creation Script
-------------------------
Quick script to create the initial administrator account.
Usage: python create_admin.py --email admin@example.com --pass admin123 --name "Super Admin"
"""

import argparse
from app import create_app
from models import db, User


def create_admin_user(email, password, name):
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        user = User.query.filter_by(email=email.lower().strip(), role='admin').first()
        if user:
            print(f"Error: Admin with email {email} already exists.")
            return

        # Create new admin
        admin = User(
            email=email.lower().strip(),
            name=name.strip(),
            role='admin'
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Success: Admin user '{name}' created with email '{email}'.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create a system administrator.")
    parser.add_argument('--email', required=True, help="Admin login email")
    parser.add_argument('--password', required=True, help="Admin login password")
    parser.add_argument('--name', default="Administrator", help="Admin's display name")

    args = parser.parse_args()
    create_admin_user(args.email, args.password, args.name)