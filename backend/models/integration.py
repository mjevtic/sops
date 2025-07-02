"""
Integration models for managing third-party service connections
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.types import JSON


class IntegrationType(str, Enum):
    """Integration platform types"""
    SLACK = "slack"
    TRELLO = "trello"
    NOTION = "notion"
    GOOGLE_SHEETS = "google_sheets"
    ZENDESK = "zendesk"
    FRESHDESK = "freshdesk"
    JIRA = "jira"
    GITHUB = "github"
    DISCORD = "discord"
    TEAMS = "teams"


class IntegrationStatus(str, Enum):
    """Integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING_SETUP = "pending_setup"


class Integration(SQLModel, table=True):
    """Integration configuration for third-party services"""
    __tablename__ = "integrations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    
    # Integration details
    name: str = Field(max_length=255)  # User-friendly name
    platform: IntegrationType = Field(index=True)
    status: IntegrationStatus = Field(default=IntegrationStatus.PENDING_SETUP)
    
    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Health monitoring
    last_health_check: Optional[datetime] = Field(default=None)
    health_check_status: Optional[str] = Field(default=None, max_length=50)
    last_error: Optional[str] = Field(default=None, max_length=1000)
    
    # Usage statistics
    total_actions_executed: int = Field(default=0)
    last_action_executed_at: Optional[datetime] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)  # Soft delete
    
    # Relationships
    user: "User" = Relationship(back_populates="integrations")
    credentials: "IntegrationCredential" = Relationship(back_populates="integration")


class IntegrationCredential(SQLModel, table=True):
    """Encrypted storage for integration credentials"""
    __tablename__ = "integration_credentials"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    integration_id: int = Field(foreign_key="integrations.id", unique=True, index=True)
    
    # Encrypted credentials (using Fernet encryption)
    encrypted_credentials: str = Field(max_length=2000)  # JSON string, encrypted
    
    # Credential metadata
    credential_type: str = Field(max_length=50)  # api_key, oauth_token, webhook_url, etc.
    expires_at: Optional[datetime] = Field(default=None)
    
    # Security
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(default=None)
    
    # Relationship
    integration: Integration = Relationship(back_populates="credentials")


class IntegrationCreate(SQLModel):
    """Integration creation schema"""
    name: str = Field(max_length=255)
    platform: IntegrationType
    config: Dict[str, Any] = Field(default_factory=dict)
    credentials: Dict[str, Any]  # Will be encrypted before storage


class IntegrationUpdate(SQLModel):
    """Integration update schema"""
    name: Optional[str] = Field(default=None, max_length=255)
    status: Optional[IntegrationStatus] = Field(default=None)
    config: Optional[Dict[str, Any]] = Field(default=None)
    credentials: Optional[Dict[str, Any]] = Field(default=None)  # Will be encrypted


class IntegrationResponse(SQLModel):
    """Integration response schema (excludes sensitive data)"""
    id: int
    name: str
    platform: IntegrationType
    status: IntegrationStatus
    config: Dict[str, Any]
    last_health_check: Optional[datetime]
    health_check_status: Optional[str]
    last_error: Optional[str]
    total_actions_executed: int
    last_action_executed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class IntegrationHealthCheck(SQLModel):
    """Integration health check result"""
    integration_id: int
    status: str  # healthy, unhealthy, unknown
    response_time_ms: Optional[int]
    error_message: Optional[str]
    checked_at: datetime
    details: Dict[str, Any] = Field(default_factory=dict)


# Platform-specific configuration schemas
class SlackConfig(SQLModel):
    """Slack integration configuration"""
    workspace_name: str
    default_channel: Optional[str] = None
    bot_name: Optional[str] = "SupportOps Bot"


class TrelloConfig(SQLModel):
    """Trello integration configuration"""
    board_id: str
    default_list_id: Optional[str] = None


class NotionConfig(SQLModel):
    """Notion integration configuration"""
    database_id: str
    page_template_id: Optional[str] = None


class GoogleSheetsConfig(SQLModel):
    """Google Sheets integration configuration"""
    spreadsheet_id: str
    default_sheet_name: Optional[str] = "Sheet1"


class ZendeskConfig(SQLModel):
    """Zendesk integration configuration"""
    subdomain: str
    webhook_endpoint: str


class FreshdeskConfig(SQLModel):
    """Freshdesk integration configuration"""
    domain: str
    webhook_endpoint: str

