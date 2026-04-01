# Hostel Allocation System

A fully functional, modern hostel allocation system built with **Python (Flask)** and **SQLite**. Designed for streamlined student management, real-time allocation, and organized complaint tracking.

## Features

- **Student Self-Registration**: Secure signup with personal and academic details.
- **Preference Matching**: Students specify their building, AC, and room type preferences.
- **Admin Dashboard**: Real-time overview of unallocated students, active allocations, and hostel capacity.
- **Smart Allocation**: Admins see room availability filtered by gender and preferences for optimal assignment.
- **Waiting List**: Automatic rank assignment when no suitable rooms are available.
- **Complaint Management**: Two-way communication for reporting and resolving room/hostel issues.
- **In-App Notifications**: Alerts for allocation changes, waitlist status, and complaint updates.
- **Premium UI**: Responsive design with a clean sidebar for admins and a modern dashboard for students.

## Technology Stack

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Database**: SQLite (easy switch to PostgreSQL via environment variables)
- **Frontend**: Bootstrap 5.3, custom CSS for a premium look, Inter font, Vanilla JS
- **Auth**: Secure password hashing with Werkzeug

## Installation

### 1. Prerequisites
- Python 3.8 or higher installed on your system.

### 2. Setup Virtual Environment
```bash
# Create venv
python -m venv venv

# Activate venv (Linux/macOS)
source venv/bin/activate

# For Windows
# venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize the Database & Seed Data
```bash
# Create an admin user manually
python create_admin.py --email admin@hostel.com --password admin123 --name "Super Admin"

# (Optional) Seed the database with some sample hostels, rooms, and students
python seed_data.py
```

### 5. Run the Application
```bash
python app.py
```
The application will be available at `http://127.0.0.1:5000`.

## Default Credentials
- **Admin**: `admin@hostel.com` / `admin123`
- **Sample Students** (if seeded): `ryan@student.com` or `emma@student.com` / `student123`

## Deployment
This application is ready to be hosted on platforms like PythonAnywhere, Heroku, or a VPS.
For production use:
1. Set a unique `SECRET_KEY` in environment variables.
2. Provide a `DATABASE_URL` for PostgreSQL if scaling is required.
3. Use a WSGI server like `gunicorn` or `waitress`.