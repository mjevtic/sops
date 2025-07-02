"""
Integration delete handlers
"""
import logging
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_

from database import get_session
from models.integration import Integration
from models.audit import AuditLogCreate, AuditAction
from models.user import User
from services.audit import AuditService
from routes.auth import get_current_user
from middleware import rate_limit_by_user, get_remote_address

logger = logging.getLogger(__name__)

@rate_limit_by_user("5/minute")
def delete_integration(
    integration_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Delete an integration (soft delete)
    """
    try:
        # Get integration to delete
        result = session.execute(
            select(Integration).where(
                and_(
                    Integration.id == integration_id,
                    Integration.user_id == current_user.id,
                    Integration.deleted_at.is_(None)
                )
            )
        )
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        # Soft delete integration
        session.execute(
            update(Integration).where(Integration.id == integration_id).values(
                deleted_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        session.commit()
        
        # Log integration deletion
        client_ip = get_remote_address(request)
        
        AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                action=AuditAction.INTEGRATION_DELETED,
                resource_id=str(integration.id),
                resource_type="integration",
                details={
                    "name": integration.name,
                    "platform": integration.platform.value,
                    "client_ip": client_ip
                }
            )
        )
        
        return {"message": "Integration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration deletion error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integration deletion failed"
        )
