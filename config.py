"""
Application Configuration
-------------------------
Centralised configuration for the Hostel Allocation System.
Reads sensitive values from environment variables where possible.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hostel-alloc-dev-secret-key-change-me')

    # SQLite for development; swap the URI for PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'hostel.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-WTF CSRF
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# Quick look-up dict
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}