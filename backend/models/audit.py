"""
Audit logging model for compliance and security monitoring
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.types import JSON


class AuditAction(str, Enum):
    """Audit action types"""
    # User actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_LOGIN_FAILED = "user_login_failed"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_PASSWORD_CHANGED = "user_password_changed"
    
    # Rule actions
    RULE_CREATED = "rule_created"
    RULE_UPDATED = "rule_updated"
    RULE_DELETED = "rule_deleted"
    RULE_EXECUTED = "rule_executed"
    RULE_EXECUTION_FAILED = "rule_execution_failed"
    
    # Integration actions
    INTEGRATION_CREATED = "integration_created"
    INTEGRATION_UPDATED = "integration_updated"
    INTEGRATION_DELETED = "integration_deleted"
    INTEGRATION_CREDENTIALS_UPDATED = "integration_credentials_updated"
    
    # Security events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    WEBHOOK_SIGNATURE_INVALID = "webhook_signature_invalid"
    
    # Data actions (GDPR compliance)
    DATA_EXPORTED = "data_exported"
    DATA_DELETED = "data_deleted"
    DATA_RETENTION_APPLIED = "data_retention_applied"


class AuditLog(SQLModel, table=True):
    """Audit log for tracking all system activities"""
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Who performed the action
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    username: Optional[str] = Field(default=None, max_length=100)  # For deleted users
    
    # What action was performed
    action: AuditAction = Field(index=True)
    resource_type: str = Field(max_length=50, index=True)  # user, rule, integration, etc.
    resource_id: Optional[str] = Field(default=None, max_length=100, index=True)
    
    # Related rule (if applicable)
    rule_id: Optional[int] = Field(default=None, foreign_key="rules.id", index=True)
    
    # Request details
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 compatible
    user_agent: Optional[str] = Field(default=None, max_length=500)
    request_id: Optional[str] = Field(default=None, max_length=100, index=True)
    
    # Action details
    details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    old_values: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    new_values: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Status and error information
    status: str = Field(default="success", max_length=20)  # success, failed, error
    error_message: Optional[str] = Field(default=None, max_length=1000)
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    duration_ms: Optional[int] = Field(default=None)  # Action duration in milliseconds
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="audit_logs")
    rule: Optional["Rule"] = Relationship(back_populates="audit_logs")


class AuditLogCreate(SQLModel):
    """Audit log creation schema"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    rule_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    status: str = "success"
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None


class AuditLogResponse(SQLModel):
    """Audit log response schema"""
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: AuditAction
    resource_type: str
    resource_id: Optional[str]
    rule_id: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    details: Dict[str, Any]
    status: str
    error_message: Optional[str]
    timestamp: datetime
    duration_ms: Optional[int]


class AuditLogFilter(SQLModel):
    """Audit log filtering schema"""
    user_id: Optional[int] = None
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    rule_id: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

