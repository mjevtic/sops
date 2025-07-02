"""
Webhook routes with enhanced Freshdesk and Zendesk support and signature verification
"""
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from database import get_session
from services.rule_engine import rule_engine
from middleware import verify_webhook_signature, rate_limit_by_ip, get_remote_address
from config import settings
import logging

# Import enhanced webhook handlers
from modules.freshdesk.webhook import FreshdeskWebhookHandler
from modules.zendesk.webhook import ZendeskWebhookHandler

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize webhook handlers
freshdesk_handler = FreshdeskWebhookHandler(settings.freshdesk_webhook_secret)
zendesk_handler = ZendeskWebhookHandler(settings.zendesk_webhook_secret)


async def verify_signature(
    request: Request,
    x_signature: str = Header(None, alias="X-Signature"),
    x_hub_signature: str = Header(None, alias="X-Hub-Signature"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_zendesk_webhook_signature: str = Header(None, alias="X-Zendesk-Webhook-Signature"),
    x_zendesk_webhook_signature_timestamp: str = Header(None, alias="X-Zendesk-Webhook-Signature-Timestamp")
):
    """
    Verify webhook signature for security with platform-specific handling
    """
    try:
        # Get request body
        body = await request.body()
        
        # Try different signature headers (different platforms use different formats)
        signature = x_signature or x_hub_signature or x_hub_signature_256 or x_zendesk_webhook_signature
        
        if not signature:
            logger.warning("Webhook received without signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature"
            )
        
        # Store signature info for platform-specific verification
        request.state.signature = signature
        request.state.timestamp = x_zendesk_webhook_signature_timestamp
        
        return body
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signature verification failed"
        )


@router.post("/zendesk")
@rate_limit_by_ip("100/minute")
async def zendesk_webhook(
    request: Request,
    session: Session = Depends(get_session),
    verified_body: bytes = Depends(verify_signature)
):
    """
    Handle Zendesk webhook events
    """
    try:
        # Parse JSON payload
        payload = json.loads(verified_body.decode())
        
        # Extract event information
        event_type = payload.get("type", "unknown")
        ticket_id = payload.get("ticket", {}).get("id")
        
        logger.info(f"Zendesk webhook received: {event_type} for ticket {ticket_id}")
        
        # Map Zendesk events to our internal events
        event_mapping = {
            "ticket.created": "ticket_created",
            "ticket.updated": "ticket_updated",
            "ticket.status_changed": "status_changed",
            "ticket.priority_changed": "priority_changed",
            "ticket.assignee_changed": "assignee_changed",
            "ticket.tag_added": "tag_added",
            "ticket.tag_removed": "tag_removed"
        }
        
        internal_event = event_mapping.get(event_type, event_type)
        
        # Process trigger
        execution_ids = await rule_engine.process_trigger(
            session=session,
            platform="zendesk",
            event=internal_event,
            payload=payload,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return {
            "status": "success",
            "message": f"Processed {len(execution_ids)} rules",
            "execution_ids": execution_ids,
            "event_type": internal_event
        }
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in Zendesk webhook")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except Exception as e:
        logger.error(f"Zendesk webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


@router.post("/freshdesk")
@rate_limit_by_ip("100/minute")
async def freshdesk_webhook(
    request: Request,
    session: Session = Depends(get_session),
    verified_body: bytes = Depends(verify_signature)
):
    """
    Handle Freshdesk webhook events
    """
    try:
        # Parse JSON payload
        payload = json.loads(verified_body.decode())
        
        # Extract event information
        event_type = payload.get("event_type", "unknown")
        ticket_id = payload.get("ticket", {}).get("id")
        
        logger.info(f"Freshdesk webhook received: {event_type} for ticket {ticket_id}")
        
        # Map Freshdesk events to our internal events
        event_mapping = {
            "ticket_create": "ticket_created",
            "ticket_update": "ticket_updated",
            "ticket_status_change": "status_changed",
            "ticket_priority_change": "priority_changed",
            "ticket_agent_change": "assignee_changed",
            "ticket_tag_add": "tag_added",
            "ticket_tag_remove": "tag_removed"
        }
        
        internal_event = event_mapping.get(event_type, event_type)
        
        # Process trigger
        execution_ids = await rule_engine.process_trigger(
            session=session,
            platform="freshdesk",
            event=internal_event,
            payload=payload,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return {
            "status": "success",
            "message": f"Processed {len(execution_ids)} rules",
            "execution_ids": execution_ids,
            "event_type": internal_event
        }
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in Freshdesk webhook")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except Exception as e:
        logger.error(f"Freshdesk webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


@router.post("/jira")
@rate_limit_by_ip("100/minute")
async def jira_webhook(
    request: Request,
    session: Session = Depends(get_session),
    verified_body: bytes = Depends(verify_signature)
):
    """
    Handle Jira webhook events
    """
    try:
        # Parse JSON payload
        payload = json.loads(verified_body.decode())
        
        # Extract event information
        event_type = payload.get("webhookEvent", "unknown")
        issue_key = payload.get("issue", {}).get("key")
        
        logger.info(f"Jira webhook received: {event_type} for issue {issue_key}")
        
        # Map Jira events to our internal events
        event_mapping = {
            "jira:issue_created": "issue_created",
            "jira:issue_updated": "issue_updated",
            "jira:issue_deleted": "issue_deleted",
            "jira:issue_assigned": "assignee_changed",
            "jira:issue_status_changed": "status_changed",
            "jira:issue_priority_changed": "priority_changed"
        }
        
        internal_event = event_mapping.get(event_type, event_type)
        
        # Process trigger
        execution_ids = await rule_engine.process_trigger(
            session=session,
            platform="jira",
            event=internal_event,
            payload=payload,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return {
            "status": "success",
            "message": f"Processed {len(execution_ids)} rules",
            "execution_ids": execution_ids,
            "event_type": internal_event
        }
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in Jira webhook")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except Exception as e:
        logger.error(f"Jira webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


@router.post("/github")
@rate_limit_by_ip("100/minute")
async def github_webhook(
    request: Request,
    session: Session = Depends(get_session),
    verified_body: bytes = Depends(verify_signature),
    x_github_event: str = Header(None, alias="X-GitHub-Event")
):
    """
    Handle GitHub webhook events
    """
    try:
        # Parse JSON payload
        payload = json.loads(verified_body.decode())
        
        # Extract event information
        event_type = x_github_event or "unknown"
        repo_name = payload.get("repository", {}).get("name")
        
        logger.info(f"GitHub webhook received: {event_type} for repo {repo_name}")
        
        # Map GitHub events to our internal events
        event_mapping = {
            "issues": "issue_created" if payload.get("action") == "opened" else "issue_updated",
            "issue_comment": "issue_commented",
            "pull_request": "pr_created" if payload.get("action") == "opened" else "pr_updated",
            "push": "code_pushed",
            "release": "release_created" if payload.get("action") == "published" else "release_updated"
        }
        
        internal_event = event_mapping.get(event_type, event_type)
        
        # Process trigger
        execution_ids = await rule_engine.process_trigger(
            session=session,
            platform="github",
            event=internal_event,
            payload=payload,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return {
            "status": "success",
            "message": f"Processed {len(execution_ids)} rules",
            "execution_ids": execution_ids,
            "event_type": internal_event
        }
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in GitHub webhook")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except Exception as e:
        logger.error(f"GitHub webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


@router.get("/execution/{execution_id}")
@rate_limit_by_ip("30/minute")
async def get_execution_status(execution_id: str, request: Request):
    """
    Get execution status by ID
    """
    try:
        execution = await rule_engine.get_execution_status(execution_id)
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )
        
        return {
            "execution_id": execution.execution_id,
            "rule_id": execution.rule_id,
            "status": execution.status,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "actions_executed": execution.actions_executed,
            "error_message": execution.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get execution status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get execution status"
        )


# Test endpoint for webhook development (development only)
if settings.environment == "development":
    @router.post("/test")
    @rate_limit_by_ip("10/minute")
    async def test_webhook(
        platform: str,
        event: str,
        payload: Dict[str, Any],
        request: Request,
        session: Session = Depends(get_session)
    ):
        """
        Test webhook endpoint for development
        """
        try:
            execution_ids = await rule_engine.process_trigger(
                session=session,
                platform=platform,
                event=event,
                payload=payload
            )
            
            return {
                "status": "success",
                "message": f"Test processed {len(execution_ids)} rules",
                "execution_ids": execution_ids,
                "platform": platform,
                "event": event
            }
            
        except Exception as e:
            logger.error(f"Test webhook error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Test webhook failed"
            )



@router.post("/freshdesk")
@rate_limit_by_ip("100/minute")
async def handle_freshdesk_webhook(
    request: Request,
    session: Session = Depends(get_session),
    body: bytes = Depends(verify_signature)
):
    """
    Handle Freshdesk webhook events with enhanced processing
    """
    try:
        # Parse JSON payload
        payload = json.loads(body.decode('utf-8'))
        
        # Verify Freshdesk signature
        signature = getattr(request.state, 'signature', None)
        if signature and not freshdesk_handler.verify_signature(body, signature):
            logger.warning(f"Invalid Freshdesk webhook signature from {get_remote_address(request)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Freshdesk webhook signature"
            )
        
        # Parse webhook event
        event_data = freshdesk_handler.parse_webhook_event(payload)
        
        logger.info(f"Received Freshdesk webhook: {event_data.get('event_type')}")
        
        # Process event through rule engine
        if event_data.get('parsed'):
            await rule_engine.process_webhook_event(session, event_data)
        
        return {
            "success": True,
            "message": "Freshdesk webhook processed successfully",
            "event_type": event_data.get('event_type'),
            "parsed": event_data.get('parsed', False)
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Freshdesk webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Freshdesk webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


@router.post("/zendesk")
@rate_limit_by_ip("100/minute")
async def handle_zendesk_webhook(
    request: Request,
    session: Session = Depends(get_session),
    body: bytes = Depends(verify_signature)
):
    """
    Handle Zendesk webhook events with enhanced processing
    """
    try:
        # Parse JSON payload
        payload = json.loads(body.decode('utf-8'))
        
        # Verify Zendesk signature
        signature = getattr(request.state, 'signature', None)
        timestamp = getattr(request.state, 'timestamp', None)
        
        if signature and timestamp and not zendesk_handler.verify_signature(body, signature, timestamp):
            logger.warning(f"Invalid Zendesk webhook signature from {get_remote_address(request)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Zendesk webhook signature"
            )
        
        # Parse webhook event
        event_data = zendesk_handler.parse_webhook_event(payload)
        
        logger.info(f"Received Zendesk webhook: {event_data.get('event_type')}")
        
        # Process event through rule engine
        if event_data.get('parsed'):
            await rule_engine.process_webhook_event(session, event_data)
        
        return {
            "success": True,
            "message": "Zendesk webhook processed successfully",
            "event_type": event_data.get('event_type'),
            "parsed": event_data.get('parsed', False)
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Zendesk webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Zendesk webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


@router.get("/freshdesk/setup")
async def get_freshdesk_webhook_setup():
    """
    Get Freshdesk webhook setup instructions
    """
    return freshdesk_handler.get_webhook_setup_instructions()


@router.get("/zendesk/setup")
async def get_zendesk_webhook_setup():
    """
    Get Zendesk webhook setup instructions
    """
    return zendesk_handler.get_webhook_setup_instructions()


@router.get("/events")
async def get_supported_webhook_events():
    """
    Get all supported webhook events across platforms
    """
    return {
        "success": True,
        "platforms": {
            "freshdesk": {
                "name": "Freshdesk",
                "events": freshdesk_handler.get_supported_events(),
                "webhook_url": "/webhooks/freshdesk",
                "setup_url": "/webhooks/freshdesk/setup"
            },
            "zendesk": {
                "name": "Zendesk",
                "events": zendesk_handler.get_supported_events(),
                "webhook_url": "/webhooks/zendesk",
                "setup_url": "/webhooks/zendesk/setup"
            }
        }
    }

