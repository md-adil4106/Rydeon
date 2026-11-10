"""
Rydeon - Application Factory & Blueprint Registration
------------------------------------------------------
Configures the Flask WSGI instance, error handlers, and route blueprints.
"""

from flask import Flask, render_template, jsonify, request
import mysql.connector
from config.config import Config

def create_app(config_class=Config):
    """Initializes and returns a configured Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register blueprints
    from app.routes.frontend import frontend_bp
    app.register_blueprint(frontend_bp)

    # Centralized Error Handlers
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
