"""
Rydeon - Application Factory & Blueprint Registration
------------------------------------------------------
Configures the Flask WSGI instance, session cookies, error handlers,
CSRF helpers, and modular route blueprints.
"""

from flask import Flask, render_template, jsonify, request
import mysql.connector
from config.config import Config
from app.services.csrf import generate_csrf_token

def create_app(config_class=Config):
    """Initializes and returns a configured Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # CSRF Token Injection into all templates
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf_token)

    # Register blueprints
    from app.routes.frontend import frontend_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(frontend_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # Centralized Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Forbidden: Insufficient privileges", "status": 403}), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Resource not found", "status": 404}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Internal server error", "status": 500}), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(mysql.connector.Error)
    def database_error(error):
        app.logger.error(f"Database error encountered: {error}")
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Database connectivity error",
                "detail": str(error),
                "status": 503
            }), 503
        return render_template('errors/db_error.html', error=str(error)), 503

    return app
