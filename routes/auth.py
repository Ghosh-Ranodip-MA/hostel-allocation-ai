"""
Authentication Routes
---------------------
Login, logout, registration, and preference selection.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Hostel
from forms import LoginForm, RegistrationForm, PreferencesForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Student self-registration."""
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower().strip(),
            name=form.name.data.strip(),
            roll_number=form.roll_number.data.strip(),
            year=form.year.data,
            branch=form.branch.data.strip(),
            gender=form.gender.data,
            parent_phone=form.parent_phone.data.strip(),
            address=form.address.data.strip(),
            eating_preference=form.eating_preference.data,
            role='student',
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in and set your hostel preferences.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login for students."""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('warden.dashboard'))
        return redirect(url_for('student.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if user.role == 'admin':
                return redirect(next_page or url_for('warden.dashboard'))
            return redirect(next_page or url_for('student.dashboard'))
        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/warden-login', methods=['GET', 'POST'])
def warden_login():
    """Security entrance for Wardens."""
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('warden.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data) and user.role == 'admin':
            login_user(user, remember=form.remember.data)
            return redirect(url_for('warden.dashboard'))
        elif user and user.role != 'admin':
            flash('Access denied. Please use the student portal.', 'warning')
        else:
            flash('Invalid credentials.', 'danger')

    return render_template('auth/warden_login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Student selects hostel & room preferences."""
    if current_user.role != 'student':
        return redirect(url_for('warden.dashboard'))

    form = PreferencesForm()
    # Only show hostels matching student's gender
    gender_map = {'male': 'boys', 'female': 'girls'}
    hostels = Hostel.query.filter_by(gender_type=gender_map.get(current_user.gender, 'boys')).all()
    form.preferred_hostel_id.choices = [(h.id, h.name) for h in hostels]

    if form.validate_on_submit():
        current_user.preferred_hostel_id = form.preferred_hostel_id.data
        current_user.preferred_room_type = form.preferred_room_type.data
        current_user.preferred_ac = form.preferred_ac.data == '1'
        current_user.preferred_floor = form.preferred_floor.data
        current_user.eating_preference = form.eating_preference.data
        db.session.commit()
        flash('Preferences saved successfully!', 'success')
        return redirect(url_for('student.dashboard'))

    # Pre-fill if already set
    if current_user.preferred_hostel_id:
        form.preferred_hostel_id.data = current_user.preferred_hostel_id
    if current_user.preferred_room_type:
        form.preferred_room_type.data = current_user.preferred_room_type
    if current_user.preferred_ac is not None:
        form.preferred_ac.data = '1' if current_user.preferred_ac else '0'
    if current_user.preferred_floor is not None:
        form.preferred_floor.data = current_user.preferred_floor
    if current_user.eating_preference:
        form.eating_preference.data = current_user.eating_preference

    return render_template('auth/preferences.html', form=form)