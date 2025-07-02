"""
Integration execution handlers
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from database import get_session
from models.integration import Integration, IntegrationCredential, IntegrationStatus
from models.audit import AuditLogCreate, AuditAction
from models.user import User
from services.audit import AuditService
from routes.auth import get_current_user
from middleware import rate_limit_by_user, get_remote_address
from config import decrypt_data

from .utils import get_integration_handler

logger = logging.getLogger(__name__)

@rate_limit_by_user("20/minute")
def execute_integration_action(
    integration_id: int,
    action_data: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Execute an action using the integration
    """
    try:
        # Get action name
        action_name = action_data.get("action")
        if not action_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action name is required"
            )
        
        # Get parameters
        parameters = action_data.get("parameters", {})
        
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
        
        # Check if integration is active
        if integration.status != IntegrationStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Integration is not active (status: {integration.status.value})"
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
        
        # Get integration handler
        handler = get_integration_handler(integration.platform.value, decrypted_credentials)
        
        # Check if action is supported
        if not hasattr(handler, action_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action '{action_name}' is not supported by this integration"
            )
        
        # Execute action
        action_method = getattr(handler, action_name)
        result = action_method(**parameters)
        
        # Log action execution
        client_ip = get_remote_address(request)
        
        AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                action=AuditAction.INTEGRATION_ACTION_EXECUTED,
                resource_id=str(integration.id),
                resource_type="integration",
                details={
                    "name": integration.name,
                    "platform": integration.platform.value,
                    "action": action_name,
                    "client_ip": client_ip,
                    "success": result.get("success", True),
                    "message": result.get("message")
                }
            )
        )
        
        return {
            "success": True,
            "message": "Action executed successfully",
            "integration_id": integration_id,
            "action": action_name,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration action execution error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Action execution failed: {str(e)}"
        )
