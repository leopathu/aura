"""
Security Audit Logging System

TASK-403: Create security audit logs for all security events
Logs: authentication attempts, authorization failures, suspicious activity
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, Integer, Text, Index
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


# Configure security logger
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# File handler for security logs
security_handler = logging.FileHandler("logs/security_audit.log")
security_handler.setLevel(logging.INFO)

# Formatter for structured logging
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
security_handler.setFormatter(formatter)
security_logger.addHandler(security_handler)


class SecurityEventType(str, Enum):
    """Types of security events to log"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # Authorization events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    FORBIDDEN_ACCESS = "forbidden_access"
    PERMISSION_DENIED = "permission_denied"
    
    # Token events
    TOKEN_CREATED = "token_created"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    TOKEN_REVOKED = "token_revoked"
    
    # Security incidents
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTEMPT = "csrf_attempt"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    IP_BLOCKED = "ip_blocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # Data access
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    
    # API key events
    API_KEY_CREATED = "api_key_created"
    API_KEY_ROTATED = "api_key_rotated"
    API_KEY_DELETED = "api_key_deleted"
    API_KEY_INVALID = "api_key_invalid"


class SecurityEventSeverity(str, Enum):
    """Severity levels for security events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SecurityAuditLog(Base):
    """Database model for security audit logs"""
    __tablename__ = "security_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    
    # User information
    user_id = Column(String(36), index=True)
    user_email = Column(String(255), index=True)
    
    # Request information
    ip_address = Column(String(45), index=True)  # IPv6 max length
    user_agent = Column(String(500))
    request_path = Column(String(500))
    request_method = Column(String(10))
    
    # Event details
    message = Column(Text)
    details = Column(JSONB)  # Structured event data
    
    # Response information
    status_code = Column(Integer)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_security_logs_timestamp_severity', 'timestamp', 'severity'),
        Index('idx_security_logs_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_security_logs_ip_timestamp', 'ip_address', 'timestamp'),
    )


class SecurityEvent(BaseModel):
    """Pydantic model for security events"""
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None


class SecurityAuditLogger:
    """Security audit logging service"""
    
    @staticmethod
    def log_event(event: SecurityEvent):
        """Log a security event to file and database"""
        # Log to file
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "user_id": event.user_id,
            "user_email": event.user_email,
            "ip_address": event.ip_address,
            "message": event.message,
            "details": event.details,
        }
        
        # Choose logging level based on severity
        if event.severity == SecurityEventSeverity.INFO:
            security_logger.info(json.dumps(log_data))
        elif event.severity == SecurityEventSeverity.WARNING:
            security_logger.warning(json.dumps(log_data))
        elif event.severity == SecurityEventSeverity.ERROR:
            security_logger.error(json.dumps(log_data))
        elif event.severity == SecurityEventSeverity.CRITICAL:
            security_logger.critical(json.dumps(log_data))
    
    @staticmethod
    def log_authentication_success(user_email: str, user_id: str, ip_address: str):
        """Log successful authentication"""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecurityEventSeverity.INFO,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            message=f"User {user_email} logged in successfully",
            status_code=200
        )
        SecurityAuditLogger.log_event(event)
    
    @staticmethod
    def log_authentication_failure(email: str, ip_address: str, reason: str = "Invalid credentials"):
        """Log failed authentication attempt"""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILED,
            severity=SecurityEventSeverity.WARNING,
            user_email=email,
            ip_address=ip_address,
            message=f"Failed login attempt for {email}: {reason}",
            details={"reason": reason},
            status_code=401
        )
        SecurityAuditLogger.log_event(event)
    
    @staticmethod
    def log_brute_force_attempt(ip_address: str, attempts: int):
        """Log potential brute force attack"""
        event = SecurityEvent(
            event_type=SecurityEventType.BRUTE_FORCE_ATTEMPT,
            severity=SecurityEventSeverity.ERROR,
            ip_address=ip_address,
            message=f"Potential brute force attack from {ip_address}",
            details={"attempts": attempts},
            status_code=429
        )
        SecurityAuditLogger.log_event(event)
    
    @staticmethod
    def log_unauthorized_access(user_email: str, user_id: str, resource: str, ip_address: str):
        """Log unauthorized access attempt"""
        event = SecurityEvent(
            event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
            severity=SecurityEventSeverity.WARNING,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            message=f"Unauthorized access attempt to {resource}",
            details={"resource": resource},
            status_code=403
        )
        SecurityAuditLogger.log_event(event)
    
    @staticmethod
    def log_sql_injection_attempt(ip_address: str, payload: str, endpoint: str):
        """Log SQL injection attempt"""
        event = SecurityEvent(
            event_type=SecurityEventType.SQL_INJECTION_ATTEMPT,
            severity=SecurityEventSeverity.CRITICAL,
            ip_address=ip_address,
            request_path=endpoint,
            message=f"SQL injection attempt detected from {ip_address}",
            details={"payload": payload[:500], "endpoint": endpoint},
            status_code=400
        )
        SecurityAuditLogger.log_event(event)
    
    @staticmethod
    def log_xss_attempt(ip_address: str, payload: str, endpoint: str):
        """Log XSS attempt"""
        event = SecurityEvent(
            event_type=SecurityEventType.XSS_ATTEMPT,
            severity=SecurityEventSeverity.CRITICAL,
            ip_address=ip_address,
            request_path=endpoint,
            message=f"XSS attempt detected from {ip_address}",
            details={"payload": payload[:500], "endpoint": endpoint},
            status_code=400
        )
        SecurityAuditLogger.log_event(event)
    
    @staticmethod
    def log_rate_limit_exceeded(ip_address: str, endpoint: str):
        """Log rate limit violation"""
        event = SecurityEvent(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            severity=SecurityEventSeverity.WARNING,
            ip_address=ip_address,
            request_path=endpoint,
            message=f"Rate limit exceeded from {ip_address} on {endpoint}",
            status_code=429
        )
        SecurityAuditLogger.log_event(event)
    
    @staticmethod
    def log_ip_blocked(ip_address: str, reason: str):
        """Log IP blocking"""
        event = SecurityEvent(
            event_type=SecurityEventType.IP_BLOCKED,
            severity=SecurityEventSeverity.ERROR,
            ip_address=ip_address,
            message=f"IP {ip_address} has been blocked: {reason}",
            details={"reason": reason},
            status_code=403
        )
        SecurityAuditLogger.log_event(event)
    
    @staticmethod
    def log_password_change(user_email: str, user_id: str, ip_address: str):
        """Log password change"""
        event = SecurityEvent(
            event_type=SecurityEventType.PASSWORD_CHANGE,
            severity=SecurityEventSeverity.INFO,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            message=f"Password changed for {user_email}",
            status_code=200
        )
        SecurityAuditLogger.log_event(event)
    
    @staticmethod
    def log_api_key_rotation(user_id: str, credential_type: str):
        """Log API key rotation"""
        event = SecurityEvent(
            event_type=SecurityEventType.API_KEY_ROTATED,
            severity=SecurityEventSeverity.INFO,
            user_id=user_id,
            message=f"API key rotated for credential type: {credential_type}",
            details={"credential_type": credential_type}
        )
        SecurityAuditLogger.log_event(event)
    
    @staticmethod
    def log_sensitive_data_access(user_id: str, user_email: str, resource: str, ip_address: str):
        """Log access to sensitive data"""
        event = SecurityEvent(
            event_type=SecurityEventType.SENSITIVE_DATA_ACCESS,
            severity=SecurityEventSeverity.INFO,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            message=f"Sensitive data accessed: {resource}",
            details={"resource": resource}
        )
        SecurityAuditLogger.log_event(event)
    
    @staticmethod
    def log_suspicious_activity(ip_address: str, description: str, details: Optional[Dict] = None):
        """Log suspicious activity"""
        event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=SecurityEventSeverity.WARNING,
            ip_address=ip_address,
            message=f"Suspicious activity detected: {description}",
            details=details or {}
        )
        SecurityAuditLogger.log_event(event)


# Convenience instance
audit_logger = SecurityAuditLogger()
