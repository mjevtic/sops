"""
Freshdesk webhook handler for SupportOps Automator
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class FreshdeskWebhookHandler:
    """
    Handle Freshdesk webhook events with signature verification
    """
    
    def __init__(self, webhook_secret: Optional[str] = None):
        """
        Initialize webhook handler
        
        Args:
            webhook_secret: Webhook secret for signature verification
        """
        self.webhook_secret = webhook_secret
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature from headers
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True
        
        try:
            # Freshdesk uses HMAC-SHA256
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def parse_webhook_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Freshdesk webhook event
        
        Args:
            payload: Webhook payload
            
        Returns:
            Parsed event data
        """
        try:
            # Extract event type and data
            event_type = payload.get('event_type', 'unknown')
            
            # Common event data
            event_data = {
                'platform': 'freshdesk',
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'raw_payload': payload
            }
            
            # Parse based on event type
            if event_type == 'ticket_created':
                event_data.update(self._parse_ticket_created(payload))
            elif event_type == 'ticket_updated':
                event_data.update(self._parse_ticket_updated(payload))
            elif event_type == 'ticket_resolved':
                event_data.update(self._parse_ticket_resolved(payload))
            elif event_type == 'ticket_closed':
                event_data.update(self._parse_ticket_closed(payload))
            elif event_type == 'note_created':
                event_data.update(self._parse_note_created(payload))
            elif event_type == 'contact_created':
                event_data.update(self._parse_contact_created(payload))
            elif event_type == 'contact_updated':
                event_data.update(self._parse_contact_updated(payload))
            else:
                logger.warning(f"Unknown Freshdesk event type: {event_type}")
                event_data['parsed'] = False
            
            return event_data
            
        except Exception as e:
            logger.error(f"Failed to parse Freshdesk webhook: {e}")
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
                'description': ticket.get('description_text'),
                'status': ticket.get('status'),
                'priority': ticket.get('priority'),
                'type': ticket.get('type'),
                'source': ticket.get('source'),
                'group_id': ticket.get('group_id'),
                'responder_id': ticket.get('responder_id'),
                'tags': ticket.get('tags', []),
                'created_at': ticket.get('created_at'),
                'updated_at': ticket.get('updated_at'),
                'due_by': ticket.get('due_by'),
                'fr_due_by': ticket.get('fr_due_by'),
                'custom_fields': ticket.get('custom_fields', {})
            },
            'requester': {
                'id': requester.get('id'),
                'name': requester.get('name'),
                'email': requester.get('email'),
                'phone': requester.get('phone'),
                'company_id': requester.get('company_id')
            },
            'trigger_conditions': {
                'ticket_id': ticket.get('id'),
                'priority': ticket.get('priority'),
                'status': ticket.get('status'),
                'type': ticket.get('type'),
                'source': ticket.get('source'),
                'group_id': ticket.get('group_id'),
                'requester_email': requester.get('email'),
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
                'group_id': ticket.get('group_id'),
                'responder_id': ticket.get('responder_id'),
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
                'changes': list(changes.keys()) if changes else []
            }
        }
    
    def _parse_ticket_resolved(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ticket resolved event"""
        ticket = payload.get('ticket', {})
        resolver = payload.get('resolver', {})
        
        return {
            'parsed': True,
            'ticket': {
                'id': ticket.get('id'),
                'subject': ticket.get('subject'),
                'status': ticket.get('status'),
                'priority': ticket.get('priority'),
                'type': ticket.get('type'),
                'group_id': ticket.get('group_id'),
                'responder_id': ticket.get('responder_id'),
                'resolved_at': ticket.get('updated_at')
            },
            'resolver': {
                'id': resolver.get('id'),
                'name': resolver.get('name'),
                'email': resolver.get('email')
            },
            'trigger_conditions': {
                'ticket_id': ticket.get('id'),
                'priority': ticket.get('priority'),
                'type': ticket.get('type'),
                'group_id': ticket.get('group_id'),
                'resolver_id': resolver.get('id')
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
                'group_id': ticket.get('group_id'),
                'responder_id': ticket.get('responder_id'),
                'closed_at': ticket.get('updated_at')
            },
            'trigger_conditions': {
                'ticket_id': ticket.get('id'),
                'priority': ticket.get('priority'),
                'type': ticket.get('type'),
                'group_id': ticket.get('group_id')
            }
        }
    
    def _parse_note_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse note created event"""
        note = payload.get('note', {})
        ticket = payload.get('ticket', {})
        
        return {
            'parsed': True,
            'note': {
                'id': note.get('id'),
                'body': note.get('body_text'),
                'private': note.get('private'),
                'incoming': note.get('incoming'),
                'user_id': note.get('user_id'),
                'created_at': note.get('created_at')
            },
            'ticket': {
                'id': ticket.get('id'),
                'subject': ticket.get('subject'),
                'status': ticket.get('status'),
                'priority': ticket.get('priority')
            },
            'trigger_conditions': {
                'ticket_id': ticket.get('id'),
                'note_id': note.get('id'),
                'note_private': note.get('private'),
                'note_incoming': note.get('incoming'),
                'user_id': note.get('user_id')
            }
        }
    
    def _parse_contact_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse contact created event"""
        contact = payload.get('contact', {})
        
        return {
            'parsed': True,
            'contact': {
                'id': contact.get('id'),
                'name': contact.get('name'),
                'email': contact.get('email'),
                'phone': contact.get('phone'),
                'mobile': contact.get('mobile'),
                'company_id': contact.get('company_id'),
                'tags': contact.get('tags', []),
                'created_at': contact.get('created_at')
            },
            'trigger_conditions': {
                'contact_id': contact.get('id'),
                'contact_email': contact.get('email'),
                'company_id': contact.get('company_id'),
                'tags': contact.get('tags', [])
            }
        }
    
    def _parse_contact_updated(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse contact updated event"""
        contact = payload.get('contact', {})
        changes = payload.get('changes', {})
        
        return {
            'parsed': True,
            'contact': {
                'id': contact.get('id'),
                'name': contact.get('name'),
                'email': contact.get('email'),
                'phone': contact.get('phone'),
                'company_id': contact.get('company_id'),
                'updated_at': contact.get('updated_at')
            },
            'changes': changes,
            'trigger_conditions': {
                'contact_id': contact.get('id'),
                'contact_email': contact.get('email'),
                'company_id': contact.get('company_id'),
                'changes': list(changes.keys()) if changes else []
            }
        }
    
    @staticmethod
    def get_supported_events() -> Dict[str, str]:
        """Get supported webhook events"""
        return {
            'ticket_created': 'Ticket Created',
            'ticket_updated': 'Ticket Updated',
            'ticket_resolved': 'Ticket Resolved',
            'ticket_closed': 'Ticket Closed',
            'note_created': 'Note Created',
            'contact_created': 'Contact Created',
            'contact_updated': 'Contact Updated'
        }
    
    @staticmethod
    def get_webhook_setup_instructions() -> Dict[str, Any]:
        """Get webhook setup instructions"""
        return {
            'platform': 'Freshdesk',
            'instructions': [
                '1. Go to Admin → Automations → Webhooks in your Freshdesk account',
                '2. Click "New Webhook"',
                '3. Enter the webhook URL: {webhook_url}/webhooks/freshdesk',
                '4. Select the events you want to monitor',
                '5. Set the webhook secret for security',
                '6. Test the webhook to ensure it\'s working',
                '7. Save the webhook configuration'
            ],
            'required_permissions': [
                'Admin access to Freshdesk account',
                'Webhook configuration permissions'
            ],
            'supported_events': FreshdeskWebhookHandler.get_supported_events(),
            'security_notes': [
                'Always use HTTPS for webhook URLs',
                'Set a strong webhook secret',
                'Verify webhook signatures in production',
                'Monitor webhook delivery logs'
            ]
        }

