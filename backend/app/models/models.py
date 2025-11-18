from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


# Association tables for many-to-many relationships
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)

brain_roles = Table(
    'brain_roles',
    Base.metadata,
    Column('brain_id', Integer, ForeignKey('brains.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)

brain_departments = Table(
    'brain_departments',
    Base.metadata,
    Column('brain_id', Integer, ForeignKey('brains.id', ondelete='CASCADE'), primary_key=True),
    Column('department_id', Integer, ForeignKey('departments.id', ondelete='CASCADE'), primary_key=True)
)

brain_teams = Table(
    'brain_teams',
    Base.metadata,
    Column('brain_id', Integer, ForeignKey('brains.id', ondelete='CASCADE'), primary_key=True),
    Column('team_id', Integer, ForeignKey('teams.id', ondelete='CASCADE'), primary_key=True)
)


class BrainVisibility(str, enum.Enum):
    PRIVATE = "private"
    ORGANIZATION = "organization"
    ROLE = "role"
    DEPARTMENT = "department"
    TEAM = "team"


class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="organization", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")
    brains = relationship("Brain", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    department = relationship("Department", back_populates="users")
    team = relationship("Team", back_populates="users")
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    brains = relationship("Brain", back_populates="owner", foreign_keys="Brain.owner_id")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    google_drive_tokens = relationship("GoogleDriveToken", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    permissions = Column(JSON, default=dict)  # Store permissions as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")
    brains = relationship("Brain", secondary=brain_roles, back_populates="assigned_roles")


class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="departments")
    users = relationship("User", back_populates="department")
    teams = relationship("Team", back_populates="department")
    brains = relationship("Brain", secondary=brain_departments, back_populates="assigned_departments")


class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="teams")
    department = relationship("Department", back_populates="teams")
    users = relationship("User", back_populates="team")
    brains = relationship("Brain", secondary=brain_teams, back_populates="assigned_teams")


class Brain(Base):
    __tablename__ = "brains"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    visibility = Column(SQLEnum(BrainVisibility), default=BrainVisibility.PRIVATE, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default=dict)  # Store brain-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="brains")
    owner = relationship("User", back_populates="brains", foreign_keys=[owner_id])
    assigned_roles = relationship("Role", secondary=brain_roles, back_populates="brains")
    assigned_departments = relationship("Department", secondary=brain_departments, back_populates="brains")
    assigned_teams = relationship("Team", secondary=brain_teams, back_populates="brains")
    documents = relationship("Document", back_populates="brain", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="brain", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    brain_id = Column(Integer, ForeignKey("brains.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, image, etc.
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    source = Column(String(50), default="upload")  # upload, google_drive
    source_url = Column(String(1000), nullable=True)  # Google Drive URL if applicable
    vector_ids = Column(JSON, default=list)  # Store Qdrant vector IDs
    doc_metadata = Column(JSON, default=dict)
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    brain = relationship("Brain", back_populates="documents")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    brain_id = Column(Integer, ForeignKey("brains.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    brain = relationship("Brain", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=list)  # Store document sources used
    msg_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class GoogleDriveToken(Base):
    __tablename__ = "google_drive_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expiry = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="google_drive_tokens")
