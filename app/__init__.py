from flask import Flask
from config.config import Config

def create_app(config_class=Config):
    """Application factory for Rydeon Vehicle Rental System."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register blueprints
    from app.routes.frontend import frontend_bp
    app.register_blueprint(frontend_bp)

    return app
