"""
Integration update handlers
"""
import json
import logging
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_

from database import get_session
from models.integration import (
    Integration, IntegrationCredential, IntegrationUpdate, IntegrationStatus
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
def update_integration(
    integration_id: int,
    integration_data: IntegrationUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update an integration
    """
    try:
        # Get integration to update
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
        
        # Check if name is already taken by another integration
        if integration_data.name and integration_data.name != integration.name:
            name_result = session.execute(
                select(Integration).where(
                    and_(
                        Integration.name == integration_data.name,
                        Integration.user_id == current_user.id,
                        Integration.id != integration_id,
                        Integration.deleted_at.is_(None)
                    )
                )
            )
            existing = name_result.scalar_one_or_none()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Integration with this name already exists"
                )
        
        # Update credentials if provided
        if integration_data.credentials is not None:
            # Get existing credential record
            cred_result = session.execute(
                select(IntegrationCredential).where(
                    IntegrationCredential.integration_id == integration_id
                )
            )
            credential = cred_result.scalar_one_or_none()
            
            # Determine credential type
            credential_type = determine_credential_type(
                integration.platform.value, 
                integration_data.credentials
            )
            
            # Encrypt credentials
            encrypted_credentials = encrypt_data(json.dumps(integration_data.credentials))
            
            if credential:
                # Update existing credential
                credential.credential_type = credential_type
                credential.encrypted_credentials = encrypted_credentials
                credential.updated_at = datetime.utcnow()
            else:
                # Create new credential
                new_credential = IntegrationCredential(
                    integration_id=integration_id,
                    credential_type=credential_type,
                    encrypted_credentials=encrypted_credentials,
                    created_at=datetime.utcnow()
                )
                session.add(new_credential)
            
            # Test connection with new credentials
            test_result = test_integration_connection(integration, integration_data.credentials)
            
            if test_result["success"]:
                integration_data.status = IntegrationStatus.ACTIVE
                integration_data.health_check_status = "healthy"
                integration_data.last_error = None
            else:
                integration_data.status = IntegrationStatus.ERROR
                integration_data.health_check_status = "error"
                integration_data.last_error = test_result.get("error", "Unknown error")
            
            integration_data.last_health_check = datetime.utcnow()
        
        # Prepare update data
        update_data = {}
        if integration_data.name is not None:
            update_data["name"] = integration_data.name
        if integration_data.description is not None:
            update_data["description"] = integration_data.description
        if integration_data.status is not None:
            update_data["status"] = integration_data.status
        if integration_data.health_check_status is not None:
            update_data["health_check_status"] = integration_data.health_check_status
        if integration_data.last_health_check is not None:
            update_data["last_health_check"] = integration_data.last_health_check
        if integration_data.last_error is not None:
            update_data["last_error"] = integration_data.last_error
        
        # Update integration
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            session.execute(
                update(Integration).where(Integration.id == integration_id).values(**update_data)
            )
            session.commit()
            
            # Refresh integration object
            session.refresh(integration)
            
            # Log integration update
            client_ip = get_remote_address(request)
            new_values = {k: str(v) for k, v in update_data.items() if k != "updated_at"}
            
            AuditService.log_action(
                session,
                AuditLogCreate(
                    user_id=current_user.id,
                    action=AuditAction.INTEGRATION_UPDATED,
                    resource_id=str(integration.id),
                    resource_type="integration",
                    details={
                        "name": integration.name,
                        "platform": integration.platform.value,
                        "status": integration.status.value,
                        "client_ip": client_ip,
                        "updated_fields": list(new_values.keys()),
                        "new_values": new_values
                    }
                )
            )
        
        # Return updated integration
        return {
            "id": integration.id,
            "name": integration.name,
            "description": integration.description,
            "platform": integration.platform.value,
            "status": integration.status.value,
            "health_check_status": integration.health_check_status,
            "last_health_check": integration.last_health_check,
            "last_error": integration.last_error,
            "created_at": integration.created_at,
            "updated_at": integration.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration update error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integration update failed"
        )
