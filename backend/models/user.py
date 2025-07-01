"""
User model with Role-Based Access Control (RBAC)
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from passlib.context import CryptContext


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class User(SQLModel, table=True):
    """User model with security features"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, max_length=100)
    hashed_password: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.USER)
    
    # Security fields
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    failed_login_attempts: int = Field(default=0)
    last_login: Optional[datetime] = Field(default=None)
    password_changed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # GDPR compliance
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)  # Soft delete
    data_retention_until: Optional[datetime] = Field(default=None)
    
    # Personal data (for GDPR)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    
    # Relationships
    rules: List["Rule"] = Relationship(back_populates="user")
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")
    integrations: List["Integration"] = Relationship(back_populates="user")


class UserCreate(SQLModel):
    """User creation schema"""
    email: str = Field(max_length=255)
    username: str = Field(max_length=100)
    password: str = Field(min_length=8, max_length=100)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    role: UserRole = Field(default=UserRole.USER)


class UserUpdate(SQLModel):
    """User update schema"""
    email: Optional[str] = Field(default=None, max_length=255)
    username: Optional[str] = Field(default=None, max_length=100)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class UserResponse(SQLModel):
    """User response schema (excludes sensitive data)"""
    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    first_name: Optional[str]
    last_name: Optional[str]


class UserLogin(SQLModel):
    """User login schema"""
    username: str
    password: str


class Token(SQLModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(SQLModel):
    """Token payload data"""
    user_id: int
    username: str
    role: UserRole
    exp: int
    iat: int
    jti: str  # JWT ID for token revocation


# Password hashing utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

