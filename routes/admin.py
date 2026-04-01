"""
Admin Routes
------------
Full admin panel: dashboard, unallocated students, waiting list,
room/hostel CRUD, allocation, vacation, and complaint management.
"""

import csv
import io
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from models import (
    db, User, Hostel, Room, Allocation, WaitingList, Complaint, Notification,
)
from forms import HostelForm, RoomForm, ComplaintStatusForm
from functools import wraps

warden_bp = Blueprint('warden', __name__, url_prefix='/warden')


def admin_required(f):
    """Decorator – allow only admins."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ---- Helpers -------------------------------------------------------------
def _notify(user_id, message):
    """Create an in-app notification."""
    n = Notification(user_id=user_id, message=message)
    db.session.add(n)


def _gender_map(gender):
    return 'boys' if gender == 'male' else 'girls'


# ---- Dashboard -----------------------------------------------------------
@warden_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin overview with key stats."""
    total_students = User.query.filter_by(role='student').count()
    allocated = User.query.filter_by(role='student', is_allocated=True).count()
    unallocated = User.query.filter_by(role='student', is_allocated=False).count()
    waiting = WaitingList.query.filter_by(status='waiting').count()
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter(Room.available_beds > 0, Room.status == 'available').count()
    open_complaints = Complaint.query.filter(Complaint.status != 'resolved').count()

    # Fetch top waiting list students for the dashboard snapshot
    recent_waitlist = WaitingList.query.filter_by(status='waiting').order_by(WaitingList.rank.asc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        allocated=allocated,
        unallocated=unallocated,
        waiting=waiting,
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        open_complaints=open_complaints,
        recent_waitlist=recent_waitlist
    )


@warden_bp.route('/auto-allocate', methods=['POST'])
@login_required
@admin_required
def auto_allocate():
    """AI Auto-allocation logic."""
    unallocated_students = User.query.filter_by(role='student', is_allocated=False).all()
    
    if not unallocated_students:
        flash('No unallocated students found.', 'info')
        return redirect(url_for('warden.dashboard'))
    
    allocations_count = 0
    for student in unallocated_students:
        gender_type = 'boys' if student.gender == 'male' else 'girls'
        
        # 1. Broadly identify available rooms for the correct gender
        available_rooms = Room.query.join(Hostel).filter(
            Hostel.gender_type == gender_type,
            Room.status == 'available',
            Room.available_beds > 0
        ).all()
        
        if not available_rooms:
            continue

        # 2. Score rooms for this student
        scored_rooms = []
        for room in available_rooms:
            score = 0
            # Preference matches
            if student.preferred_ac == room.ac: score += 10
            if student.preferred_room_type == room.room_type: score += 5
            if student.preferred_hostel_id == room.hostel_id: score += 3
            
            # Smart grouping Match (Branch)
            # Check others in the room
            others_in_room = Allocation.query.filter_by(room_id=room.id, status='active').all()
            for other_alloc in others_in_room:
                other_student = User.query.get(other_alloc.student_id)
                if other_student:
                    if other_student.branch == student.branch: score += 8
                    if other_student.eating_preference == student.eating_preference: score += 5
            
            scored_rooms.append((score, room))
        
        # Sort by score descending and pick best
        scored_rooms.sort(key=lambda x: x[0], reverse=True)
        best_room = scored_rooms[0][1]
        
        # 3. Perform allocation
        alloc = Allocation(student_id=student.id, room_id=best_room.id)
        student.is_allocated = True
        best_room.available_beds -= 1
        if best_room.available_beds == 0:
            best_room.status = 'full'
        
        # Clean up waiting list
        WaitingList.query.filter_by(student_id=student.id).delete()
        
        _notify(student.id, f'AI Auto-Allocation: You have been assigned to Room {best_room.room_number}.')
        db.session.add(alloc)
        allocations_count += 1
        db.session.commit() # Commit each to update available_beds for next loop
            
    flash(f'AI Auto-Allocation completed. {allocations_count} students allocated.', 'success')
    return redirect(url_for('warden.dashboard'))


# ---- Unallocated Students ------------------------------------------------
@warden_bp.route('/unallocated')
@login_required
@admin_required
def unallocated():
    """List students who are not yet allocated and not on waiting list."""
    q = User.query.filter_by(role='student', is_allocated=False)

    # Exclude students already on waiting list
    waiting_ids = [w.student_id for w in WaitingList.query.filter_by(status='waiting').all()]
    if waiting_ids:
        q = q.filter(~User.id.in_(waiting_ids))

    # Filters
    gender = request.args.get('gender')
    year = request.args.get('year')
    branch = request.args.get('branch')
    if gender:
        q = q.filter_by(gender=gender)
    if year:
        q = q.filter_by(year=year)
    if branch:
        q = q.filter(User.branch.ilike(f'%{branch}%'))

    students = q.order_by(User.id.asc()).all()
    return render_template('admin/unallocated.html', students=students)


# ---- Allocated Students --------------------------------------------------
@warden_bp.route('/allocated')
@login_required
@admin_required
def allocated_students():
    """List students with active allocations."""
    allocations = (
        db.session.query(Allocation, User, Room, Hostel)
        .join(User, Allocation.student_id == User.id)
        .join(Room, Allocation.room_id == Room.id)
        .join(Hostel, Room.hostel_id == Hostel.id)
        .filter(Allocation.status == 'active')
        .order_by(Allocation.allocated_at.desc())
        .all()
    )
    return render_template('admin/allocated_students.html', allocations=allocations)


@warden_bp.route('/download-allocated-csv')
@login_required
@admin_required
def download_allocated_csv():
    """Generate and return a CSV of all active allocations."""
    allocations = (
        db.session.query(Allocation, User, Room, Hostel)
        .join(User, Allocation.student_id == User.id)
        .join(Room, Allocation.room_id == Room.id)
        .join(Hostel, Room.hostel_id == Hostel.id)
        .filter(Allocation.status == 'active')
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Student Name', 'Roll Number', 'Gender', 'Branch', 'Year', 'Hostel', 'Room Number', 'Room Type', 'AC', 'Allocated Date'])
    
    # Data
    for alloc, user, room, hostel in allocations:
        writer.writerow([
            user.name,
            user.roll_number,
            user.gender,
            user.branch,
            user.year,
            hostel.name,
            room.room_number,
            room.room_type,
            'Yes' if room.ac else 'No',
            alloc.allocated_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=allocated_students.csv"}
    )


# ---- Allocate a student to a room ----------------------------------------
@warden_bp.route('/allocate/<int:student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def allocate(student_id):
    """Show matching rooms and allocate student."""
    student = User.query.get_or_404(student_id)
    if student.is_allocated:
        flash('Student is already allocated.', 'warning')
        return redirect(url_for('warden.unallocated'))

    # Build a query of available rooms matching the student's gender
    gender_type = _gender_map(student.gender)
    rooms_q = (
        Room.query
        .join(Hostel)
        .filter(
            Hostel.gender_type == gender_type,
            Room.status == 'available',
            Room.available_beds > 0,
        )
    )

    # Apply preference filters if set
    if student.preferred_ac is not None:
        rooms_q = rooms_q.filter(Room.ac == student.preferred_ac)
    if student.preferred_room_type:
        rooms_q = rooms_q.filter(Room.room_type == student.preferred_room_type)
    if student.preferred_hostel_id:
        rooms_q = rooms_q.filter(Room.hostel_id == student.preferred_hostel_id)
    if student.preferred_floor is not None:
        rooms_q = rooms_q.filter(Room.floor == student.preferred_floor)

    # Also provide "all matching" rooms (gender only) for admin flexibility
    all_rooms_q = (
        Room.query
        .join(Hostel)
        .filter(
            Hostel.gender_type == gender_type,
            Room.status == 'available',
            Room.available_beds > 0,
        )
    )

    preferred_rooms = rooms_q.all()
    all_rooms = all_rooms_q.all()

    if request.method == 'POST':
        room_id = request.form.get('room_id', type=int)
        room = Room.query.get(room_id)
        if not room or room.available_beds <= 0 or room.status != 'available':
            flash('Invalid or full room selected.', 'danger')
            return redirect(url_for('warden.allocate', student_id=student_id))

        # Create allocation
        alloc = Allocation(student_id=student.id, room_id=room.id)
        student.is_allocated = True
        room.available_beds -= 1
        if room.available_beds == 0:
            room.status = 'full'

        # Remove from waiting list if present
        wl = WaitingList.query.filter_by(student_id=student.id, status='waiting').first()
        if wl:
            wl.status = 'allocated'

        _notify(student.id, f'You have been allocated to Room {room.room_number} in {room.hostel.name}.')
        db.session.add(alloc)
        db.session.commit()

        flash(f'{student.name} allocated to Room {room.room_number}.', 'success')
        return redirect(url_for('warden.unallocated'))

    return render_template(
        'admin/allocate.html',
        student=student,
        preferred_rooms=preferred_rooms,
        all_rooms=all_rooms,
    )


# ---- Vacate a student ----------------------------------------------------
@warden_bp.route('/vacate/<int:allocation_id>', methods=['POST'])
@login_required
@admin_required
def vacate(allocation_id):
    """Vacate a student from their room."""
    alloc = Allocation.query.get_or_404(allocation_id)
    if alloc.status != 'active':
        flash('Allocation is not active.', 'warning')
        return redirect(url_for('warden.allocated_students'))

    alloc.status = 'vacated'
    student = User.query.get(alloc.student_id)
    student.is_allocated = False

    room = Room.query.get(alloc.room_id)
    room.available_beds += 1
    if room.status == 'full':
        room.status = 'available'

    _notify(student.id, f'You have been vacated from Room {room.room_number}.')
    db.session.commit()

    flash(f'{student.name} vacated from Room {room.room_number}.', 'success')
    return redirect(url_for('warden.allocated_students'))


# ---- Waiting List ---------------------------------------------------------
@warden_bp.route('/waiting-list')
@login_required
@admin_required
def waiting_list():
    """View waiting list, ordered by rank/date."""
    entries = (
        db.session.query(WaitingList, User)
        .join(User, WaitingList.student_id == User.id)
        .filter(WaitingList.status == 'waiting')
        .order_by(WaitingList.rank.asc(), WaitingList.added_at.asc())
        .all()
    )
    return render_template('admin/waiting_list.html', entries=entries)


@warden_bp.route('/add-to-waiting/<int:student_id>', methods=['POST'])
@login_required
@admin_required
def add_to_waiting(student_id):
    """Add an unallocated student to the waiting list."""
    student = User.query.get_or_404(student_id)
    if student.is_allocated:
        flash('Student is already allocated.', 'warning')
        return redirect(url_for('warden.unallocated'))

    existing = WaitingList.query.filter_by(student_id=student.id, status='waiting').first()
    if existing:
        flash('Student is already on the waiting list.', 'info')
        return redirect(url_for('warden.unallocated'))

    # Determine next rank
    max_rank = db.session.query(db.func.max(WaitingList.rank)).filter_by(status='waiting').scalar() or 0
    wl = WaitingList(student_id=student.id, rank=max_rank + 1)
    db.session.add(wl)
    _notify(student.id, 'You have been added to the hostel waiting list.')
    db.session.commit()

    flash(f'{student.name} added to waiting list at rank {max_rank + 1}.', 'success')
    return redirect(url_for('warden.unallocated'))


# ---- Hostel CRUD ----------------------------------------------------------
@warden_bp.route('/hostels')
@login_required
@admin_required
def hostels():
    all_hostels = Hostel.query.order_by(Hostel.name).all()
    return render_template('admin/hostels.html', hostels=all_hostels)


@warden_bp.route('/hostels/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_hostel():
    form = HostelForm()
    if form.validate_on_submit():
        h = Hostel(
            name=form.name.data.strip(),
            address=form.address.data.strip() if form.address.data else '',
            gender_type=form.gender_type.data,
            total_capacity=form.total_capacity.data,
            warden_name=form.warden_name.data.strip() if form.warden_name.data else '',
        )
        db.session.add(h)
        db.session.commit()
        flash(f'Hostel "{h.name}" created.', 'success')
        return redirect(url_for('warden.hostels'))
    return render_template('admin/hostel_form.html', form=form, title='Add Hostel')


@warden_bp.route('/hostels/edit/<int:hid>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_hostel(hid):
    hostel = Hostel.query.get_or_404(hid)
    form = HostelForm(obj=hostel)
    if form.validate_on_submit():
        hostel.name = form.name.data.strip()
        hostel.address = form.address.data.strip() if form.address.data else ''
        hostel.gender_type = form.gender_type.data
        hostel.total_capacity = form.total_capacity.data
        hostel.warden_name = form.warden_name.data.strip() if form.warden_name.data else ''
        db.session.commit()
        flash('Hostel updated.', 'success')
        return redirect(url_for('warden.hostels'))
    return render_template('admin/hostel_form.html', form=form, title='Edit Hostel')


@warden_bp.route('/hostels/delete/<int:hid>', methods=['POST'])
@login_required
@admin_required
def delete_hostel(hid):
    hostel = Hostel.query.get_or_404(hid)
    db.session.delete(hostel)
    db.session.commit()
    flash(f'Hostel "{hostel.name}" deleted.', 'success')
    return redirect(url_for('warden.hostels'))


# ---- Room CRUD ------------------------------------------------------------
@warden_bp.route('/rooms')
@login_required
@admin_required
def rooms():
    hostel_filter = request.args.get('hostel_id', type=int)
    q = Room.query
    if hostel_filter:
        q = q.filter_by(hostel_id=hostel_filter)
    all_rooms = q.order_by(Room.hostel_id, Room.room_number).all()
    all_hostels = Hostel.query.order_by(Hostel.name).all()
    return render_template('admin/rooms.html', rooms=all_rooms, hostels=all_hostels, hostel_filter=hostel_filter)


@warden_bp.route('/rooms/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_room():
    form = RoomForm()
    form.hostel_id.choices = [(h.id, h.name) for h in Hostel.query.order_by(Hostel.name).all()]
    if form.validate_on_submit():
        r = Room(
            hostel_id=form.hostel_id.data,
            room_number=form.room_number.data.strip(),
            floor=form.floor.data,
            capacity=form.capacity.data,
            available_beds=form.capacity.data,   # new room → all beds free
            room_type=form.room_type.data,
            ac=(form.ac.data == '1'),
            status=form.status.data,
        )
        db.session.add(r)
        db.session.commit()
        flash(f'Room {r.room_number} created.', 'success')
        return redirect(url_for('warden.rooms'))
    return render_template('admin/room_form.html', form=form, title='Add Room')


@warden_bp.route('/rooms/edit/<int:rid>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_room(rid):
    room = Room.query.get_or_404(rid)
    form = RoomForm(obj=room)
    form.hostel_id.choices = [(h.id, h.name) for h in Hostel.query.order_by(Hostel.name).all()]
    if request.method == 'GET':
        form.ac.data = '1' if room.ac else '0'
    if form.validate_on_submit():
        room.hostel_id = form.hostel_id.data
        room.room_number = form.room_number.data.strip()
        room.floor = form.floor.data
        room.capacity = form.capacity.data
        room.room_type = form.room_type.data
        room.ac = (form.ac.data == '1')
        room.status = form.status.data
        db.session.commit()
        flash('Room updated.', 'success')
        return redirect(url_for('warden.rooms'))
    return render_template('admin/room_form.html', form=form, title='Edit Room')


@warden_bp.route('/rooms/delete/<int:rid>', methods=['POST'])
@login_required
@admin_required
def delete_room(rid):
    room = Room.query.get_or_404(rid)
    db.session.delete(room)
    db.session.commit()
    flash(f'Room {room.room_number} deleted.', 'success')
    return redirect(url_for('warden.rooms'))


# ---- Complaints -----------------------------------------------------------
@warden_bp.route('/complaints')
@login_required
@admin_required
def complaints():
    status_filter = request.args.get('status')
    q = Complaint.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    all_complaints = (
        q.join(User, Complaint.student_id == User.id)
        .add_columns(User.name, User.roll_number)
        .order_by(Complaint.raised_at.desc())
        .all()
    )
    return render_template('admin/complaints.html', complaints=all_complaints, status_filter=status_filter)


@warden_bp.route('/complaints/<int:cid>/update', methods=['POST'])
@login_required
@admin_required
def update_complaint(cid):
    complaint = Complaint.query.get_or_404(cid)
    new_status = request.form.get('status')
    if new_status in ('open', 'in_progress', 'resolved'):
        old_status = complaint.status
        complaint.status = new_status
        if new_status == 'resolved':
            complaint.resolved_at = datetime.now(timezone.utc)
        _notify(
            complaint.student_id,
            f'Your complaint (#{complaint.id}) status changed from {old_status} to {new_status}.',
        )
        db.session.commit()
        flash('Complaint status updated.', 'success')
    else:
        flash('Invalid status.', 'danger')
    return redirect(url_for('warden.complaints'))


# ---- API: rooms for allocation modal (JSON) --------------------------------
@warden_bp.route('/api/rooms/<int:student_id>')
@login_required
@admin_required
def api_rooms(student_id):
    """Return matching rooms as JSON for AJAX allocation modal."""
    student = User.query.get_or_404(student_id)
    gender_type = _gender_map(student.gender)
    rooms = (
        Room.query.join(Hostel)
        .filter(Hostel.gender_type == gender_type, Room.status == 'available', Room.available_beds > 0)
        .all()
    )
    return jsonify([
        {
            'id': r.id,
            'room_number': r.room_number,
            'hostel': r.hostel.name,
            'floor': r.floor,
            'room_type': r.room_type,
            'ac': r.ac,
            'available_beds': r.available_beds,
        }
        for r in rooms
    ])