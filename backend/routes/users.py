"""
User management routes with RBAC and security features
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from database import get_session
from models.user import User, UserCreate, UserUpdate, UserResponse, UserRole, get_password_hash
from models.audit import AuditLogCreate, AuditAction
from services.audit import AuditService
from routes.auth import get_current_user, require_admin
from middleware import rate_limit_by_user, get_remote_address
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new user (admin only)
    """
    try:
        # Check if user already exists
        existing_user = await session.execute(
            select(User).where(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            role=user_data.role,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=True,
            is_verified=True
        )
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        # Log user creation
        client_ip = get_remote_address(request)
        await AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                username=current_user.username,
                action=AuditAction.USER_CREATED,
                resource_type="user",
                resource_id=str(new_user.id),
                ip_address=client_ip,
                details={
                    "created_user_email": new_user.email,
                    "created_user_role": new_user.role.value
                }
            )
        )
        
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            username=new_user.username,
            role=new_user.role,
            is_active=new_user.is_active,
            is_verified=new_user.is_verified,
            last_login=new_user.last_login,
            created_at=new_user.created_at,
            first_name=new_user.first_name,
            last_name=new_user.last_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User creation error: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )


@router.get("/", response_model=List[UserResponse])
@rate_limit_by_user("30/minute")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Get list of users (admin only)
    """
    try:
        query = select(User).where(User.deleted_at.is_(None))
        
        # Apply filters
        if role:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await session.execute(query)
        users = result.scalars().all()
        
        return [
            UserResponse(
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
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/{user_id}", response_model=UserResponse)
@rate_limit_by_user("30/minute")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get user by ID (admin can see all, users can see themselves)
    """
    try:
        # Access control
        if current_user.role.value != "admin" and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        result = await session.execute(
            select(User).where(
                and_(User.id == user_id, User.deleted_at.is_(None))
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
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
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update user (admin can update all, users can update themselves with restrictions)
    """
    try:
        # Access control
        if current_user.role.value != "admin" and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get user to update
        result = await session.execute(
            select(User).where(
                and_(User.id == user_id, User.deleted_at.is_(None))
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Store old values for audit
        old_values = {
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "is_active": user.is_active,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
        
        # Prepare update data
        update_data = {}
        
        # Non-admin users cannot change role or is_active
        if current_user.role.value != "admin":
            if user_data.role is not None or user_data.is_active is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to modify role or active status"
                )
        
        # Apply updates
        if user_data.email is not None:
            # Check if email is already taken
            existing = await session.execute(
                select(User).where(
                    and_(User.email == user_data.email, User.id != user_id)
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
            update_data["email"] = user_data.email
        
        if user_data.username is not None:
            # Check if username is already taken
            existing = await session.execute(
                select(User).where(
                    and_(User.username == user_data.username, User.id != user_id)
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            update_data["username"] = user_data.username
        
        if user_data.first_name is not None:
            update_data["first_name"] = user_data.first_name
        
        if user_data.last_name is not None:
            update_data["last_name"] = user_data.last_name
        
        if user_data.role is not None and current_user.role.value == "admin":
            update_data["role"] = user_data.role
        
        if user_data.is_active is not None and current_user.role.value == "admin":
            update_data["is_active"] = user_data.is_active
        
        # Update user
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await session.execute(
                update(User).where(User.id == user_id).values(**update_data)
            )
            await session.commit()
            
            # Refresh user object
            await session.refresh(user)
            
            # Log user update
            client_ip = get_remote_address(request)
            new_values = {k: str(v) for k, v in update_data.items() if k != "updated_at"}
            
            await AuditService.log_action(
                session,
                AuditLogCreate(
                    user_id=current_user.id,
                    username=current_user.username,
                    action=AuditAction.USER_UPDATED,
                    resource_type="user",
                    resource_id=str(user_id),
                    ip_address=client_ip,
                    old_values=old_values,
                    new_values=new_values,
                    details={"updated_by": current_user.username}
                )
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
        logger.error(f"User update error: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete user (soft delete for GDPR compliance) - admin only
    """
    try:
        # Prevent self-deletion
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Get user to delete
        result = await session.execute(
            select(User).where(
                and_(User.id == user_id, User.deleted_at.is_(None))
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Soft delete user
        from datetime import datetime
        await session.execute(
            update(User).where(User.id == user_id).values(
                deleted_at=datetime.utcnow(),
                is_active=False,
                email=f"deleted_{user_id}@deleted.local",
                username=f"deleted_{user_id}"
            )
        )
        await session.commit()
        
        # Log user deletion
        client_ip = get_remote_address(request)
        await AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                username=current_user.username,
                action=AuditAction.USER_DELETED,
                resource_type="user",
                resource_id=str(user_id),
                ip_address=client_ip,
                details={
                    "deleted_user_email": user.email,
                    "deletion_type": "soft_delete",
                    "deleted_by": current_user.username
                }
            )
        )
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User deletion error: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )


@router.post("/{user_id}/export-data")
async def export_user_data(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Export user data for GDPR compliance
    """
    try:
        export_data = await AuditService.export_user_data(
            session, user_id, current_user
        )
        
        return export_data
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Data export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data export failed"
        )

