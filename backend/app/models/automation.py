"""
Automation Models

TASK-310: Create Automation model
TASK-311: Add workflow definition field (JSON)
TASK-312: Add schedule field (cron format)
TASK-313: Add trigger configuration
TASK-314: Create AutomationRun model
TASK-315: Add run status tracking
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from app.db.session import Base


class TriggerType(str, enum.Enum):
    """Trigger types for automations"""
    SCHEDULE = "schedule"  # Cron-based schedule
    WEBHOOK = "webhook"  # External webhook
    EVENT = "event"  # Internal event (e.g., agent completion)
    MANUAL = "manual"  # User-triggered


class AutomationStatus(str, enum.Enum):
    """Automation status"""
    ACTIVE = "active"
    PAUSED = "paused"
    DRAFT = "draft"
    ARCHIVED = "archived"


class RunStatus(str, enum.Enum):
    """Automation run status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class Automation(Base):
    """
    Automation model
    
    TASK-310: Automation model
    TASK-311: Workflow definition (JSON)
    TASK-312: Schedule field (cron)
    TASK-313: Trigger configuration
    """
    __tablename__ = "automations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Organization relationship
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(
        SQLEnum(AutomationStatus),
        nullable=False,
        default=AutomationStatus.DRAFT
    )
    
    # Workflow definition (TASK-311)
    # JSON structure: { "steps": [ { "type": "...", "config": {...} } ] }
    workflow = Column(JSONB, nullable=False, default=dict)
    
    # Trigger configuration (TASK-313)
    trigger_type = Column(
        SQLEnum(TriggerType),
        nullable=False,
        default=TriggerType.MANUAL
    )
    
    # Schedule (TASK-312) - cron format
    schedule = Column(String(255), nullable=True)  # e.g., "0 9 * * MON-FRI"
    
    # Trigger config (additional settings)
    trigger_config = Column(JSONB, nullable=False, default=dict)
    
    # Agent to use (optional)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Metadata
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    total_runs = Column(Integer, nullable=False, default=0)
    success_runs = Column(Integer, nullable=False, default=0)
    failed_runs = Column(Integer, nullable=False, default=0)
    
    # Relationships
    organization = relationship("Organization", back_populates="automations")
    agent = relationship("Agent", back_populates="automations")
    runs = relationship("AutomationRun", back_populates="automation", cascade="all, delete-orphan")
    created_by_user = relationship("User")
    
    def __repr__(self):
        return f"<Automation {self.name} ({self.status})>"


class AutomationRun(Base):
    """
    Automation run model
    
    TASK-314: AutomationRun model
    TASK-315: Run status tracking
    """
    __tablename__ = "automation_runs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Automation relationship
    automation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("automations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Run status (TASK-315)
    status = Column(
        SQLEnum(RunStatus),
        nullable=False,
        default=RunStatus.PENDING,
        index=True
    )
    
    # Trigger info
    trigger_type = Column(String(50), nullable=False)
    trigger_data = Column(JSONB, nullable=False, default=dict)
    
    # Execution details
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Workflow state
    current_step = Column(Integer, nullable=True)
    total_steps = Column(Integer, nullable=True)
    
    # Execution context
    context = Column(JSONB, nullable=False, default=dict)
    
    # Results
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    
    # Logs
    logs = Column(JSONB, nullable=False, default=list)
    
    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    
    # Celery task ID
    task_id = Column(String(255), nullable=True, index=True)
    
    # Relationships
    automation = relationship("Automation", back_populates="runs")
    
    def __repr__(self):
        return f"<AutomationRun {self.id} ({self.status})>"
    
    def add_log(self, level: str, message: str, data: dict = None):
        """Add log entry to run"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "data": data or {}
        }
        
        if self.logs is None:
            self.logs = []
        
        self.logs.append(log_entry)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate run duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0
    
    @property
    def is_running(self) -> bool:
        """Check if run is currently running"""
        return self.status == RunStatus.RUNNING
    
    @property
    def is_complete(self) -> bool:
        """Check if run is complete (success or failure)"""
        return self.status in [RunStatus.SUCCESS, RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.TIMEOUT]
