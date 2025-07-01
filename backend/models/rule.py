"""
Rule model for automation workflows
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Relationship, JSON
from pydantic import validator


class RuleStatus(str, Enum):
    """Rule status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


class Rule(SQLModel, table=True):
    """Rule model for automation workflows"""
    __tablename__ = "rules"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    
    # Rule identification
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: RuleStatus = Field(default=RuleStatus.DRAFT)
    
    # Trigger configuration
    trigger_platform: str = Field(max_length=50, index=True)  # zendesk, freshdesk, etc.
    trigger_event: str = Field(max_length=100)  # tag_added, status_changed, etc.
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict, sa_column_kwargs={"type_": JSON})
    
    # Actions configuration
    actions: List[Dict[str, Any]] = Field(default_factory=list, sa_column_kwargs={"type_": JSON})
    
    # Execution settings
    is_enabled: bool = Field(default=True)
    max_executions_per_hour: int = Field(default=100)  # Rate limiting per rule
    execution_timeout_seconds: int = Field(default=300)  # 5 minutes default
    
    # Statistics
    execution_count: int = Field(default=0)
    last_executed_at: Optional[datetime] = Field(default=None)
    last_execution_status: Optional[str] = Field(default=None)
    last_execution_error: Optional[str] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)  # Soft delete
    
    # Relationships
    user: "User" = Relationship(back_populates="rules")
    audit_logs: List["AuditLog"] = Relationship(back_populates="rule")


class RuleCreate(SQLModel):
    """Rule creation schema"""
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    trigger_platform: str = Field(max_length=50)
    trigger_event: str = Field(max_length=100)
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    max_executions_per_hour: int = Field(default=100, ge=1, le=1000)
    execution_timeout_seconds: int = Field(default=300, ge=30, le=3600)
    
    @validator('actions')
    def validate_actions(cls, v):
        """Validate actions structure"""
        if not v:
            raise ValueError('At least one action is required')
        
        for action in v:
            if not isinstance(action, dict):
                raise ValueError('Each action must be a dictionary')
            if 'platform' not in action:
                raise ValueError('Each action must have a platform')
            if 'type' not in action:
                raise ValueError('Each action must have a type')
        
        return v
    
    @validator('trigger_platform')
    def validate_trigger_platform(cls, v):
        """Validate trigger platform"""
        allowed_platforms = ['zendesk', 'freshdesk', 'jira', 'github']
        if v not in allowed_platforms:
            raise ValueError(f'Trigger platform must be one of: {allowed_platforms}')
        return v


class RuleUpdate(SQLModel):
    """Rule update schema"""
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[RuleStatus] = Field(default=None)
    trigger_conditions: Optional[Dict[str, Any]] = Field(default=None)
    actions: Optional[List[Dict[str, Any]]] = Field(default=None)
    is_enabled: Optional[bool] = Field(default=None)
    max_executions_per_hour: Optional[int] = Field(default=None, ge=1, le=1000)
    execution_timeout_seconds: Optional[int] = Field(default=None, ge=30, le=3600)


class RuleResponse(SQLModel):
    """Rule response schema"""
    id: int
    name: str
    description: Optional[str]
    status: RuleStatus
    trigger_platform: str
    trigger_event: str
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_enabled: bool
    max_executions_per_hour: int
    execution_timeout_seconds: int
    execution_count: int
    last_executed_at: Optional[datetime]
    last_execution_status: Optional[str]
    created_at: datetime
    updated_at: datetime


class RuleExecution(SQLModel):
    """Rule execution tracking"""
    rule_id: int
    trigger_data: Dict[str, Any]
    execution_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str  # pending, running, completed, failed
    error_message: Optional[str] = None
    actions_executed: List[Dict[str, Any]] = Field(default_factory=list)

