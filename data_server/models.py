"""
data_server/models.py — Database models for users, projects, collaboration
Uses SQLAlchemy ORM
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from app import db


class User(db.Model):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)  # UUID
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", foreign_keys="[Project.created_by]", back_populates="created_by_user")
    edits = relationship("ProjectVersion", back_populates="changed_by_user")
    
    __table_args__ = (
        Index("idx_username", "username"),
        Index("idx_is_active", "is_active"),
    )


class Session(db.Model):
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="sessions")
    presence = relationship("Presence", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_token", "token"),
        Index("idx_expires_at", "expires_at"),
        Index("idx_user_active", "user_id", "is_active"),
    )


class Project(db.Model):
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # 'sequence', 'script', 'blockly'
    content = Column(Text, nullable=True)  # JSON: steps, metadata, etc.
    blockly_xml = Column(Text, nullable=True)  # Blockly workspace XML
    python_code = Column(Text, nullable=True)  # Generated Python code
    
    revision = Column(Integer, default=1, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    checksum = Column(String(64), nullable=True)  # SHA256 for conflict detection
    
    locked_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    locked_until = Column(DateTime, nullable=True)
    
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="projects")
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    locked_by_user = relationship("User", foreign_keys=[locked_by])
    
    versions = relationship("ProjectVersion", back_populates="project", cascade="all, delete-orphan")
    events = relationship("CollaborationEvent", back_populates="project", cascade="all, delete-orphan")
    presence = relationship("Presence", back_populates="project", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_name_type", "name", "type"),
        Index("idx_updated_at", "updated_at"),
        Index("idx_locked_by", "locked_by"),
    )


class ProjectVersion(db.Model):
    __tablename__ = "project_versions"
    
    id = Column(String(36), primary_key=True)  # UUID
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    revision = Column(Integer, nullable=False)
    content_snapshot = Column(Text, nullable=True)  # Full JSON snapshot
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    change_reason = Column(String(500), nullable=True)
    checksum = Column(String(64), nullable=True)
    
    project = relationship("Project", back_populates="versions")
    changed_by_user = relationship("User", back_populates="edits")
    
    __table_args__ = (
        Index("idx_project_revision", "project_id", "revision"),
        Index("idx_changed_at", "changed_at"),
    )


class CollaborationEvent(db.Model):
    __tablename__ = "collaboration_events"
    
    id = Column(String(36), primary_key=True)  # UUID
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)  # Monotonic event counter per project
    event_type = Column(String(100), nullable=False)  # step_added, step_edited, step_deleted, etc.
    payload = Column(Text, nullable=True)  # JSON: event-specific data
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    project = relationship("Project", back_populates="events")
    session = relationship("Session")
    
    __table_args__ = (
        Index("idx_project_sequence", "project_id", "sequence"),
        Index("idx_created_at", "created_at"),
    )


class Presence(db.Model):
    __tablename__ = "presence"
    
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    status = Column(String(50), default="online", nullable=False)  # online, idle, offline
    last_heartbeat = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    session = relationship("Session", back_populates="presence")
    project = relationship("Project", back_populates="presence")
    
    __table_args__ = (
        Index("idx_project_user", "project_id", "user_id"),
        Index("idx_last_heartbeat", "last_heartbeat"),
    )
