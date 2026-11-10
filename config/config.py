import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base application configuration loaded from environment variables."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'rydeon-dev-secret-key-2026')
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

    # Session Security Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # MySQL Database Configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_NAME = os.environ.get('DB_NAME', 'vehicle_rental_system')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_POOL_NAME = os.environ.get('DB_POOL_NAME', 'rydeon_pool')
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 5))

class TestingConfig(Config):
    """Configuration for testing suites."""
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    DB_NAME = os.environ.get('TEST_DB_NAME', 'vehicle_rental_system')
