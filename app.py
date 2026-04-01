"""
Hostel Allocation System – Main Application
--------------------------------------------
Entry point for the Flask application.
"""

import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from models import db, User
from config import config_by_name


def create_app(config_name=None):
    """Application factory."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Ensure instance folder exists (for SQLite)
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

    # Initialise extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.admin import warden_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(warden_bp)

    # Root redirect
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('warden.dashboard'))
            return redirect(url_for('student.dashboard'))
        return redirect(url_for('auth.login'))

    # Create tables on first request (development convenience)
    with app.app_context():
        db.create_all()

    return app


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)