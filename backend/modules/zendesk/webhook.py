"""
Zendesk webhook handler for SupportOps Automator
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class ZendeskWebhookHandler:
    """
    Handle Zendesk webhook events with signature verification
    """
    
    def __init__(self, webhook_secret: Optional[str] = None):
        """
        Initialize webhook handler
        
        Args:
            webhook_secret: Webhook secret for signature verification
        """
        self.webhook_secret = webhook_secret
    
    def verify_signature(self, payload: bytes, signature: str, timestamp: str) -> bool:
        """
        Verify webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature from headers
            timestamp: Webhook timestamp
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True
        
        try:
            # Zendesk uses HMAC-SHA256 with timestamp
            message = timestamp + payload.decode('utf-8')
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def parse_webhook_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Zendesk webhook event
        
        Args:
            payload: Webhook payload
            
        Returns:
            Parsed event data
        """
        try:
            # Extract event type and data
            event_type = payload.get('type', 'unknown')
            
            # Common event data
            event_data = {
                'platform': 'zendesk',
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'raw_payload': payload
            }
            
            # Parse based on event type
            if event_type == 'ticket.created':
                event_data.update(self._parse_ticket_created(payload))
            elif event_type == 'ticket.updated':
                event_data.update(self._parse_ticket_updated(payload))
            elif event_type == 'ticket.solved':
                event_data.update(self._parse_ticket_solved(payload))
            elif event_type == 'ticket.closed':
                event_data.update(self._parse_ticket_closed(payload))
            elif event_type == 'comment.created':
                event_data.update(self._parse_comment_created(payload))
            elif event_type == 'user.created':
                event_data.update(self._parse_user_created(payload))
            elif event_type == 'user.updated':
                event_data.update(self._parse_user_updated(payload))
            elif event_type == 'organization.created':
                event_data.update(self._parse_organization_created(payload))
            elif event_type == 'organization.updated':
                event_data.update(self._parse_organization_updated(payload))
            else:
                logger.warning(f"Unknown Zendesk event type: {event_type}")
                event_data['parsed'] = False
            
            return event_data
            
        except Exception as e:
            logger.error(f"Failed to parse Zendesk webhook: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid webhook payload: {e}")
    
    def _parse_ticket_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ticket created event"""
        ticket = payload.get('ticket', {})
        requester = payload.get('requester', {})
        
        return {
            'parsed': True,
            'ticket': {
                'id': ticket.get('id'),
                'subject': ticket.get('subject'),
                'description': ticket.get('description'),
                'status': ticket.get('status'),
                'priority': ticket.get('priority'),
                'type': ticket.get('type'),
                'requester_id': ticket.get('requester_id'),
                'submitter_id': ticket.get('submitter_id'),
                'assignee_id': ticket.get('assignee_id'),
                'group_id': ticket.get('group_id'),
                'organization_id': ticket.get('organization_id'),
                'tags': ticket.get('tags', []),
                'created_at': ticket.get('created_at'),
                'updated_at': ticket.get('updated_at'),
                'due_at': ticket.get('due_at'),
                'custom_fields': ticket.get('custom_fields', [])
            },
            'requester': {
                'id': requester.get('id'),
                'name': requester.get('name'),
                'email': requester.get('email'),
                'phone': requester.get('phone'),
                'organization_id': requester.get('organization_id')
            },
            'trigger_conditions': {
                'ticket_id': ticket.get('id'),
                'priority': ticket.get('priority'),
                'status': ticket.get('status'),
                'type': ticket.get('type'),
                'group_id': ticket.get('group_id'),
                'requester_id': ticket.get('requester_id'),
                'requester_email': requester.get('email'),
                'organization_id': ticket.get('organization_id'),
                'tags': ticket.get('tags', [])
            }
        }
    
    def _parse_ticket_updated(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ticket updated event"""
        ticket = payload.get('ticket', {})
        changes = payload.get('changes', {})
        
        return {
            'parsed': True,
            'ticket': {
                'id': ticket.get('id'),
                'subject': ticket.get('subject'),
                'status': ticket.get('status'),
                'priority': ticket.get('priority'),
                'type': ticket.get('type'),
                'assignee_id': ticket.get('assignee_id'),
                'group_id': ticket.get('group_id'),
                'organization_id': ticket.get('organization_id'),
                'tags': ticket.get('tags', []),
                'updated_at': ticket.get('updated_at')
            },
            'changes': changes,
            'trigger_conditions': {
                'ticket_id': ticket.get('id'),
                'priority': ticket.get('priority'),
                'status': ticket.get('status'),
                'type': ticket.get('type'),
                'group_id': ticket.get('group_id'),
                'assignee_id': ticket.get('assignee_id'),
                'organization_id': ticket.get('organization_id'),
                'changes': list(changes.keys()) if changes else []
            }
        }
    
    def _parse_ticket_solved(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ticket solved event"""
        ticket = payload.get('ticket', {})
        solver = payload.get('solver', {})
        
        return {
            'parsed': True,
            'ticket': {
                'id': ticket.get('id'),
                'subject': ticket.get('subject'),
                'status': ticket.get('status'),
                'priority': ticket.get('priority'),
                'type': ticket.get('type'),
                'assignee_id': ticket.get('assignee_id'),
                'group_id': ticket.get('group_id'),
                'organization_id': ticket.get('organization_id'),
                'solved_at': ticket.get('updated_at')
            },
            'solver': {
                'id': solver.get('id'),
                'name': solver.get('name'),
                'email': solver.get('email')
            },
            'trigger_conditions': {
                'ticket_id': ticket.get('id'),
                'priority': ticket.get('priority'),
                'type': ticket.get('type'),
                'group_id': ticket.get('group_id'),
                'assignee_id': ticket.get('assignee_id'),
                'solver_id': solver.get('id'),
                'organization_id': ticket.get('organization_id')
            }
        }
    
    def _parse_ticket_closed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ticket closed event"""
        ticket = payload.get('ticket', {})
        
        return {
            'parsed': True,
            'ticket': {
                'id': ticket.get('id'),
                'subject': ticket.get('subject'),
                'status': ticket.get('status'),
                'priority': ticket.get('priority'),
                'type': ticket.get('type'),
                'assignee_id': ticket.get('assignee_id'),
                'group_id': ticket.get('group_id'),
                'organization_id': ticket.get('organization_id'),
                'closed_at': ticket.get('updated_at')
            },
            'trigger_conditions': {
                'ticket_id': ticket.get('id'),
                'priority': ticket.get('priority'),
                'type': ticket.get('type'),
                'group_id': ticket.get('group_id'),
                'assignee_id': ticket.get('assignee_id'),
                'organization_id': ticket.get('organization_id')
            }
        }
    
    def _parse_comment_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse comment created event"""
        comment = payload.get('comment', {})
        ticket = payload.get('ticket', {})
        author = payload.get('author', {})
        
        return {
            'parsed': True,
            'comment': {
                'id': comment.get('id'),
                'body': comment.get('body'),
                'html_body': comment.get('html_body'),
                'plain_body': comment.get('plain_body'),
                'public': comment.get('public'),
                'author_id': comment.get('author_id'),
                'audit_id': comment.get('audit_id'),
                'created_at': comment.get('created_at')
            },
            'ticket': {
                'id': ticket.get('id'),
                'subject': ticket.get('subject'),
                'status': ticket.get('status'),
                'priority': ticket.get('priority'),
                'assignee_id': ticket.get('assignee_id'),
                'group_id': ticket.get('group_id')
            },
            'author': {
                'id': author.get('id'),
                'name': author.get('name'),
                'email': author.get('email'),
                'role': author.get('role')
            },
            'trigger_conditions': {
                'ticket_id': ticket.get('id'),
                'comment_id': comment.get('id'),
                'comment_public': comment.get('public'),
                'author_id': comment.get('author_id'),
                'author_role': author.get('role'),
                'group_id': ticket.get('group_id')
            }
        }
    
    def _parse_user_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user created event"""
        user = payload.get('user', {})
        
        return {
            'parsed': True,
            'user': {
                'id': user.get('id'),
                'name': user.get('name'),
                'email': user.get('email'),
                'phone': user.get('phone'),
                'role': user.get('role'),
                'organization_id': user.get('organization_id'),
                'tags': user.get('tags', []),
                'created_at': user.get('created_at'),
                'verified': user.get('verified'),
                'active': user.get('active')
            },
            'trigger_conditions': {
                'user_id': user.get('id'),
                'user_email': user.get('email'),
                'user_role': user.get('role'),
                'organization_id': user.get('organization_id'),
                'tags': user.get('tags', [])
            }
        }
    
    def _parse_user_updated(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user updated event"""
        user = payload.get('user', {})
        changes = payload.get('changes', {})
        
        return {
            'parsed': True,
            'user': {
                'id': user.get('id'),
                'name': user.get('name'),
                'email': user.get('email'),
                'role': user.get('role'),
                'organization_id': user.get('organization_id'),
                'updated_at': user.get('updated_at'),
                'verified': user.get('verified'),
                'active': user.get('active')
            },
            'changes': changes,
            'trigger_conditions': {
                'user_id': user.get('id'),
                'user_email': user.get('email'),
                'user_role': user.get('role'),
                'organization_id': user.get('organization_id'),
                'changes': list(changes.keys()) if changes else []
            }
        }
    
    def _parse_organization_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse organization created event"""
        organization = payload.get('organization', {})
        
        return {
            'parsed': True,
            'organization': {
                'id': organization.get('id'),
                'name': organization.get('name'),
                'details': organization.get('details'),
                'notes': organization.get('notes'),
                'domain_names': organization.get('domain_names', []),
                'tags': organization.get('tags', []),
                'created_at': organization.get('created_at')
            },
            'trigger_conditions': {
                'organization_id': organization.get('id'),
                'organization_name': organization.get('name'),
                'domain_names': organization.get('domain_names', []),
                'tags': organization.get('tags', [])
            }
        }
    
    def _parse_organization_updated(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse organization updated event"""
        organization = payload.get('organization', {})
        changes = payload.get('changes', {})
        
        return {
            'parsed': True,
            'organization': {
                'id': organization.get('id'),
                'name': organization.get('name'),
                'details': organization.get('details'),
                'domain_names': organization.get('domain_names', []),
                'updated_at': organization.get('updated_at')
            },
            'changes': changes,
            'trigger_conditions': {
                'organization_id': organization.get('id'),
                'organization_name': organization.get('name'),
                'domain_names': organization.get('domain_names', []),
                'changes': list(changes.keys()) if changes else []
            }
        }
    
    @staticmethod
    def get_supported_events() -> Dict[str, str]:
        """Get supported webhook events"""
        return {
            'ticket.created': 'Ticket Created',
            'ticket.updated': 'Ticket Updated',
            'ticket.solved': 'Ticket Solved',
            'ticket.closed': 'Ticket Closed',
            'comment.created': 'Comment Created',
            'user.created': 'User Created',
            'user.updated': 'User Updated',
            'organization.created': 'Organization Created',
            'organization.updated': 'Organization Updated'
        }
    
    @staticmethod
    def get_webhook_setup_instructions() -> Dict[str, Any]:
        """Get webhook setup instructions"""
        return {
            'platform': 'Zendesk',
            'instructions': [
                '1. Go to Admin Center → Apps and integrations → Webhooks in your Zendesk account',
                '2. Click "Create webhook"',
                '3. Enter the webhook URL: {webhook_url}/webhooks/zendesk',
                '4. Set the request method to POST',
                '5. Add authentication if required',
                '6. Select the events you want to monitor',
                '7. Set up signing secret for security',
                '8. Test the webhook to ensure it\'s working',
                '9. Save the webhook configuration'
            ],
            'required_permissions': [
                'Admin access to Zendesk account',
                'Webhook configuration permissions'
            ],
            'supported_events': ZendeskWebhookHandler.get_supported_events(),
            'security_notes': [
                'Always use HTTPS for webhook URLs',
                'Set a strong signing secret',
                'Verify webhook signatures in production',
                'Monitor webhook delivery logs',
                'Use timestamp validation to prevent replay attacks'
            ],
            'authentication_options': [
                'Basic authentication',
                'Bearer token',
                'API key authentication',
                'Custom headers'
            ]
        }

