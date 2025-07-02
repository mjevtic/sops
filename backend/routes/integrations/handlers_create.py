"""
Integration creation handlers
"""
import json
import logging
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from database import get_session
from models.integration import (
    Integration, IntegrationCredential, IntegrationCreate, IntegrationStatus
)
from models.audit import AuditLogCreate, AuditAction
from models.user import User
from services.audit import AuditService
from routes.auth import get_current_user
from middleware import rate_limit_by_user, get_remote_address
from config import encrypt_data

from .utils import determine_credential_type
from .connection_tests import test_integration_connection

logger = logging.getLogger(__name__)

@rate_limit_by_user("5/minute")
def create_integration(
    integration_data: IntegrationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a new integration
    """
    try:
        # Check if integration with same name already exists
        result = session.execute(
            select(Integration).where(
                Integration.name == integration_data.name,
                Integration.user_id == current_user.id,
                Integration.deleted_at.is_(None)
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Integration with this name already exists"
            )
        
        # Create integration
        integration = Integration(
            user_id=current_user.id,
            name=integration_data.name,
            description=integration_data.description,
            platform=integration_data.platform,
            status=IntegrationStatus.PENDING,
            health_check_status="unknown",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(integration)
        session.commit()
        session.refresh(integration)
        
        # Create credentials if provided
        if integration_data.credentials:
            # Determine credential type
            credential_type = determine_credential_type(
                integration_data.platform.value, 
                integration_data.credentials
            )
            
            # Encrypt credentials
            encrypted_credentials = encrypt_data(json.dumps(integration_data.credentials))
            
            # Create credential record
            credential = IntegrationCredential(
                integration_id=integration.id,
                credential_type=credential_type,
                encrypted_credentials=encrypted_credentials,
                created_at=datetime.utcnow()
            )
            
            session.add(credential)
            session.commit()
            
            # Test connection
            test_result = test_integration_connection(integration, integration_data.credentials)
            
            if test_result["success"]:
                integration.status = IntegrationStatus.ACTIVE
                integration.health_check_status = "healthy"
            else:
                integration.status = IntegrationStatus.ERROR
                integration.health_check_status = "error"
                integration.last_error = test_result.get("error", "Unknown error")
            
            integration.last_health_check = datetime.utcnow()
            session.commit()
        
        # Log integration creation
        client_ip = get_remote_address(request)
        
        AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                action=AuditAction.INTEGRATION_CREATED,
                resource_id=str(integration.id),
                resource_type="integration",
                details={
                    "name": integration.name,
                    "platform": integration.platform.value,
                    "status": integration.status.value,
                    "client_ip": client_ip
                }
            )
        )
        
        return {
            "id": integration.id,
            "name": integration.name,
            "description": integration.description,
            "platform": integration.platform.value,
            "status": integration.status.value,
            "health_check_status": integration.health_check_status,
            "created_at": integration.created_at,
            "updated_at": integration.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration creation error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integration creation failed"
        )
