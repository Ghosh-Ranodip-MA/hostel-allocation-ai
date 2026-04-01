"""
Flask-WTF Forms
---------------
All form definitions with validation for the Hostel Allocation System.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SelectField, BooleanField,
    TextAreaField, IntegerField, SubmitField, HiddenField,
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Optional, ValidationError,
)
from models import User


# ---------------------------------------------------------------------------
# Auth Forms
# ---------------------------------------------------------------------------
class RegistrationForm(FlaskForm):
    """Student self-registration form."""
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')],
    )
    roll_number = StringField('Roll Number', validators=[DataRequired(), Length(max=30)])
    year = SelectField(
        'Year',
        choices=[('', '-- Select Year --'), ('1st', '1st Year'), ('2nd', '2nd Year'),
                 ('3rd', '3rd Year'), ('4th', '4th Year')],
        validators=[DataRequired()],
    )
    branch = StringField('Branch', validators=[DataRequired(), Length(max=60)])
    gender = SelectField(
        'Gender',
        choices=[('', '-- Select Gender --'), ('male', 'Male'), ('female', 'Female')],
        validators=[DataRequired()],
    )
    parent_phone = StringField('Parent Phone', validators=[DataRequired(), Length(max=20)])
    eating_preference = SelectField(
        'Eating Preference',
        choices=[('', '-- Select Preference --'), ('Veg', 'Vegetarian'), ('Non-Veg', 'Non-Vegetarian')],
        validators=[DataRequired()],
    )
    address = TextAreaField('Address', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('That email is already registered.')

    def validate_roll_number(self, field):
        if User.query.filter_by(roll_number=field.data.strip()).first():
            raise ValidationError('That roll number is already registered.')


class LoginForm(FlaskForm):
    """Login form for students and admins."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------
class PreferencesForm(FlaskForm):
    """Student selects hostel & room preferences after registration."""
    preferred_hostel_id = SelectField('Preferred Hostel', coerce=int, validators=[DataRequired()])
    preferred_room_type = SelectField(
        'Room Type',
        choices=[('single', 'Single'), ('double', 'Double Shared'), ('triple', 'Triple Shared')],
        validators=[DataRequired()],
    )
    preferred_ac = SelectField(
        'AC Preference',
        choices=[('1', 'AC'), ('0', 'Non-AC')],
        validators=[DataRequired()],
    )
    eating_preference = SelectField(
        'Eating Preference',
        choices=[('Veg', 'Vegetarian'), ('Non-Veg', 'Non-Vegetarian')],
        validators=[DataRequired()],
    )
    preferred_floor = IntegerField('Preferred Floor (optional)', validators=[Optional()])
    submit = SubmitField('Save Preferences')


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
class ProfileForm(FlaskForm):
    """Students can update contact details only."""
    parent_phone = StringField('Parent Phone', validators=[DataRequired(), Length(max=20)])
    address = TextAreaField('Address', validators=[DataRequired()])
    submit = SubmitField('Update Profile')


# ---------------------------------------------------------------------------
# Complaint
# ---------------------------------------------------------------------------
class ComplaintForm(FlaskForm):
    """Raise a new complaint."""
    description = TextAreaField('Describe your complaint', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Submit Complaint')


# ---------------------------------------------------------------------------
# Admin: Hostel CRUD
# ---------------------------------------------------------------------------
class HostelForm(FlaskForm):
    name = StringField('Hostel Name', validators=[DataRequired(), Length(max=100)])
    address = StringField('Address', validators=[Optional(), Length(max=200)])
    gender_type = SelectField(
        'Gender Type',
        choices=[('boys', 'Boys'), ('girls', 'Girls')],
        validators=[DataRequired()],
    )
    total_capacity = IntegerField('Total Capacity', validators=[DataRequired()])
    warden_name = StringField('Warden Name', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Save Hostel')


# ---------------------------------------------------------------------------
# Admin: Room CRUD
# ---------------------------------------------------------------------------
class RoomForm(FlaskForm):
    hostel_id = SelectField('Hostel', coerce=int, validators=[DataRequired()])
    room_number = StringField('Room Number', validators=[DataRequired(), Length(max=20)])
    floor = IntegerField('Floor', validators=[DataRequired()])
    capacity = IntegerField('Capacity (beds)', validators=[DataRequired()])
    room_type = SelectField(
        'Room Type',
        choices=[('single', 'Single'), ('double', 'Double Shared'), ('triple', 'Triple Shared')],
        validators=[DataRequired()],
    )
    ac = SelectField('AC', choices=[('1', 'AC'), ('0', 'Non-AC')], validators=[DataRequired()])
    status = SelectField(
        'Status',
        choices=[('available', 'Available'), ('full', 'Full'), ('maintenance', 'Under Maintenance')],
        validators=[DataRequired()],
    )
    submit = SubmitField('Save Room')


# ---------------------------------------------------------------------------
# Admin: Complaint Status Update
# ---------------------------------------------------------------------------
class ComplaintStatusForm(FlaskForm):
    status = SelectField(
        'Status',
        choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('resolved', 'Resolved')],
        validators=[DataRequired()],
    )
    submit = SubmitField('Update Status')