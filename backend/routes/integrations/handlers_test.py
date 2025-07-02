"""
Integration test handlers
"""
import json
import logging
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_

from database import get_session
from models.integration import Integration, IntegrationCredential, IntegrationStatus
from models.audit import AuditLogCreate, AuditAction
from models.user import User
from services.audit import AuditService
from routes.auth import get_current_user
from middleware import rate_limit_by_user, get_remote_address
from config import decrypt_data

from .connection_tests import test_integration_connection

logger = logging.getLogger(__name__)

@rate_limit_by_user("5/minute")
def test_integration(
    integration_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Test integration connection
    """
    try:
        # Get integration
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
        
        # Get credentials
        cred_result = session.execute(
            select(IntegrationCredential).where(
                IntegrationCredential.integration_id == integration_id
            )
        )
        credential = cred_result.scalar_one_or_none()
        
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integration has no credentials"
            )
        
        # Decrypt credentials
        decrypted_credentials = json.loads(decrypt_data(credential.encrypted_credentials))
        
        # Test connection
        test_result = test_integration_connection(integration, decrypted_credentials)
        
        # Update integration status based on test result
        if test_result["success"]:
            session.execute(
                update(Integration).where(Integration.id == integration_id).values(
                    status=IntegrationStatus.ACTIVE,
                    health_check_status="healthy",
                    last_health_check=datetime.utcnow(),
                    last_error=None,
                    updated_at=datetime.utcnow()
                )
            )
        else:
            session.execute(
                update(Integration).where(Integration.id == integration_id).values(
                    status=IntegrationStatus.ERROR,
                    health_check_status="error",
                    last_health_check=datetime.utcnow(),
                    last_error=test_result.get("error", "Unknown error"),
                    updated_at=datetime.utcnow()
                )
            )
        
        session.commit()
        
        # Log test action
        client_ip = get_remote_address(request)
        
        AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                action=AuditAction.INTEGRATION_TESTED,
                resource_id=str(integration.id),
                resource_type="integration",
                details={
                    "name": integration.name,
                    "platform": integration.platform.value,
                    "success": test_result["success"],
                    "client_ip": client_ip
                }
            )
        )
        
        return {
            "integration_id": integration.id,
            "name": integration.name,
            "platform": integration.platform.value,
            "test_result": test_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration test error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integration test failed"
        )
