"""
data_server/routes/collab.py — Collaboration endpoints (lock, presence, events)
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app import db
from models import Project, Presence, CollaborationEvent, Session
from utils import generate_uuid, require_auth
import json

collab_bp = Blueprint("collab", __name__)


@collab_bp.post("/<project_id>/lock")
@require_auth
def acquire_lock(project_id: str):
    """
    POST /api/projects/<project_id>/lock
    Acquire lock on project for editing
    """
    project = db.session.query(Project).get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    data = request.get_json()
    ttl_seconds = data.get("ttl_seconds", current_app.config.LOCK_TTL_SECONDS)
    
    # Check if already locked by another user
    if project.locked_by and project.locked_by != request.user_id:
        if project.locked_until and project.locked_until > datetime.utcnow():
            return jsonify({
                "error": "locked_by_other",
                "locked_by": project.locked_by,
                "locked_until": int(project.locked_until.timestamp()),
            }), 409
    
    # Acquire lock
    project.locked_by = request.user_id
    project.locked_until = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    db.session.commit()
    
    current_app.logger.info(f"Lock acquired on {project_id} by {request.user_id}")
    
    return jsonify({
        "locked": True,
        "locked_by": project.locked_by,
        "locked_until": int(project.locked_until.timestamp()),
    }), 200


@collab_bp.post("/<project_id>/unlock")
@require_auth
def release_lock(project_id: str):
    """
    POST /api/projects/<project_id>/unlock
    Release lock on project
    """
    project = db.session.query(Project).get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    # Only the lock owner can release
    if project.locked_by != request.user_id:
        return jsonify({"error": "Not lock owner"}), 403
    
    project.locked_by = None
    project.locked_until = None
    db.session.commit()
    
    current_app.logger.info(f"Lock released on {project_id} by {request.user_id}")
    
    return jsonify({"ok": True}), 200


@collab_bp.post("/<project_id>/presence")
@require_auth
def update_presence(project_id: str):
    """
    POST /api/projects/<project_id>/presence
    Update presence status (heartbeat)
    """
    project = db.session.query(Project).get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    data = request.get_json()
    action = data.get("action", "online")  # online, idle, offline
    
    # Find or create presence record
    presence = db.session.query(Presence).filter_by(
        user_id=request.user_id,
        session_id=request.session_id,
        project_id=project_id
    ).first()
    
    if not presence:
        presence = Presence(
            id=generate_uuid(),
            user_id=request.user_id,
            session_id=request.session_id,
            project_id=project_id,
            status=action
        )
        db.session.add(presence)
    else:
        presence.status = action
        presence.last_heartbeat = datetime.utcnow()
    
    db.session.commit()
    
    # Return current presence list for project
    all_presence = db.session.query(Presence).filter_by(project_id=project_id).all()
    presence_list = []
    for p in all_presence:
        presence_list.append({
            "user_id": p.user_id,
            "session_id": p.session_id,
            "status": p.status,
            "last_heartbeat": int(p.last_heartbeat.timestamp()),
        })
    
    return jsonify({"presence": presence_list}), 200


@collab_bp.post("/<project_id>/events")
@require_auth
def append_event(project_id: str):
    """
    POST /api/projects/<project_id>/events
    Append collaboration event (step_added, step_edited, etc.)
    """
    project = db.session.query(Project).get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    data = request.get_json()
    event_type = data.get("event_type")
    payload = data.get("payload", {})
    
    if not event_type:
        return jsonify({"error": "event_type required"}), 400
    
    # Get next sequence number for this project
    last_event = db.session.query(CollaborationEvent).filter_by(project_id=project_id).order_by(
        CollaborationEvent.sequence.desc()
    ).first()
    next_sequence = (last_event.sequence if last_event else 0) + 1
    
    event = CollaborationEvent(
        id=generate_uuid(),
        project_id=project_id,
        sequence=next_sequence,
        event_type=event_type,
        payload=json.dumps(payload),
        user_id=request.user_id,
        session_id=request.session_id,
        created_at=datetime.utcnow(),
    )
    
    db.session.add(event)
    db.session.commit()
    
    return jsonify({
        "event_id": event.id,
        "sequence": event.sequence,
        "timestamp": int(event.created_at.timestamp()),
    }), 201


@collab_bp.get("/<project_id>/events")
@require_auth
def get_events(project_id: str):
    """
    GET /api/projects/<project_id>/events?since=<sequence_num>
    Get collaboration events since given sequence
    """
    project = db.session.query(Project).get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    since = request.args.get("since", 0, type=int)
    
    events = db.session.query(CollaborationEvent).filter(
        CollaborationEvent.project_id == project_id,
        CollaborationEvent.sequence > since
    ).order_by(CollaborationEvent.sequence.asc()).all()
    
    result = []
    for evt in events:
        result.append({
            "event_id": evt.id,
            "sequence": evt.sequence,
            "event_type": evt.event_type,
            "payload": json.loads(evt.payload) if evt.payload else {},
            "user_id": evt.user_id,
            "timestamp": int(evt.created_at.timestamp()),
        })
    
    return jsonify({"events": result}), 200
