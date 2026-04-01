# 🏢 AI-Powered Hostel Allocation System (HostelConnect)

A premium, fully-functional **Hostel Management & AI Allocation System** built with **Python (Flask)** and **SQLite**. Designed to automate student housing with intelligent matching, real-time warden management, and a seamless student portal.

---

## 🤖 **AI-Driven Features**
This project features an **Intelligent Allocation Engine** that replaces manual placement. The AI considers multiple factors to find the perfect room:
- **Gender Segregation**: Strictly assigned to boys-only or girls-only hostels.
- **Preference Matching**: Weights for AC/Non-AC, Floor, and Room Type (Single/Double/Triple).
- **Smart Grouping**: Prioritizes grouping students from the **same branch/stream** and **similar eating preferences** (Veg/Non-Veg) to foster better community living.
- **Capacity Management**: Real-time bed tracking with an automated waiting list for overflow.

---

## 🛡️ **Warden Side Features**
A dedicated management suite for staff (`/auth/warden-login`):
- **AI Auto-Allocation**: Single-click button to intelligently assign all unallocated students.
- **Hostel & Room CRUD**: Full power to add, edit, or delete buildings, floors, and rooms.
- **Active Assignment List**: Track every student's location and vacate rooms with one click.
- **Complaint Resolution**: View student issues, update statuses (In Progress/Resolved), and notify students automatically.
- **Data Export**: One-click **CSV Download** of all allocated student data for administrative reports.

---

## 🎓 **Student Side Features**
A modern dashboard for residents:
- **Smart Registration**: Capture academic, personal, and preference data.
- **Preference Portal**: Select building, room type, and lifestyle preferences.
- **Real-Time Notifications**: Get notified instantly when you are allocated a room or when your complaint state changes.
- **Profile & Complaints**: Raise and track maintenance issues directly from the portal.

---

## 🛠️ **Installation & Setup**

### 1. Prerequisites
- Python 3.8+ installed.

### 2. Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Admin Credentials
```bash
python create_admin.py --email admin@hostel.com --password admin123 --name "Chief Warden"
```

### 5. Run the Application
```bash
gunicorn "app:create_app()" 
# or for development: python app.py
```

---

## 🌍 **Deployment Ready**
This repository is configured for immediate deployment to **Render.com** or **Vercel**:
- Includes `Procfile` for Gunicorn pairing.
- Environment variable support for `SECRET_KEY` and `FLASK_CONFIG`.
- Standard `requirements.txt` for fast build cycles.

---

## 🔑 **Default Warden Access**
- **Portal**: [https://your-app-url.onrender.com/auth/warden-login](https://your-app-url.onrender.com/auth/warden-login)
- **ID**: `admin@hostel.com`
- **Pass**: `admin123`

---
*Created with ❤️ for efficient campus housing management.*