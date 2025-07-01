"""
Freshdesk integration actions for SupportOps Automator
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .client import FreshdeskClient, FreshdeskTicket, FreshdeskContact, FreshdeskNote, FreshdeskTimeEntry

logger = logging.getLogger(__name__)


class FreshdeskAction:
    """
    Freshdesk action handler for automation rules
    """
    
    def __init__(self, domain: str, api_key: str):
        """
        Initialize Freshdesk action handler
        
        Args:
            domain: Freshdesk domain
            api_key: Freshdesk API key
        """
        self.client = FreshdeskClient(domain, api_key)
        self.domain = domain
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Freshdesk connection"""
        try:
            success = await self.client.test_connection()
            return {
                "success": success,
                "message": "Connection successful" if success else "Connection failed",
                "platform": "freshdesk",
                "domain": self.domain
            }
        except Exception as e:
            logger.error(f"Freshdesk connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "platform": "freshdesk",
                "domain": self.domain
            }
    
    # Ticket Actions
    async def create_ticket(self, **kwargs) -> Dict[str, Any]:
        """
        Create a new ticket
        
        Args:
            subject: Ticket subject (required)
            description: Ticket description (required)
            email: Requester email
            name: Requester name
            phone: Requester phone
            priority: Priority (1=Low, 2=Medium, 3=High, 4=Urgent)
            status: Status (2=Open, 3=Pending, 4=Resolved, 5=Closed)
            type: Ticket type
            source: Source (1=Email, 2=Portal, 3=Phone, 7=Chat)
            group_id: Group ID
            agent_id: Agent ID (responder_id)
            tags: List of tags
            custom_fields: Custom field values
            cc_emails: CC email addresses
            
        Returns:
            Created ticket information
        """
        try:
            # Validate required fields
            if not kwargs.get('subject'):
                raise ValueError("Subject is required")
            if not kwargs.get('description'):
                raise ValueError("Description is required")
            
            # Create ticket object
            ticket = FreshdeskTicket(
                subject=kwargs['subject'],
                description=kwargs['description'],
                email=kwargs.get('email'),
                name=kwargs.get('name'),
                phone=kwargs.get('phone'),
                priority=kwargs.get('priority', 1),
                status=kwargs.get('status', 2),
                type=kwargs.get('type'),
                source=kwargs.get('source', 2),
                group_id=kwargs.get('group_id'),
                responder_id=kwargs.get('agent_id'),
                tags=kwargs.get('tags', []),
                custom_fields=kwargs.get('custom_fields', {}),
                cc_emails=kwargs.get('cc_emails', [])
            )
            
            result = await self.client.create_ticket(ticket)
            
            return {
                "success": True,
                "message": "Ticket created successfully",
                "ticket_id": result.get('id'),
                "ticket_url": self.client.get_ticket_url(result.get('id')),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to create Freshdesk ticket: {e}")
            return {
                "success": False,
                "message": f"Failed to create ticket: {str(e)}"
            }
    
    async def update_ticket(self, ticket_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update an existing ticket
        
        Args:
            ticket_id: Ticket ID to update
            **kwargs: Fields to update
            
        Returns:
            Update result
        """
        try:
            # Prepare update data
            updates = {}
            
            # Map common fields
            field_mapping = {
                'subject': 'subject',
                'description': 'description',
                'priority': 'priority',
                'status': 'status',
                'type': 'type',
                'group_id': 'group_id',
                'agent_id': 'responder_id',
                'tags': 'tags',
                'custom_fields': 'custom_fields'
            }
            
            for key, field in field_mapping.items():
                if key in kwargs:
                    updates[field] = kwargs[key]
            
            result = await self.client.update_ticket(ticket_id, updates)
            
            return {
                "success": True,
                "message": "Ticket updated successfully",
                "ticket_id": ticket_id,
                "ticket_url": self.client.get_ticket_url(ticket_id),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to update Freshdesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to update ticket: {str(e)}"
            }
    
    async def add_note(self, ticket_id: int, body: str, private: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Add note to ticket
        
        Args:
            ticket_id: Ticket ID
            body: Note content
            private: Whether note is private
            **kwargs: Additional note parameters
            
        Returns:
            Note creation result
        """
        try:
            note = FreshdeskNote(
                body=body,
                private=private,
                notify_emails=kwargs.get('notify_emails', [])
            )
            
            result = await self.client.add_note_to_ticket(ticket_id, note)
            
            return {
                "success": True,
                "message": "Note added successfully",
                "ticket_id": ticket_id,
                "note_id": result.get('id'),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to add note to Freshdesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to add note: {str(e)}"
            }
    
    async def add_reply(self, ticket_id: int, body: str, cc_emails: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Add reply to ticket
        
        Args:
            ticket_id: Ticket ID
            body: Reply content
            cc_emails: CC email addresses
            
        Returns:
            Reply creation result
        """
        try:
            result = await self.client.add_reply_to_ticket(ticket_id, body, cc_emails)
            
            return {
                "success": True,
                "message": "Reply added successfully",
                "ticket_id": ticket_id,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to add reply to Freshdesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to add reply: {str(e)}"
            }
    
    async def assign_ticket(self, ticket_id: int, agent_id: int, group_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Assign ticket to agent/group
        
        Args:
            ticket_id: Ticket ID
            agent_id: Agent ID
            group_id: Group ID (optional)
            
        Returns:
            Assignment result
        """
        try:
            updates = {"responder_id": agent_id}
            if group_id:
                updates["group_id"] = group_id
            
            result = await self.client.update_ticket(ticket_id, updates)
            
            return {
                "success": True,
                "message": "Ticket assigned successfully",
                "ticket_id": ticket_id,
                "agent_id": agent_id,
                "group_id": group_id,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to assign Freshdesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to assign ticket: {str(e)}"
            }
    
    async def change_status(self, ticket_id: int, status: int) -> Dict[str, Any]:
        """
        Change ticket status
        
        Args:
            ticket_id: Ticket ID
            status: New status (2=Open, 3=Pending, 4=Resolved, 5=Closed)
            
        Returns:
            Status change result
        """
        try:
            result = await self.client.update_ticket(ticket_id, {"status": status})
            
            status_names = {
                2: "Open",
                3: "Pending",
                4: "Resolved",
                5: "Closed"
            }
            
            return {
                "success": True,
                "message": f"Ticket status changed to {status_names.get(status, status)}",
                "ticket_id": ticket_id,
                "status": status,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to change Freshdesk ticket {ticket_id} status: {e}")
            return {
                "success": False,
                "message": f"Failed to change status: {str(e)}"
            }
    
    async def add_time_entry(self, ticket_id: int, time_spent: str, note: Optional[str] = None, billable: bool = True) -> Dict[str, Any]:
        """
        Add time entry to ticket
        
        Args:
            ticket_id: Ticket ID
            time_spent: Time spent (format: "HH:MM")
            note: Time entry note
            billable: Whether time is billable
            
        Returns:
            Time entry result
        """
        try:
            time_entry = FreshdeskTimeEntry(
                time_spent=time_spent,
                note=note,
                billable=billable,
                executed_at=datetime.utcnow()
            )
            
            result = await self.client.add_time_entry(ticket_id, time_entry)
            
            return {
                "success": True,
                "message": "Time entry added successfully",
                "ticket_id": ticket_id,
                "time_spent": time_spent,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to add time entry to Freshdesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to add time entry: {str(e)}"
            }
    
    # Contact Actions
    async def create_contact(self, name: str, email: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new contact
        
        Args:
            name: Contact name
            email: Contact email
            **kwargs: Additional contact fields
            
        Returns:
            Contact creation result
        """
        try:
            contact = FreshdeskContact(
                name=name,
                email=email,
                phone=kwargs.get('phone'),
                mobile=kwargs.get('mobile'),
                company_id=kwargs.get('company_id'),
                tags=kwargs.get('tags', []),
                custom_fields=kwargs.get('custom_fields', {})
            )
            
            result = await self.client.create_contact(contact)
            
            return {
                "success": True,
                "message": "Contact created successfully",
                "contact_id": result.get('id'),
                "contact_url": self.client.get_contact_url(result.get('id')),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to create Freshdesk contact: {e}")
            return {
                "success": False,
                "message": f"Failed to create contact: {str(e)}"
            }
    
    async def update_contact(self, contact_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update contact
        
        Args:
            contact_id: Contact ID
            **kwargs: Fields to update
            
        Returns:
            Update result
        """
        try:
            result = await self.client.update_contact(contact_id, kwargs)
            
            return {
                "success": True,
                "message": "Contact updated successfully",
                "contact_id": contact_id,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to update Freshdesk contact {contact_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to update contact: {str(e)}"
            }
    
    async def search_contacts(self, query: str) -> Dict[str, Any]:
        """
        Search contacts
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        try:
            result = await self.client.search_contacts(query)
            
            return {
                "success": True,
                "message": f"Found {len(result.get('results', []))} contacts",
                "contacts": result.get('results', []),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to search Freshdesk contacts: {e}")
            return {
                "success": False,
                "message": f"Failed to search contacts: {str(e)}"
            }
    
    # Utility Actions
    async def get_ticket_info(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get ticket information
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket information
        """
        try:
            result = await self.client.get_ticket(ticket_id, include=['requester', 'stats'])
            
            return {
                "success": True,
                "message": "Ticket retrieved successfully",
                "ticket_id": ticket_id,
                "ticket_url": self.client.get_ticket_url(ticket_id),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to get Freshdesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to get ticket: {str(e)}"
            }
    
    async def list_agents(self) -> Dict[str, Any]:
        """
        List all agents
        
        Returns:
            Agents list
        """
        try:
            result = await self.client.list_agents()
            
            return {
                "success": True,
                "message": f"Retrieved {len(result)} agents",
                "agents": result,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to list Freshdesk agents: {e}")
            return {
                "success": False,
                "message": f"Failed to list agents: {str(e)}"
            }
    
    async def list_groups(self) -> Dict[str, Any]:
        """
        List all groups
        
        Returns:
            Groups list
        """
        try:
            result = await self.client.list_groups()
            
            return {
                "success": True,
                "message": f"Retrieved {len(result)} groups",
                "groups": result,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to list Freshdesk groups: {e}")
            return {
                "success": False,
                "message": f"Failed to list groups: {str(e)}"
            }
    
    # Bulk Actions
    async def bulk_update_tickets(self, ticket_ids: List[int], updates: Dict) -> Dict[str, Any]:
        """
        Bulk update multiple tickets
        
        Args:
            ticket_ids: List of ticket IDs
            updates: Updates to apply
            
        Returns:
            Bulk update result
        """
        try:
            result = await self.client.bulk_update_tickets(ticket_ids, updates)
            
            return {
                "success": True,
                "message": f"Bulk updated {len(ticket_ids)} tickets",
                "ticket_ids": ticket_ids,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to bulk update Freshdesk tickets: {e}")
            return {
                "success": False,
                "message": f"Failed to bulk update tickets: {str(e)}"
            }
    
    # Available Actions for Rule Engine
    @classmethod
    def get_available_actions(cls) -> List[Dict[str, Any]]:
        """Get list of available actions for rule engine"""
        return [
            {
                "name": "create_ticket",
                "display_name": "Create Ticket",
                "description": "Create a new support ticket",
                "parameters": [
                    {"name": "subject", "type": "string", "required": True, "description": "Ticket subject"},
                    {"name": "description", "type": "string", "required": True, "description": "Ticket description"},
                    {"name": "email", "type": "string", "required": False, "description": "Requester email"},
                    {"name": "name", "type": "string", "required": False, "description": "Requester name"},
                    {"name": "priority", "type": "integer", "required": False, "description": "Priority (1-4)", "default": 1},
                    {"name": "status", "type": "integer", "required": False, "description": "Status (2-5)", "default": 2},
                    {"name": "group_id", "type": "integer", "required": False, "description": "Group ID"},
                    {"name": "agent_id", "type": "integer", "required": False, "description": "Agent ID"},
                    {"name": "tags", "type": "array", "required": False, "description": "Tags"},
                ]
            },
            {
                "name": "update_ticket",
                "display_name": "Update Ticket",
                "description": "Update an existing ticket",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "subject", "type": "string", "required": False, "description": "New subject"},
                    {"name": "priority", "type": "integer", "required": False, "description": "New priority"},
                    {"name": "status", "type": "integer", "required": False, "description": "New status"},
                    {"name": "group_id", "type": "integer", "required": False, "description": "New group ID"},
                    {"name": "agent_id", "type": "integer", "required": False, "description": "New agent ID"},
                ]
            },
            {
                "name": "add_note",
                "display_name": "Add Note",
                "description": "Add a note to a ticket",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "body", "type": "string", "required": True, "description": "Note content"},
                    {"name": "private", "type": "boolean", "required": False, "description": "Private note", "default": False},
                ]
            },
            {
                "name": "add_reply",
                "display_name": "Add Reply",
                "description": "Add a reply to a ticket",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "body", "type": "string", "required": True, "description": "Reply content"},
                    {"name": "cc_emails", "type": "array", "required": False, "description": "CC emails"},
                ]
            },
            {
                "name": "assign_ticket",
                "display_name": "Assign Ticket",
                "description": "Assign ticket to agent/group",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "agent_id", "type": "integer", "required": True, "description": "Agent ID"},
                    {"name": "group_id", "type": "integer", "required": False, "description": "Group ID"},
                ]
            },
            {
                "name": "change_status",
                "display_name": "Change Status",
                "description": "Change ticket status",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "status", "type": "integer", "required": True, "description": "New status (2=Open, 3=Pending, 4=Resolved, 5=Closed)"},
                ]
            },
            {
                "name": "add_time_entry",
                "display_name": "Add Time Entry",
                "description": "Add time tracking entry",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "time_spent", "type": "string", "required": True, "description": "Time spent (HH:MM format)"},
                    {"name": "note", "type": "string", "required": False, "description": "Time entry note"},
                    {"name": "billable", "type": "boolean", "required": False, "description": "Billable time", "default": True},
                ]
            },
            {
                "name": "create_contact",
                "display_name": "Create Contact",
                "description": "Create a new contact",
                "parameters": [
                    {"name": "name", "type": "string", "required": True, "description": "Contact name"},
                    {"name": "email", "type": "string", "required": True, "description": "Contact email"},
                    {"name": "phone", "type": "string", "required": False, "description": "Phone number"},
                    {"name": "company_id", "type": "integer", "required": False, "description": "Company ID"},
                ]
            }
        ]

