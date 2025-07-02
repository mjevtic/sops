"""
Authentication routes with security features
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_session
from models.user import User, UserLogin, UserCreate, UserResponse, Token
from models.audit import AuditLogCreate, AuditAction
from services.auth import AuthService
from services.audit import AuditService
from middleware import rate_limit_by_ip, get_remote_address
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=Token)
@rate_limit_by_ip("5/minute")
def login(
    user_credentials: UserLogin,
    request: Request,
    session: Session = Depends(get_session)
):
    """
    Authenticate user and return JWT tokens
    """
    try:
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent")
        
        user = AuthService.authenticate_user(
            session=session,
            username=user_credentials.username,
            password=user_credentials.password,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create tokens
        access_token = AuthService.create_access_token(user)
        refresh_token = AuthService.create_refresh_token(user)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/refresh", response_model=Token)
@rate_limit_by_ip("10/minute")
def refresh_token(
    request: Request,
    refresh_token: str,
    session: Session = Depends(get_session)
):
    """
    Refresh access token using refresh token
    """
    try:
        new_token = AuthService.refresh_access_token(session, refresh_token)
        
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        return new_token
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
@rate_limit_by_ip("10/minute")
def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """
    Logout user (invalidate token)
    """
    try:
        # Get current user
        user = AuthService.get_current_user(session, credentials.credentials)
        
        if user:
            # Log logout
            client_ip = get_remote_address(request)
            user_agent = request.headers.get("user-agent")
            
            AuditService.log_action(
                session,
                AuditLogCreate(
                    user_id=user.id,
                    username=user.username,
                    action=AuditAction.USER_LOGOUT,
                    resource_type="user",
                    resource_id=str(user.id),
                    ip_address=client_ip,
                    user_agent=user_agent,
                    details={"logout_method": "manual"}
                )
            )
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {"message": "Logged out"}  # Always return success for security


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """
    Get current user information
    """
    try:
        user = AuthService.get_current_user(session, credentials.credentials)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login=user.last_login,
            created_at=user.created_at,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """
    Change user password
    """
    try:
        user = AuthService.get_current_user(session, credentials.credentials)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Validate new password
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent")
        
        success = AuthService.change_password(
            session=session,
            user=user,
            old_password=old_password,
            new_password=new_password,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password"
            )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


# Dependency to get current user
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """
    Dependency to get current authenticated user
    """
    user = AuthService.get_current_user(session, credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# Dependency to require admin role
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require admin role
    """
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user

