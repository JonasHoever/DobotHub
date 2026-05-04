"""
data_server/routes/auth.py — Authentication endpoints (login, validate, logout)
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from models import db, User, Session
from utils import generate_uuid, generate_token, verify_token, hash_password, verify_password, require_auth

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    """
    POST /api/auth/register
    Register a new user
    """
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip()
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
        
    if db.session.query(User).filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409
        
    password_hash = hash_password(password)
    user = User(
        id=generate_uuid(),
        username=username,
        email=email if email else None,
        password_hash=password_hash,
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    
    current_app.logger.info(f"New user registered: {username}")
    
    return jsonify({
        "ok": True,
        "message": "User registered successfully",
        "user_id": user.id
    }), 201


@auth_bp.post("/login")
def login():
    """
    POST /api/auth/login
    Login with username/password
    Returns JWT token and session info
    """
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    # Find user by username
    user = db.session.query(User).filter_by(username=username, is_active=True).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Create session and token
    session_id = generate_uuid()
    token = generate_token(user.id, current_app.config)
    expiry = current_app.config.get("JWT_EXPIRY", timedelta(hours=24))
    expires_at = datetime.utcnow() + expiry
    
    session = Session(
        id=session_id,
        user_id=user.id,
        token=token,
        expires_at=expires_at,
        is_active=True
    )
    db.session.add(session)
    db.session.commit()
    
    current_app.logger.info(f"User {username} (session {session_id}) logged in")
    
    return jsonify({
        "ok": True,
        "token": token,
        "expires_in": int(expiry.total_seconds()),
        "user_id": user.id,
        "session_id": session_id,
    }), 200


@auth_bp.post("/validate")
@require_auth
def validate():
    """
    POST /api/auth/validate
    Verify token is valid and return extended session info
    Requires: Authorization: Bearer <token>
    """
    user = db.session.query(User).get(request.user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    token_expires_in = int(
        (request.session.expires_at - datetime.utcnow()).total_seconds()
    )
    
    return jsonify({
        "ok": True,
        "user_id": request.user_id,
        "session_id": request.session_id,
        "token_expires_in": max(0, token_expires_in),
        "username": user.username,
    }), 200


@auth_bp.post("/logout")
@require_auth
def logout():
    """
    POST /api/auth/logout
    Revoke current session token
    Requires: Authorization: Bearer <token>
    """
    request.session.is_active = False
    db.session.commit()
    
    current_app.logger.info(f"User {request.user_id} (session {request.session_id}) logged out")
    
    return jsonify({"ok": True}), 200


@auth_bp.post("/refresh")
@require_auth
def refresh():
    """
    POST /api/auth/refresh
    Refresh JWT token (optional: can be used for token rotation)
    Requires: Authorization: Bearer <token>
    """
    # Revoke old session
    request.session.is_active = False
    
    # Create new session
    session_id = generate_uuid()
    token = generate_token(request.user_id, current_app.config)
    expiry = current_app.config.get("JWT_EXPIRY", timedelta(hours=24))
    expires_at = datetime.utcnow() + expiry
    
    new_session = Session(
        id=session_id,
        user_id=request.user_id,
        token=token,
        expires_at=expires_at,
        is_active=True
    )
    db.session.add(new_session)
    db.session.commit()
    
    current_app.logger.info(f"User {request.user_id} token refreshed")
    
    return jsonify({
        "ok": True,
        "token": token,expiry
        "expires_in": int(current_app.config.JWT_EXPIRY.total_seconds()),
        "session_id": session_id,
    }), 200
