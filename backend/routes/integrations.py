"""
Integration management routes with enhanced Freshdesk and Zendesk support
"""
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from database import get_session
from models.integration import (
    Integration, IntegrationCredential, IntegrationCreate, IntegrationUpdate, 
    IntegrationResponse, IntegrationType, IntegrationStatus
)
from models.audit import AuditLogCreate, AuditAction
from models.user import User
from services.audit import AuditService
from routes.auth import get_current_user
from middleware import rate_limit_by_user, get_remote_address
from config import encrypt_data, decrypt_data
import logging
from datetime import datetime

# Import enhanced integration modules
from modules.freshdesk import FreshdeskAction
from modules.zendesk import ZendeskAction
from modules.slack import SlackAction
from modules.trello import TrelloAction
from modules.notion import NotionAction
from modules.google_sheets import GoogleSheetsAction

logger = logging.getLogger(__name__)
router = APIRouter()


# Integration platform handlers
INTEGRATION_HANDLERS = {
    'freshdesk': FreshdeskAction,
    'zendesk': ZendeskAction,
    'slack': SlackAction,
    'trello': TrelloAction,
    'notion': NotionAction,
    'google_sheets': GoogleSheetsAction
}


def get_integration_handler(platform: str, credentials: Dict[str, Any]):
    """Get integration handler for platform"""
    handler_class = INTEGRATION_HANDLERS.get(platform)
    if not handler_class:
        raise ValueError(f"Unsupported platform: {platform}")
    
    try:
        if platform == 'freshdesk':
            return handler_class(
                domain=credentials.get('domain'),
                api_key=credentials.get('api_key')
            )
        elif platform == 'zendesk':
            return handler_class(
                subdomain=credentials.get('subdomain'),
                email=credentials.get('email'),
                api_token=credentials.get('api_token')
            )
        elif platform == 'slack':
            return handler_class(
                bot_token=credentials.get('bot_token'),
                app_token=credentials.get('app_token')
            )
        elif platform == 'trello':
            return handler_class(
                api_key=credentials.get('api_key'),
                token=credentials.get('token')
            )
        elif platform == 'notion':
            return handler_class(
                token=credentials.get('token')
            )
        elif platform == 'google_sheets':
            return handler_class(
                credentials_json=credentials.get('credentials_json')
            )
        else:
            raise ValueError(f"Handler not implemented for platform: {platform}")
    except Exception as e:
        logger.error(f"Failed to create handler for {platform}: {e}")
        raise ValueError(f"Invalid credentials for {platform}: {e}")


@router.get("/platforms")
async def get_supported_platforms():
    """
    Get list of supported integration platforms with their requirements
    """
    platforms = {
        'freshdesk': {
            'name': 'Freshdesk',
            'description': 'Customer support and helpdesk platform',
            'credentials': [
                {'name': 'domain', 'type': 'string', 'required': True, 'description': 'Freshdesk domain (e.g., company.freshdesk.com)'},
                {'name': 'api_key', 'type': 'string', 'required': True, 'description': 'Freshdesk API key', 'sensitive': True}
            ],
            'capabilities': [
                'Create and update tickets',
                'Add notes and replies',
                'Manage contacts and companies',
                'Time tracking',
                'Bulk operations',
                'Webhook processing'
            ],
            'webhook_events': [
                'ticket_created', 'ticket_updated', 'ticket_resolved', 'ticket_closed',
                'note_created', 'contact_created', 'contact_updated'
            ]
        },
        'zendesk': {
            'name': 'Zendesk',
            'description': 'Customer service and engagement platform',
            'credentials': [
                {'name': 'subdomain', 'type': 'string', 'required': True, 'description': 'Zendesk subdomain (e.g., company for company.zendesk.com)'},
                {'name': 'email', 'type': 'string', 'required': True, 'description': 'Agent email address'},
                {'name': 'api_token', 'type': 'string', 'required': True, 'description': 'Zendesk API token', 'sensitive': True}
            ],
            'capabilities': [
                'Create and update tickets',
                'Add comments (public/private)',
                'Manage users and organizations',
                'Apply macros',
                'Search tickets and users',
                'Bulk operations',
                'Webhook processing'
            ],
            'webhook_events': [
                'ticket.created', 'ticket.updated', 'ticket.solved', 'ticket.closed',
                'comment.created', 'user.created', 'user.updated',
                'organization.created', 'organization.updated'
            ]
        },
        'slack': {
            'name': 'Slack',
            'description': 'Team communication and collaboration platform',
            'credentials': [
                {'name': 'bot_token', 'type': 'string', 'required': True, 'description': 'Slack Bot User OAuth Token', 'sensitive': True},
                {'name': 'app_token', 'type': 'string', 'required': False, 'description': 'Slack App-Level Token', 'sensitive': True}
            ],
            'capabilities': [
                'Send messages to channels and users',
                'Create and manage channels',
                'Invite users to channels',
                'Upload files and attachments',
                'Manage user presence'
            ]
        },
        'trello': {
            'name': 'Trello',
            'description': 'Project management and collaboration tool',
            'credentials': [
                {'name': 'api_key', 'type': 'string', 'required': True, 'description': 'Trello API key', 'sensitive': True},
                {'name': 'token', 'type': 'string', 'required': True, 'description': 'Trello user token', 'sensitive': True}
            ],
            'capabilities': [
                'Create and update cards',
                'Move cards between lists',
                'Add comments and attachments',
                'Manage checklists and labels',
                'Board and list management'
            ]
        },
        'notion': {
            'name': 'Notion',
            'description': 'All-in-one workspace for notes, docs, and collaboration',
            'credentials': [
                {'name': 'token', 'type': 'string', 'required': True, 'description': 'Notion Integration Token', 'sensitive': True}
            ],
            'capabilities': [
                'Create and update pages',
                'Manage databases and records',
                'Add comments and mentions',
                'Query and filter data',
                'File and media management'
            ]
        },
        'google_sheets': {
            'name': 'Google Sheets',
            'description': 'Cloud-based spreadsheet application',
            'credentials': [
                {'name': 'credentials_json', 'type': 'text', 'required': True, 'description': 'Google Service Account JSON credentials', 'sensitive': True}
            ],
            'capabilities': [
                'Read and write spreadsheet data',
                'Create and manage sheets',
                'Append and update rows',
                'Batch operations',
                'Formula and formatting support'
            ]
        }
    }
    
    return {
        "success": True,
        "platforms": platforms,
        "total_platforms": len(platforms)
    }


@router.get("/actions/{platform}")
async def get_platform_actions(platform: str):
    """
    Get available actions for a specific platform
    """
    try:
        handler_class = INTEGRATION_HANDLERS.get(platform)
        if not handler_class:
            raise HTTPException(
                status_code=404,
                detail=f"Platform '{platform}' not supported"
            )
        
        actions = handler_class.get_available_actions()
        
        return {
            "success": True,
            "platform": platform,
            "actions": actions,
            "total_actions": len(actions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get actions for platform {platform}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get platform actions: {str(e)}"
        )


@router.post("/", response_model=IntegrationResponse)
@rate_limit_by_user("10/minute")
async def create_integration(
    integration_data: IntegrationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new integration
    """
    try:
        # Check if integration already exists for this platform
        existing_result = await session.execute(
            select(Integration).where(
                and_(
                    Integration.user_id == current_user.id,
                    Integration.platform == integration_data.platform,
                    Integration.deleted_at.is_(None)
                )
            )
        )
        existing_integration = existing_result.scalar_one_or_none()
        
        if existing_integration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Integration for {integration_data.platform} already exists"
            )
        
        # Create new integration
        new_integration = Integration(
            user_id=current_user.id,
            name=integration_data.name,
            platform=integration_data.platform,
            config=integration_data.config,
            status=IntegrationStatus.PENDING_SETUP
        )
        
        session.add(new_integration)
        await session.commit()
        await session.refresh(new_integration)
        
        # Encrypt and store credentials
        encrypted_credentials = encrypt_data(json.dumps(integration_data.credentials))
        
        credential = IntegrationCredential(
            integration_id=new_integration.id,
            encrypted_credentials=encrypted_credentials,
            credential_type=determine_credential_type(integration_data.platform, integration_data.credentials)
        )
        
        session.add(credential)
        await session.commit()
        
        # Test the integration
        test_result = await test_integration_connection(new_integration, integration_data.credentials)
        
        # Update status based on test result
        if test_result["success"]:
            new_integration.status = IntegrationStatus.ACTIVE
            new_integration.health_check_status = "healthy"
        else:
            new_integration.status = IntegrationStatus.ERROR
            new_integration.last_error = test_result.get("error", "Connection test failed")
        
        new_integration.last_health_check = datetime.utcnow()
        await session.commit()
        
        # Log integration creation
        client_ip = get_remote_address(request)
        await AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                username=current_user.username,
                action=AuditAction.INTEGRATION_CREATED,
                resource_type="integration",
                resource_id=str(new_integration.id),
                ip_address=client_ip,
                details={
                    "integration_name": new_integration.name,
                    "platform": new_integration.platform.value,
                    "status": new_integration.status.value,
                    "test_result": test_result["success"]
                }
            )
        )
        
        return IntegrationResponse(
            id=new_integration.id,
            name=new_integration.name,
            platform=new_integration.platform,
            status=new_integration.status,
            config=new_integration.config,
            last_health_check=new_integration.last_health_check,
            health_check_status=new_integration.health_check_status,
            last_error=new_integration.last_error,
            total_actions_executed=new_integration.total_actions_executed,
            last_action_executed_at=new_integration.last_action_executed_at,
            created_at=new_integration.created_at,
            updated_at=new_integration.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration creation error: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integration creation failed"
        )


@router.get("/", response_model=List[IntegrationResponse])
@rate_limit_by_user("30/minute")
async def get_integrations(
    platform: Optional[IntegrationType] = None,
    status_filter: Optional[IntegrationStatus] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get user's integrations
    """
    try:
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
        
        # Order by creation date
        query = query.order_by(Integration.created_at.desc())
        
        result = await session.execute(query)
        integrations = result.scalars().all()
        
        return [
            IntegrationResponse(
                id=integration.id,
                name=integration.name,
                platform=integration.platform,
                status=integration.status,
                config=integration.config,
                last_health_check=integration.last_health_check,
                health_check_status=integration.health_check_status,
                last_error=integration.last_error,
                total_actions_executed=integration.total_actions_executed,
                last_action_executed_at=integration.last_action_executed_at,
                created_at=integration.created_at,
                updated_at=integration.updated_at
            )
            for integration in integrations
        ]
        
    except Exception as e:
        logger.error(f"Get integrations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve integrations"
        )


@router.get("/{integration_id}", response_model=IntegrationResponse)
@rate_limit_by_user("30/minute")
async def get_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific integration by ID
    """
    try:
        result = await session.execute(
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
        
        return IntegrationResponse(
            id=integration.id,
            name=integration.name,
            platform=integration.platform,
            status=integration.status,
            config=integration.config,
            last_health_check=integration.last_health_check,
            health_check_status=integration.health_check_status,
            last_error=integration.last_error,
            total_actions_executed=integration.total_actions_executed,
            last_action_executed_at=integration.last_action_executed_at,
            created_at=integration.created_at,
            updated_at=integration.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get integration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve integration"
        )


@router.put("/{integration_id}", response_model=IntegrationResponse)
@rate_limit_by_user("10/minute")
async def update_integration(
    integration_id: int,
    integration_data: IntegrationUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update an integration
    """
    try:
        # Get integration to update
        result = await session.execute(
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
        
        # Store old values for audit
        old_values = {
            "name": integration.name,
            "status": integration.status.value,
            "config": integration.config
        }
        
        # Prepare update data
        update_data = {}
        
        if integration_data.name is not None:
            update_data["name"] = integration_data.name
        
        if integration_data.status is not None:
            update_data["status"] = integration_data.status
        
        if integration_data.config is not None:
            update_data["config"] = integration_data.config
        
        # Update credentials if provided
        if integration_data.credentials is not None:
            # Get existing credential record
            cred_result = await session.execute(
                select(IntegrationCredential).where(
                    IntegrationCredential.integration_id == integration_id
                )
            )
            credential = cred_result.scalar_one_or_none()
            
            if credential:
                # Update existing credentials
                encrypted_credentials = encrypt_data(json.dumps(integration_data.credentials))
                credential.encrypted_credentials = encrypted_credentials
                credential.updated_at = datetime.utcnow()
                credential.credential_type = determine_credential_type(integration.platform, integration_data.credentials)
            else:
                # Create new credential record
                encrypted_credentials = encrypt_data(json.dumps(integration_data.credentials))
                new_credential = IntegrationCredential(
                    integration_id=integration_id,
                    encrypted_credentials=encrypted_credentials,
                    credential_type=determine_credential_type(integration.platform, integration_data.credentials)
                )
                session.add(new_credential)
            
            # Test connection with new credentials
            test_result = await test_integration_connection(integration, integration_data.credentials)
            
            if test_result["success"]:
                update_data["status"] = IntegrationStatus.ACTIVE
                update_data["health_check_status"] = "healthy"
                update_data["last_error"] = None
            else:
                update_data["status"] = IntegrationStatus.ERROR
                update_data["last_error"] = test_result.get("error", "Connection test failed")
            
            update_data["last_health_check"] = datetime.utcnow()
        
        # Update integration
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await session.execute(
                update(Integration).where(Integration.id == integration_id).values(**update_data)
            )
            await session.commit()
            
            # Refresh integration object
            await session.refresh(integration)
            
            # Log integration update
            client_ip = get_remote_address(request)
            new_values = {k: str(v) for k, v in update_data.items() if k != "updated_at"}
            
            await AuditService.log_action(
                session,
                AuditLogCreate(
                    user_id=current_user.id,
                    username=current_user.username,
                    action=AuditAction.INTEGRATION_UPDATED,
                    resource_type="integration",
                    resource_id=str(integration_id),
                    ip_address=client_ip,
                    old_values=old_values,
                    new_values=new_values,
                    details={"updated_by": current_user.username}
                )
            )
        
        return IntegrationResponse(
            id=integration.id,
            name=integration.name,
            platform=integration.platform,
            status=integration.status,
            config=integration.config,
            last_health_check=integration.last_health_check,
            health_check_status=integration.health_check_status,
            last_error=integration.last_error,
            total_actions_executed=integration.total_actions_executed,
            last_action_executed_at=integration.last_action_executed_at,
            created_at=integration.created_at,
            updated_at=integration.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration update error: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integration update failed"
        )


@router.delete("/{integration_id}")
@rate_limit_by_user("5/minute")
async def delete_integration(
    integration_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete an integration (soft delete)
    """
    try:
        # Get integration to delete
        result = await session.execute(
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
        await session.execute(
            update(Integration).where(Integration.id == integration_id).values(
                deleted_at=datetime.utcnow(),
                status=IntegrationStatus.INACTIVE
            )
        )
        await session.commit()
        
        # Log integration deletion
        client_ip = get_remote_address(request)
        await AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                username=current_user.username,
                action=AuditAction.INTEGRATION_DELETED,
                resource_type="integration",
                resource_id=str(integration_id),
                ip_address=client_ip,
                details={
                    "integration_name": integration.name,
                    "platform": integration.platform.value,
                    "deletion_type": "soft_delete",
                    "deleted_by": current_user.username
                }
            )
        )
        
        return {"message": "Integration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration deletion error: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integration deletion failed"
        )


@router.post("/{integration_id}/test")
@rate_limit_by_user("5/minute")
async def test_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Test an integration connection
    """
    try:
        # Get integration
        result = await session.execute(
            select(Integration).join(IntegrationCredential).where(
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
        cred_result = await session.execute(
            select(IntegrationCredential).where(
                IntegrationCredential.integration_id == integration_id
            )
        )
        credential = cred_result.scalar_one_or_none()
        
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Integration credentials not found"
            )
        
        # Decrypt credentials
        decrypted_credentials = json.loads(decrypt_data(credential.encrypted_credentials))
        
        # Test connection
        test_result = await test_integration_connection(integration, decrypted_credentials)
        
        # Update health check status
        await session.execute(
            update(Integration).where(Integration.id == integration_id).values(
                last_health_check=datetime.utcnow(),
                health_check_status="healthy" if test_result["success"] else "unhealthy",
                last_error=test_result.get("error") if not test_result["success"] else None
            )
        )
        await session.commit()
        
        return {
            "success": test_result["success"],
            "message": test_result.get("message", "Test completed"),
            "error": test_result.get("error"),
            "details": test_result.get("details", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integration test failed"
        )


@router.get("/platforms/available")
@rate_limit_by_user("10/minute")
async def get_available_platforms():
    """
    Get list of available integration platforms
    """
    try:
        platforms = []
        
        for platform in IntegrationType:
            platform_info = get_platform_info(platform)
            platforms.append(platform_info)
        
        return {"platforms": platforms}
        
    except Exception as e:
        logger.error(f"Get available platforms error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available platforms"
        )


# Helper functions
def determine_credential_type(platform: IntegrationType, credentials: dict) -> str:
    """Determine credential type based on platform and credentials"""
    try:
        if platform == IntegrationType.SLACK:
            if "bot_token" in credentials:
                return "bot_token"
            elif "oauth_token" in credentials:
                return "oauth_token"
        elif platform == IntegrationType.TRELLO:
            if "api_key" in credentials and "api_token" in credentials:
                return "api_key_token"
        elif platform == IntegrationType.NOTION:
            if "api_token" in credentials:
                return "api_token"
        elif platform == IntegrationType.GOOGLE_SHEETS:
            if "access_token" in credentials:
                return "oauth_token"
            elif "service_account_key" in credentials:
                return "service_account"
        
        return "unknown"
        
    except Exception as e:
        logger.error(f"Error determining credential type: {e}")
        return "unknown"


async def test_integration_connection(integration: Integration, credentials: dict) -> dict:
    """Test integration connection"""
    try:
        platform = integration.platform
        
        if platform == IntegrationType.SLACK:
            return await test_slack_connection(credentials)
        elif platform == IntegrationType.TRELLO:
            return await test_trello_connection(credentials)
        elif platform == IntegrationType.NOTION:
            return await test_notion_connection(credentials)
        elif platform == IntegrationType.GOOGLE_SHEETS:
            return await test_google_sheets_connection(credentials)
        else:
            return {
                "success": False,
                "error": f"Testing not implemented for platform: {platform}"
            }
            
    except Exception as e:
        logger.error(f"Integration connection test error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def test_slack_connection(credentials: dict) -> dict:
    """Test Slack connection"""
    try:
        import httpx
        
        bot_token = credentials.get("bot_token")
        if not bot_token:
            return {"success": False, "error": "Bot token is required"}
        
        url = "https://slack.com/api/auth.test"
        headers = {"Authorization": f"Bearer {bot_token}"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                return {
                    "success": True,
                    "message": "Slack connection successful",
                    "details": {
                        "team": result.get("team"),
                        "user": result.get("user")
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown Slack API error")
                }
                
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_trello_connection(credentials: dict) -> dict:
    """Test Trello connection"""
    try:
        import httpx
        
        api_key = credentials.get("api_key")
        api_token = credentials.get("api_token")
        
        if not api_key or not api_token:
            return {"success": False, "error": "API key and token are required"}
        
        url = "https://api.trello.com/1/members/me"
        params = {"key": api_key, "token": api_token}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "success": True,
                "message": "Trello connection successful",
                "details": {
                    "username": result.get("username"),
                    "full_name": result.get("fullName")
                }
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_notion_connection(credentials: dict) -> dict:
    """Test Notion connection"""
    try:
        import httpx
        
        api_token = credentials.get("api_token")
        if not api_token:
            return {"success": False, "error": "API token is required"}
        
        url = "https://api.notion.com/v1/users/me"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Notion-Version": "2022-06-28"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "success": True,
                "message": "Notion connection successful",
                "details": {
                    "user_type": result.get("type"),
                    "name": result.get("name")
                }
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_google_sheets_connection(credentials: dict) -> dict:
    """Test Google Sheets connection"""
    try:
        import httpx
        
        access_token = credentials.get("access_token")
        if not access_token:
            return {"success": False, "error": "Access token is required"}
        
        url = "https://www.googleapis.com/oauth2/v1/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "success": True,
                "message": "Google Sheets connection successful",
                "details": {
                    "email": result.get("email"),
                    "name": result.get("name")
                }
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_platform_info(platform: IntegrationType) -> dict:
    """Get platform information"""
    platform_configs = {
        IntegrationType.SLACK: {
            "name": "Slack",
            "description": "Send messages, create channels, and manage Slack workspaces",
            "required_credentials": ["bot_token"],
            "optional_credentials": ["signing_secret"],
            "actions": ["send_message", "send_direct_message", "create_channel", "invite_to_channel"],
            "setup_url": "https://api.slack.com/apps"
        },
        IntegrationType.TRELLO: {
            "name": "Trello",
            "description": "Create cards, manage boards, and automate Trello workflows",
            "required_credentials": ["api_key", "api_token"],
            "optional_credentials": [],
            "actions": ["create_card", "move_card", "add_comment", "create_checklist", "add_label"],
            "setup_url": "https://trello.com/app-key"
        },
        IntegrationType.NOTION: {
            "name": "Notion",
            "description": "Create pages, manage databases, and organize Notion workspaces",
            "required_credentials": ["api_token"],
            "optional_credentials": [],
            "actions": ["create_page", "update_page", "add_comment", "create_database_entry", "query_database"],
            "setup_url": "https://www.notion.so/my-integrations"
        },
        IntegrationType.GOOGLE_SHEETS: {
            "name": "Google Sheets",
            "description": "Manage spreadsheets, append data, and automate Google Sheets workflows",
            "required_credentials": ["access_token"],
            "optional_credentials": ["refresh_token"],
            "actions": ["append_row", "update_row", "create_sheet", "clear_range", "batch_update"],
            "setup_url": "https://console.developers.google.com/"
        }
    }
    
    config = platform_configs.get(platform, {})
    config["platform"] = platform.value
    
    return config




@router.post("/{integration_id}/test")
@rate_limit_by_user("5/minute")
async def test_integration(
    integration_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Test integration connection and functionality
    """
    try:
        # Get integration
        result = await session.execute(
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
                status_code=404,
                detail="Integration not found"
            )
        
        # Get credentials
        cred_result = await session.execute(
            select(IntegrationCredential).where(
                IntegrationCredential.integration_id == integration_id
            )
        )
        credential = cred_result.scalar_one_or_none()
        
        if not credential:
            raise HTTPException(
                status_code=400,
                detail="Integration credentials not found"
            )
        
        # Decrypt credentials
        decrypted_credentials = json.loads(decrypt_data(credential.encrypted_credentials))
        
        # Test connection
        test_result = await test_integration_connection(integration, decrypted_credentials)
        
        # Update integration status
        if test_result["success"]:
            integration.status = IntegrationStatus.ACTIVE
            integration.health_check_status = "healthy"
            integration.last_error = None
        else:
            integration.status = IntegrationStatus.ERROR
            integration.health_check_status = "unhealthy"
            integration.last_error = test_result.get("error", "Connection test failed")
        
        integration.last_health_check = datetime.utcnow()
        await session.commit()
        
        # Log test action
        client_ip = get_remote_address(request)
        await AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                username=current_user.username,
                action=AuditAction.INTEGRATION_TESTED,
                resource_type="integration",
                resource_id=str(integration_id),
                ip_address=client_ip,
                details={
                    "platform": integration.platform.value,
                    "test_result": test_result["success"],
                    "error": test_result.get("error")
                }
            )
        )
        
        return {
            "success": test_result["success"],
            "message": test_result.get("message", "Test completed"),
            "platform": integration.platform.value,
            "status": integration.status.value,
            "health_check_status": integration.health_check_status,
            "last_health_check": integration.last_health_check,
            "error": test_result.get("error"),
            "details": test_result.get("details", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integration test error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Integration test failed: {str(e)}"
        )


@router.post("/{integration_id}/execute")
@rate_limit_by_user("20/minute")
async def execute_integration_action(
    integration_id: int,
    action_data: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Execute an action using the integration
    """
    try:
        # Get integration
        result = await session.execute(
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
                status_code=404,
                detail="Integration not found"
            )
        
        if integration.status != IntegrationStatus.ACTIVE:
            raise HTTPException(
                status_code=400,
                detail=f"Integration is not active (status: {integration.status.value})"
            )
        
        # Get credentials
        cred_result = await session.execute(
            select(IntegrationCredential).where(
                IntegrationCredential.integration_id == integration_id
            )
        )
        credential = cred_result.scalar_one_or_none()
        
        if not credential:
            raise HTTPException(
                status_code=400,
                detail="Integration credentials not found"
            )
        
        # Decrypt credentials
        decrypted_credentials = json.loads(decrypt_data(credential.encrypted_credentials))
        
        # Get integration handler
        handler = get_integration_handler(integration.platform.value, decrypted_credentials)
        
        # Extract action name and parameters
        action_name = action_data.get('action')
        parameters = action_data.get('parameters', {})
        
        if not action_name:
            raise HTTPException(
                status_code=400,
                detail="Action name is required"
            )
        
        # Execute action
        if not hasattr(handler, action_name):
            raise HTTPException(
                status_code=400,
                detail=f"Action '{action_name}' not supported for platform '{integration.platform.value}'"
            )
        
        action_method = getattr(handler, action_name)
        result = await action_method(**parameters)
        
        # Update integration statistics
        integration.total_actions_executed += 1
        integration.last_action_executed_at = datetime.utcnow()
        
        if result.get("success"):
            integration.health_check_status = "healthy"
            integration.last_error = None
        else:
            integration.health_check_status = "degraded"
            integration.last_error = result.get("message", "Action execution failed")
        
        await session.commit()
        
        # Log action execution
        client_ip = get_remote_address(request)
        await AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                username=current_user.username,
                action=AuditAction.INTEGRATION_ACTION_EXECUTED,
                resource_type="integration",
                resource_id=str(integration_id),
                ip_address=client_ip,
                details={
                    "platform": integration.platform.value,
                    "action": action_name,
                    "parameters": parameters,
                    "success": result.get("success"),
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


async def test_integration_connection(integration: Integration, credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test integration connection
    """
    try:
        handler = get_integration_handler(integration.platform.value, credentials)
        result = await handler.test_connection()
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Connection test completed"),
            "platform": integration.platform.value,
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Integration connection test failed for {integration.platform.value}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Connection test failed: {str(e)}",
            "platform": integration.platform.value
        }


def determine_credential_type(platform: str, credentials: Dict[str, Any]) -> str:
    """
    Determine credential type based on platform and credentials
    """
    if platform in ['freshdesk', 'zendesk']:
        return 'api_key'
    elif platform == 'slack':
        return 'oauth_token'
    elif platform == 'trello':
        return 'api_key_token'
    elif platform == 'notion':
        return 'integration_token'
    elif platform == 'google_sheets':
        return 'service_account'
    else:
        return 'unknown'

