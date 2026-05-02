"""
data_server/config.py — Environment-based configuration for data_server
Supports .env file loading via python-dotenv
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Database
    MARIADB_HOST = os.getenv("MARIADB_HOST", "localhost")
    MARIADB_PORT = int(os.getenv("MARIADB_PORT", 3306))
    MARIADB_USER = os.getenv("MARIADB_USER", "dobot_user")
    MARIADB_PASSWORD = os.getenv("MARIADB_PASSWORD", "")
    MARIADB_DATABASE = os.getenv("MARIADB_DATABASE", "dobot_hub")
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MARIADB_USER}:{MARIADB_PASSWORD}@"
        f"{MARIADB_HOST}:{MARIADB_PORT}/{MARIADB_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Auth & JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "jwt-secret-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRY = timedelta(hours=24)
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5000,http://localhost:8080").split(",")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "data_server.log")
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5001))
    
    # Collaboration
    LOCK_TTL_SECONDS = int(os.getenv("LOCK_TTL_SECONDS", 300))
    PRESENCE_TTL_SECONDS = int(os.getenv("PRESENCE_TTL_SECONDS", 60))
    EVENT_RETENTION_DAYS = int(os.getenv("EVENT_RETENTION_DAYS", 30))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    MARIADB_DATABASE = os.getenv("MARIADB_DATABASE", "dobot_hub_dev")


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_EXPIRY = timedelta(minutes=1)


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # In production, all secrets should come from environment
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET = os.getenv("JWT_SECRET")
    MARIADB_PASSWORD = os.getenv("MARIADB_PASSWORD")
    
    def __init__(self):
        super().__init__()
        # Validate required environment variables
        if not all([self.SECRET_KEY, self.JWT_SECRET, self.MARIADB_PASSWORD]):
            raise ValueError("Required environment variables missing in production: "
                           "SECRET_KEY, JWT_SECRET, MARIADB_PASSWORD")


# Load config based on FLASK_ENV
def get_config():
    """Factory function to load appropriate config"""
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()


config = get_config()
