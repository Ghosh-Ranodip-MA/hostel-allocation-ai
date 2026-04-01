"""
Database Models
---------------
All SQLAlchemy models for the Hostel Allocation System.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    """Student or Admin user."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='student')  # student | admin

    # Profile
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(30), unique=True, nullable=True)
    year = db.Column(db.String(10), nullable=True)        # 1st, 2nd, 3rd, 4th
    branch = db.Column(db.String(60), nullable=True)
    gender = db.Column(db.String(10), nullable=True)       # male | female
    parent_phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)

    # Allocation state
    is_allocated = db.Column(db.Boolean, default=False)

    # Preferences
    preferred_hostel_id = db.Column(db.Integer, db.ForeignKey('hostels.id'), nullable=True)
    preferred_room_type = db.Column(db.String(20), nullable=True)   # single | shared | triple
    preferred_ac = db.Column(db.Boolean, nullable=True)
    eating_preference = db.Column(db.String(20), nullable=True)     # Veg | Non-Veg
    preferred_floor = db.Column(db.Integer, nullable=True)

    # Relationships
    allocations = db.relationship('Allocation', backref='student', lazy='dynamic')
    complaints = db.relationship('Complaint', backref='student', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    waiting_entry = db.relationship('WaitingList', backref='student', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def active_allocation(self):
        """Return the latest active allocation, if any."""
        return self.allocations.filter_by(status='active').first()

    def __repr__(self):
        return f'<User {self.email}>'


# ---------------------------------------------------------------------------
# Hostel
# ---------------------------------------------------------------------------
class Hostel(db.Model):
    __tablename__ = 'hostels'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=True)
    gender_type = db.Column(db.String(10), nullable=False)  # boys | girls
    total_capacity = db.Column(db.Integer, nullable=False, default=0)
    warden_name = db.Column(db.String(100), nullable=True)

    rooms = db.relationship('Room', backref='hostel', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Hostel {self.name}>'


# ---------------------------------------------------------------------------
# Room
# ---------------------------------------------------------------------------
class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    hostel_id = db.Column(db.Integer, db.ForeignKey('hostels.id'), nullable=False)
    room_number = db.Column(db.String(20), nullable=False)
    floor = db.Column(db.Integer, nullable=False, default=0)
    capacity = db.Column(db.Integer, nullable=False, default=1)
    available_beds = db.Column(db.Integer, nullable=False, default=1)
    room_type = db.Column(db.String(10), nullable=False, default='single')  # single | shared
    ac = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(15), nullable=False, default='available')  # available | full | maintenance

    allocations = db.relationship('Allocation', backref='room', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('hostel_id', 'room_number', name='uq_hostel_room'),
    )

    def __repr__(self):
        return f'<Room {self.room_number} @ Hostel {self.hostel_id}>'


# ---------------------------------------------------------------------------
# Allocation
# ---------------------------------------------------------------------------
class Allocation(db.Model):
    __tablename__ = 'allocations'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    allocated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(10), nullable=False, default='active')  # active | vacated

    def __repr__(self):
        return f'<Allocation student={self.student_id} room={self.room_id}>'


# ---------------------------------------------------------------------------
# WaitingList
# ---------------------------------------------------------------------------
class WaitingList(db.Model):
    __tablename__ = 'waiting_list'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    rank = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(15), nullable=False, default='waiting')  # waiting | allocated

    def __repr__(self):
        return f'<WaitingList student={self.student_id} rank={self.rank}>'


# ---------------------------------------------------------------------------
# Complaint
# ---------------------------------------------------------------------------
class Complaint(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(15), nullable=False, default='open')  # open | in_progress | resolved
    raised_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Complaint {self.id} status={self.status}>'


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Notification {self.id} read={self.is_read}>'