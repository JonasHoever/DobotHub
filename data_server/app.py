"""
data_server/app.py — Main Flask application for data_server
Usage: python app.py
"""

import os
import logging
from flask import Flask
from flask_cors import CORS
from config import config
from models import db

def create_app(config_name: str = None):
    """Application factory"""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    
    app = Flask(__name__)
    
    # Load config
    if config_name == "production":
        from config import ProductionConfig
        app.config.from_object(ProductionConfig)
    elif config_name == "testing":
        from config import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        from config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"])
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.projects import projects_bp
    from routes.collab import collab_bp
    
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(collab_bp, url_prefix="/api/projects")
    
    # Health check endpoint
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200
    
    # Favicon endpoint (prevents 404 errors)
    @app.get("/favicon.ico")
    def favicon():
        return "", 204  # No Content
    
    # Initialize database tables
    with app.app_context():
        db.create_all()
        app.logger.info("Database initialized")
    
    return app


def setup_logging(app):
    """Configure application logging"""
    log_level = getattr(logging, app.config["LOG_LEVEL"])
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler
    if app.config["LOG_FILE"]:
        file_handler = logging.FileHandler(app.config["LOG_FILE"])
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_formatter)
        app.logger.addHandler(file_handler)
    
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)


if __name__ == "__main__":
    app = create_app()
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"]
    )
