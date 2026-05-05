"""
data_server/routes/projects.py — Project CRUD and revision management
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from models import db, Project, ProjectVersion, User
from utils import generate_uuid, require_auth, compute_checksum
import json

projects_bp = Blueprint("projects", __name__)


@projects_bp.get("")
@require_auth
def list_projects():
    """
    GET /api/projects
    List all projects visible to authenticated user
    """
    projects = db.session.query(Project).all()
    
    result = []
    for proj in projects:
        result.append({
            "id": proj.id,
            "name": proj.name,
            "type": proj.type,
            "updated_by": proj.updated_by,
            "updated_at": int(proj.updated_at.timestamp()),
            "revision": proj.revision,
            "locked_by": proj.locked_by,
            "locked_until": int(proj.locked_until.timestamp()) if proj.locked_until else None,
        })
    
    return jsonify({"projects": result}), 200


@projects_bp.get("/<project_id>")
@require_auth
def get_project(project_id: str):
    """
    GET /api/projects/<project_id>
    Get full project content
    """
    project = db.session.query(Project).get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    return jsonify({
        "project": {
            "id": project.id,
            "name": project.name,
            "type": project.type,
            "content": json.loads(project.content) if project.content else None,
            "blockly_xml": project.blockly_xml,
            "python_code": project.python_code,
            "revision": project.revision,
            "updated_by": project.updated_by,
            "updated_at": int(project.updated_at.timestamp()),
            "checksum": project.checksum,
        }
    }), 200


@projects_bp.post("")
@require_auth
def create_project():
    """
    POST /api/projects
    Create new project
    """
    data = request.get_json()
    name = data.get("name", "").strip()
    proj_type = data.get("type", "sequence")  # sequence, script, blockly
    content = data.get("content")
    blockly_xml = data.get("blockly_xml")
    python_code = data.get("python_code")
    
    if not name:
        return jsonify({"error": "Project name required"}), 400
    
    # Check for duplicate name
    existing = db.session.query(Project).filter_by(name=name).first()
    if existing:
        return jsonify({"error": "Project name already exists"}), 409
    
    project_id = generate_uuid()
    content_str = json.dumps(content) if content else "{}"
    checksum = compute_checksum(content or {})
    
    project = Project(
        id=project_id,
        name=name,
        type=proj_type,
        content=content_str,
        blockly_xml=blockly_xml,
        python_code=python_code,
        revision=1,
        created_by=request.user_id,
        updated_by=request.user_id,
        checksum=checksum,
    )
    
    db.session.add(project)
    db.session.commit()
    
    current_app.logger.info(f"Project {project_id} created by {request.user_id}")
    
    return jsonify({
        "project": {
            "id": project.id,
            "name": project.name,
            "type": project.type,
            "revision": project.revision,
            "updated_by": project.updated_by,
            "updated_at": int(project.updated_at.timestamp()),
            "checksum": project.checksum,
        }
    }), 201


@projects_bp.put("/<project_id>")
@require_auth
def update_project(project_id: str):
    """
    PUT /api/projects/<project_id>
    Update project content with revision check
    Detects conflicts if expected_revision != server revision
    """
    project = db.session.query(Project).get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    data = request.get_json()
    expected_revision = data.get("expected_revision")
    content = data.get("content")
    blockly_xml = data.get("blockly_xml")
    python_code = data.get("python_code")
    change_reason = data.get("change_reason", "User edit")
    
    # Check for revision mismatch (conflict detection)
    if expected_revision is not None and expected_revision != project.revision:
        latest_version = db.session.query(ProjectVersion).filter_by(
            project_id=project_id,
            revision=project.revision
        ).first()
        
        return jsonify({
            "error": "revision_mismatch",
            "local_revision": expected_revision,
            "server_revision": project.revision,
            "server_updated_by": project.updated_by,
            "server_updated_at": int(project.updated_at.timestamp()),
            "server_content": json.loads(project.content) if project.content else None,
        }), 409
    
    # Update project
    content_str = json.dumps(content) if content else "{}"
    checksum = compute_checksum(content or {})
    
    old_revision = project.revision
    project.content = content_str
    project.blockly_xml = blockly_xml
    project.python_code = python_code
    project.revision += 1
    project.updated_by = request.user_id
    project.updated_at = datetime.utcnow()
    project.checksum = checksum
    
    # Store version for audit trail
    version = ProjectVersion(
        id=generate_uuid(),
        project_id=project_id,
        revision=project.revision,
        content_snapshot=content_str,
        changed_by=request.user_id,
        changed_at=datetime.utcnow(),
        change_reason=change_reason,
        checksum=checksum,
    )
    
    db.session.add(version)
    db.session.commit()
    
    current_app.logger.info(
        f"Project {project_id} updated by {request.user_id} "
        f"(revision {old_revision} -> {project.revision})"
    )
    
    return jsonify({
        "project": {
            "id": project.id,
            "name": project.name,
            "type": project.type,
            "revision": project.revision,
            "updated_by": project.updated_by,
            "updated_at": int(project.updated_at.timestamp()),
            "checksum": project.checksum,
        }
    }), 200

@projects_bp.post("/<project_id>/invite")
@require_auth
def get_invite_link(project_id: str):
    """
    POST /api/projects/<project_id>/invite
    Generate an invite link for sharing
    """
    project = db.session.query(Project).get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
        
    import os
    # Default to the known server IP, allow override via env var PUBLIC_URL
    server_host = os.environ.get("PUBLIC_URL", "http://31.70.67.178:5001").rstrip("/")
    invite_link = f"{server_host}/invite/{project_id}"
    
    return jsonify({
        "ok": True,
        "invite_link": invite_link
    }), 200


@projects_bp.delete("/<project_id>")
@require_auth
def delete_project(project_id: str):
    """
    DELETE /api/projects/<project_id>
    Delete project and all versions/events
    """
    project = db.session.query(Project).get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    db.session.delete(project)
    db.session.commit()
    
    current_app.logger.info(f"Project {project_id} deleted by {request.user_id}")
    
    return jsonify({"ok": True}), 200
