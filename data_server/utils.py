"""
data_server/utils.py — Shared utilities (JWT, UUIDs, auth checks)
"""

import jwt
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from models import db, Session, User


def generate_uuid() -> str:
    """Generate a UUID4 string"""
    return str(uuid.uuid4())


def generate_token(user_id: str, app_config) -> str:
    """Generate a JWT token"""
    payload = {
        "user_id": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + app_config.JWT_EXPIRY,
    }
    return jwt.encode(payload, app_config.JWT_SECRET, algorithm=app_config.JWT_ALGORITHM)


def verify_token(token: str, app_config) -> dict or None:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, app_config.JWT_SECRET, algorithms=[app_config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Decorator to require valid JWT token in Authorization header"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing Authorization header"}), 401
        
        token = auth_header.split(" ", 1)[1]
        payload = verify_token(token, current_app.config)
        
        if not payload:
            return jsonify({"error": "Token invalid or expired"}), 401
        
        # Verify session is still active
        try:
            session = Session.query.filter_by(token=token, is_active=True).first()
            if not session:
                return jsonify({"error": "Session not found or inactive"}), 401
            
            # Update last_activity
            session.last_activity = datetime.utcnow()
            db.session.commit()
            
            # Pass user_id and session_id to the route handler
            request.user_id = payload["user_id"]
            request.session_id = session.id
            request.session = session
        except Exception as e:
            current_app.logger.error(f"Auth check error: {e}")
            return jsonify({"error": "Auth check failed"}), 500
        
        return f(*args, **kwargs)
    
    return decorated_function


def hash_password(password: str) -> str:
    """Hash password using werkzeug (should use bcrypt in production)"""
    from werkzeug.security import generate_password_hash
    return generate_password_hash(password, method='pbkdf2:sha256')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""


def compute_checksum(content_dict: dict) -> str:
    """Compute SHA256 checksum of content for conflict detection"""
    json_str = json.dumps(content_dict, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode()).hexdigest()
    from werkzeug.security import check_password_hash
    return check_password_hash(password_hash, password)
