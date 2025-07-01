"""
Audit service for compliance and security logging
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from models.audit import AuditLog, AuditAction, AuditLogCreate, AuditLogFilter
from models.user import User
import logging

logger = logging.getLogger(__name__)


class AuditService:
    """Service for managing audit logs and compliance"""
    
    @staticmethod
    async def log_action(
        session: AsyncSession,
        audit_data: AuditLogCreate,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """
        Log an action for audit purposes
        """
        try:
            # Generate request ID if not provided
            if not request_id:
                request_id = str(uuid.uuid4())
            
            audit_log = AuditLog(
                user_id=audit_data.user_id,
                username=audit_data.username,
                action=audit_data.action,
                resource_type=audit_data.resource_type,
                resource_id=audit_data.resource_id,
                rule_id=audit_data.rule_id,
                ip_address=audit_data.ip_address,
                user_agent=audit_data.user_agent,
                request_id=request_id,
                details=audit_data.details,
                old_values=audit_data.old_values,
                new_values=audit_data.new_values,
                status=audit_data.status,
                error_message=audit_data.error_message,
                duration_ms=audit_data.duration_ms
            )
            
            session.add(audit_log)
            await session.commit()
            
            logger.info(f"Audit log created: {audit_data.action} by {audit_data.username}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            await session.rollback()
            raise
    
    @staticmethod
    async def get_audit_logs(
        session: AsyncSession,
        filters: AuditLogFilter,
        current_user: User
    ) -> List[AuditLog]:
        """
        Get audit logs with filtering and access control
        """
        try:
            query = select(AuditLog)
            
            # Apply filters
            conditions = []
            
            if filters.user_id:
                conditions.append(AuditLog.user_id == filters.user_id)
            
            if filters.action:
                conditions.append(AuditLog.action == filters.action)
            
            if filters.resource_type:
                conditions.append(AuditLog.resource_type == filters.resource_type)
            
            if filters.resource_id:
                conditions.append(AuditLog.resource_id == filters.resource_id)
            
            if filters.rule_id:
                conditions.append(AuditLog.rule_id == filters.rule_id)
            
            if filters.status:
                conditions.append(AuditLog.status == filters.status)
            
            if filters.start_date:
                conditions.append(AuditLog.timestamp >= filters.start_date)
            
            if filters.end_date:
                conditions.append(AuditLog.timestamp <= filters.end_date)
            
            # Access control: non-admin users can only see their own logs
            if current_user.role.value != "admin":
                conditions.append(AuditLog.user_id == current_user.id)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Order by timestamp descending
            query = query.order_by(desc(AuditLog.timestamp))
            
            # Apply pagination
            query = query.offset(filters.offset).limit(filters.limit)
            
            result = await session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            raise
    
    @staticmethod
    async def get_security_events(
        session: AsyncSession,
        hours: int = 24,
        current_user: User = None
    ) -> List[AuditLog]:
        """
        Get recent security events (admin only)
        """
        if current_user and current_user.role.value != "admin":
            raise PermissionError("Only administrators can view security events")
        
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            security_actions = [
                AuditAction.USER_LOGIN_FAILED,
                AuditAction.UNAUTHORIZED_ACCESS,
                AuditAction.RATE_LIMIT_EXCEEDED,
                AuditAction.WEBHOOK_SIGNATURE_INVALID
            ]
            
            query = select(AuditLog).where(
                and_(
                    AuditLog.timestamp >= since,
                    AuditLog.action.in_(security_actions)
                )
            ).order_by(desc(AuditLog.timestamp))
            
            result = await session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error retrieving security events: {e}")
            raise
    
    @staticmethod
    async def get_user_activity(
        session: AsyncSession,
        user_id: int,
        days: int = 30,
        current_user: User = None
    ) -> List[AuditLog]:
        """
        Get user activity logs
        """
        # Access control: users can only see their own activity, admins can see all
        if current_user:
            if current_user.role.value != "admin" and current_user.id != user_id:
                raise PermissionError("Access denied")
        
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            query = select(AuditLog).where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= since
                )
            ).order_by(desc(AuditLog.timestamp))
            
            result = await session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error retrieving user activity: {e}")
            raise
    
    @staticmethod
    async def export_user_data(
        session: AsyncSession,
        user_id: int,
        current_user: User
    ) -> Dict[str, Any]:
        """
        Export all user data for GDPR compliance
        """
        # Access control: users can only export their own data, admins can export any
        if current_user.role.value != "admin" and current_user.id != user_id:
            raise PermissionError("Access denied")
        
        try:
            # Get user data
            user_result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            # Get audit logs
            audit_result = await session.execute(
                select(AuditLog).where(AuditLog.user_id == user_id)
                .order_by(desc(AuditLog.timestamp))
            )
            audit_logs = audit_result.scalars().all()
            
            # Prepare export data
            export_data = {
                "user_data": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role.value,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None
                },
                "audit_logs": [
                    {
                        "action": log.action.value,
                        "resource_type": log.resource_type,
                        "timestamp": log.timestamp.isoformat(),
                        "ip_address": log.ip_address,
                        "details": log.details
                    }
                    for log in audit_logs
                ],
                "export_timestamp": datetime.utcnow().isoformat(),
                "export_requested_by": current_user.username
            }
            
            # Log the data export
            await AuditService.log_action(
                session,
                AuditLogCreate(
                    user_id=current_user.id,
                    username=current_user.username,
                    action=AuditAction.DATA_EXPORTED,
                    resource_type="user",
                    resource_id=str(user_id),
                    details={
                        "exported_by": current_user.username,
                        "data_types": ["user_profile", "audit_logs"]
                    }
                )
            )
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            raise
    
    @staticmethod
    async def delete_user_data(
        session: AsyncSession,
        user_id: int,
        current_user: User,
        reason: str = "user_request"
    ) -> bool:
        """
        Delete user data for GDPR compliance (soft delete)
        """
        # Only admins or the user themselves can delete data
        if current_user.role.value != "admin" and current_user.id != user_id:
            raise PermissionError("Access denied")
        
        try:
            # Get user
            user_result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            # Soft delete user (mark as deleted)
            user.deleted_at = datetime.utcnow()
            user.is_active = False
            user.email = f"deleted_{user.id}@deleted.local"
            user.username = f"deleted_{user.id}"
            user.first_name = None
            user.last_name = None
            
            await session.commit()
            
            # Log the data deletion
            await AuditService.log_action(
                session,
                AuditLogCreate(
                    user_id=current_user.id,
                    username=current_user.username,
                    action=AuditAction.DATA_DELETED,
                    resource_type="user",
                    resource_id=str(user_id),
                    details={
                        "deleted_by": current_user.username,
                        "reason": reason,
                        "deletion_type": "soft_delete"
                    }
                )
            )
            
            logger.info(f"User data deleted: {user_id} by {current_user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            await session.rollback()
            raise
    
    @staticmethod
    async def cleanup_old_logs(
        session: AsyncSession,
        retention_days: int = 365
    ) -> int:
        """
        Clean up old audit logs based on retention policy
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Get count of logs to be deleted
            count_result = await session.execute(
                select(AuditLog).where(AuditLog.timestamp < cutoff_date)
            )
            logs_to_delete = len(count_result.scalars().all())
            
            # Delete old logs
            await session.execute(
                AuditLog.__table__.delete().where(AuditLog.timestamp < cutoff_date)
            )
            await session.commit()
            
            logger.info(f"Cleaned up {logs_to_delete} old audit logs")
            return logs_to_delete
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            await session.rollback()
            raise

