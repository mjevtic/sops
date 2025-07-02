"""
Integration read handlers
"""
import logging
from typing import List, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from database import get_session
from models.integration import (
    Integration, IntegrationResponse, IntegrationType, IntegrationStatus
)
from models.user import User
from routes.auth import get_current_user
from middleware import rate_limit_by_user

from .utils import get_supported_platforms, get_platform_info

logger = logging.getLogger(__name__)

@rate_limit_by_user("20/minute")
def get_integrations(
    request: Request,
    platform: Optional[IntegrationType] = None,
    status_filter: Optional[IntegrationStatus] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get user's integrations
    """
    try:
        # Build query
        query = select(Integration).where(
            and_(
                Integration.user_id == current_user.id,
                Integration.deleted_at.is_(None)
            )
        )
        
        # Apply filters
        if platform:
            query = query.where(Integration.platform == platform)
        
        if status_filter:
            query = query.where(Integration.status == status_filter)
        
        # Order by name
        query = query.order_by(Integration.name)
        
        # Execute query
        result = session.execute(query)
        integrations = result.scalars().all()
        
        # Format response
        response = []
        for integration in integrations:
            platform_info = get_platform_info(integration.platform)
            
            response.append(IntegrationResponse(
                id=integration.id,
                name=integration.name,
                description=integration.description,
                platform=integration.platform,
                status=integration.status,
                health_check_status=integration.health_check_status,
                last_health_check=integration.last_health_check,
                last_error=integration.last_error,
                created_at=integration.created_at,
                updated_at=integration.updated_at,
                platform_info=platform_info
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Get integrations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve integrations"
        )

@rate_limit_by_user("20/minute")
def get_integration(
    integration_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get a specific integration by ID
    """
    try:
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
        
        # Get platform info
        platform_info = get_platform_info(integration.platform)
        
        # Format response
        return IntegrationResponse(
            id=integration.id,
            name=integration.name,
            description=integration.description,
            platform=integration.platform,
            status=integration.status,
            health_check_status=integration.health_check_status,
            last_health_check=integration.last_health_check,
            last_error=integration.last_error,
            created_at=integration.created_at,
            updated_at=integration.updated_at,
            platform_info=platform_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get integration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve integration"
        )

@rate_limit_by_user("10/minute")
def get_available_platforms(request: Request):
    """
    Get list of available integration platforms
    """
    try:
        platforms = get_supported_platforms()
        return {"platforms": platforms}
    except Exception as e:
        logger.error(f"Get platforms error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available platforms"
        )
