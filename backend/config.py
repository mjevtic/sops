"""
Secure configuration management for SupportOps Automator
"""
import os
from typing import List
from pydantic import validator
from pydantic_settings import BaseSettings
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    """Application settings with validation and security features"""
    
    # Database
    database_url: str = ""
    
    # Security
    secret_key: str = ""
    jwt_secret_key: str = ""  # Added for Coolify compatibility
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    encryption_key: str = ""
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]
    cors_origins: str = "*"  # Added for Coolify compatibility
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    max_requests_per_minute: int = 100  # Added for Coolify compatibility
    redis_url: str = "redis://localhost:6379"
    
    # Webhook Security
    webhook_secret: str = ""  # Make optional for initial setup
    freshdesk_webhook_secret: str = ""  # Secret for Freshdesk webhook validation
    zendesk_webhook_secret: str = ""  # Secret for Zendesk webhook validation
    jira_webhook_secret: str = ""  # Added for Coolify compatibility
    github_webhook_secret: str = ""  # Added for Coolify compatibility
    
    # Admin User
    admin_email: str = "admin@supportops.local"  # Default admin email
    admin_password: str = "admin123!"  # Default admin password
    admin_username: str = "admin"  # Added for Coolify compatibility
    
    # Database Connection (for Docker/Coolify compatibility)
    database_host: str = ""  # Added for Docker networking
    database_port: str = ""  # Added for Docker networking
    database_name: str = ""  # Added for Docker networking
    database_user: str = ""  # Added for Docker networking
    database_password: str = ""  # Added for Docker networking
    
    # Monitoring
    sentry_dsn: str = ""
    environment: str = "development"
    
    # Logging
    log_level: str = "INFO"
    
    @validator('allowed_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long')
        return v
    
    @validator('encryption_key')
    def validate_encryption_key(cls, v):
        try:
            # Validate that the encryption key is valid for Fernet
            Fernet(v.encode())
        except Exception:
            raise ValueError('ENCRYPTION_KEY must be a valid Fernet key')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Encryption utility
def get_cipher():
    """Get Fernet cipher for encrypting/decrypting sensitive data"""
    return Fernet(settings.encryption_key.encode())


def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    cipher = get_cipher()
    return cipher.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    cipher = get_cipher()
    return cipher.decrypt(encrypted_data.encode()).decode()

