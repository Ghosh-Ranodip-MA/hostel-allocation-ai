"""
Student Routes
--------------
Dashboard, complaints, notifications, and profile management.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Notification, Complaint, Allocation, Room, Hostel, WaitingList
from forms import ComplaintForm, ProfileForm
from functools import wraps

student_bp = Blueprint('student', __name__, url_prefix='/student')


def student_required(f):
    """Decorator – allow only students."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ---- Dashboard -----------------------------------------------------------
@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    """Main student view – allocation status or waiting rank."""
    allocation = current_user.active_allocation
    room = None
    hostel = None
    if allocation:
        room = Room.query.get(allocation.room_id)
        hostel = Hostel.query.get(room.hostel_id) if room else None

    # Fetch recent complaints and notifications for the user
    # This prevents 'Complaint' UndefinedErrors in Jinja
    recent_complaints = Complaint.query.filter_by(student_id=current_user.id).order_by(Complaint.raised_at.desc()).limit(3).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    waiting = WaitingList.query.filter_by(student_id=current_user.id, status='waiting').first()

    return render_template(
        'student/dashboard.html',
        allocation=allocation,
        room=room,
        hostel=hostel,
        waiting=waiting,
        unread_count=unread_count,
        recent_complaints=recent_complaints
    )


# ---- Complaints ----------------------------------------------------------
@student_bp.route('/complaints', methods=['GET', 'POST'])
@login_required
@student_required
def complaints():
    """View own complaints and raise a new one."""
    form = ComplaintForm()
    if form.validate_on_submit():
        alloc = current_user.active_allocation
        complaint = Complaint(
            student_id=current_user.id,
            room_id=alloc.room_id if alloc else None,
            description=form.description.data.strip(),
        )
        db.session.add(complaint)
        db.session.commit()
        flash('Complaint submitted successfully.', 'success')
        return redirect(url_for('student.complaints'))

    my_complaints = Complaint.query.filter_by(student_id=current_user.id).order_by(Complaint.raised_at.desc()).all()
    return render_template('student/complaints.html', form=form, complaints=my_complaints)


# ---- Notifications -------------------------------------------------------
@student_bp.route('/notifications')
@login_required
@student_required
def notifications():
    """View all notifications."""
    notes = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('student/notifications.html', notifications=notes)


@student_bp.route('/notifications/read/<int:nid>')
@login_required
@student_required
def mark_read(nid):
    """Mark a single notification as read."""
    note = Notification.query.get_or_404(nid)
    if note.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('student.notifications'))
    note.is_read = True
    db.session.commit()
    return redirect(url_for('student.notifications'))


@student_bp.route('/notifications/read-all')
@login_required
@student_required
def mark_all_read():
    """Mark all notifications as read."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('student.notifications'))


# ---- Profile -------------------------------------------------------------
@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    """Update contact details only."""
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.parent_phone = form.parent_phone.data.strip()
        current_user.address = form.address.data.strip()
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('student.profile'))

    # Pre-fill
    form.parent_phone.data = current_user.parent_phone
    form.address.data = current_user.address

    return render_template('student/profile.html', form=form)