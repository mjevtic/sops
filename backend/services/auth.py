"""
Authentication service with JWT tokens and security features
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from models.user import User, UserRole, verify_password, get_password_hash, Token, TokenData
from models.audit import AuditLog, AuditAction
from config import settings
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service with security features"""
    
    @staticmethod
    def authenticate_user(
        session: Session, 
        username: str, 
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[User]:
        """
        Authenticate user with security measures
        """
        try:
            # Get user by username or email
            result = session.execute(
                select(User).where(
                    (User.username == username) | (User.email == username)
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Log failed login attempt
                AuthService._log_failed_login(
                    session, username, "user_not_found", ip_address, user_agent
                )
                return None
            
            # Check if user is active
            if not user.is_active:
                AuthService._log_failed_login(
                    session, username, "user_inactive", ip_address, user_agent
                )
                return None
            
            # Check for account lockout (after 5 failed attempts)
            if user.failed_login_attempts >= 5:
                AuthService._log_failed_login(
                    session, username, "account_locked", ip_address, user_agent
                )
                return None
            
            # Verify password
            if not verify_password(password, user.hashed_password):
                # Increment failed login attempts
                session.execute(
                    update(User)
                    .where(User.id == user.id)
                    .values(failed_login_attempts=user.failed_login_attempts + 1)
                )
                session.commit()
                
                AuthService._log_failed_login(
                    session, username, "invalid_password", ip_address, user_agent
                )
                return None
            
            # Successful login - reset failed attempts and update last login
            session.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    failed_login_attempts=0,
                    last_login=datetime.utcnow()
                )
            )
            session.commit()
            
            # Log successful login
            audit_log = AuditLog(
                user_id=user.id,
                username=user.username,
                action=AuditAction.USER_LOGIN,
                resource_type="user",
                resource_id=str(user.id),
                ip_address=ip_address,
                user_agent=user_agent,
                details={"login_method": "password"},
                status="success"
            )
            session.add(audit_log)
            session.commit()
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            session.rollback()
            return None
    
    @staticmethod
    def _log_failed_login(
        session: Session,
        username: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log failed login attempt"""
        audit_log = AuditLog(
            username=username,
            action=AuditAction.USER_LOGIN_FAILED,
            resource_type="user",
            ip_address=ip_address,
            user_agent=user_agent,
            details={"reason": reason},
            status="failed"
        )
        session.add(audit_log)
        session.commit()
    
    @staticmethod
    def create_access_token(user: User) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # JWT ID for token revocation
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user: User) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        
        to_encode = {
            "sub": str(user.id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            
            user_id: int = int(payload.get("sub"))
            username: str = payload.get("username")
            role: str = payload.get("role")
            exp: int = payload.get("exp")
            iat: int = payload.get("iat")
            jti: str = payload.get("jti")
            
            if user_id is None or username is None:
                return None
            
            token_data = TokenData(
                user_id=user_id,
                username=username,
                role=UserRole(role),
                exp=exp,
                iat=iat,
                jti=jti
            )
            return token_data
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    @staticmethod
    def get_current_user(
        session: Session, 
        token: str
    ) -> Optional[User]:
        """Get current user from JWT token"""
        token_data = AuthService.verify_token(token)
        if token_data is None:
            return None
        
        try:
            result = session.execute(
                select(User).where(User.id == token_data.user_id)
            )
            user = result.scalar_one_or_none()
            
            if user is None or not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    @staticmethod
    def refresh_access_token(
        session: Session,
        refresh_token: str
    ) -> Optional[Token]:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(
                refresh_token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            
            user_id: int = int(payload.get("sub"))
            token_type: str = payload.get("type")
            
            if token_type != "refresh":
                return None
            
            # Get user
            result = session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user is None or not user.is_active:
                return None
            
            # Create new tokens
            access_token = AuthService.create_access_token(user)
            new_refresh_token = AuthService.create_refresh_token(user)
            
            return Token(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=settings.access_token_expire_minutes * 60
            )
            
        except JWTError as e:
            logger.warning(f"Refresh token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    @staticmethod
    def change_password(
        session: Session,
        user: User,
        old_password: str,
        new_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Change user password with security validation"""
        try:
            # Verify old password
            if not verify_password(old_password, user.hashed_password):
                return False
            
            # Hash new password
            new_hashed_password = get_password_hash(new_password)
            
            # Update password
            session.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    hashed_password=new_hashed_password,
                    password_changed_at=datetime.utcnow()
                )
            )
            session.commit()
            
            # Log password change
            audit_log = AuditLog(
                user_id=user.id,
                username=user.username,
                action=AuditAction.USER_PASSWORD_CHANGED,
                resource_type="user",
                resource_id=str(user.id),
                ip_address=ip_address,
                user_agent=user_agent,
                details={"changed_by": "user"},
                status="success"
            )
            session.add(audit_log)
            session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Password change error: {e}")
            session.rollback()
            return False

