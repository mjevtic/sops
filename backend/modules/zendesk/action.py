"""
Zendesk integration actions for SupportOps Automator
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .client import ZendeskClient, ZendeskTicket, ZendeskUser, ZendeskComment, ZendeskOrganization

logger = logging.getLogger(__name__)


class ZendeskAction:
    """
    Zendesk action handler for automation rules
    """
    
    def __init__(self, subdomain: str, email: str, api_token: str):
        """
        Initialize Zendesk action handler
        
        Args:
            subdomain: Zendesk subdomain
            email: Agent email
            api_token: Zendesk API token
        """
        self.client = ZendeskClient(subdomain, email, api_token)
        self.subdomain = subdomain
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Zendesk connection"""
        try:
            success = await self.client.test_connection()
            return {
                "success": success,
                "message": "Connection successful" if success else "Connection failed",
                "platform": "zendesk",
                "subdomain": self.subdomain
            }
        except Exception as e:
            logger.error(f"Zendesk connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "platform": "zendesk",
                "subdomain": self.subdomain
            }
    
    # Ticket Actions
    async def create_ticket(self, **kwargs) -> Dict[str, Any]:
        """
        Create a new ticket
        
        Args:
            subject: Ticket subject (required)
            description: Ticket description (required)
            requester_email: Requester email
            requester_name: Requester name
            priority: Priority (low, normal, high, urgent)
            status: Status (new, open, pending, hold, solved, closed)
            type: Type (problem, incident, question, task)
            assignee_id: Assignee ID
            group_id: Group ID
            tags: List of tags
            custom_fields: Custom field values
            external_id: External ID
            
        Returns:
            Created ticket information
        """
        try:
            # Validate required fields
            if not kwargs.get('subject'):
                raise ValueError("Subject is required")
            if not kwargs.get('description'):
                raise ValueError("Description is required")
            
            # Handle requester
            requester_id = kwargs.get('requester_id')
            if not requester_id and kwargs.get('requester_email'):
                # Try to find or create user
                user_result = await self._find_or_create_user(
                    kwargs.get('requester_email'),
                    kwargs.get('requester_name', kwargs.get('requester_email'))
                )
                if user_result.get('success'):
                    requester_id = user_result['user_id']
            
            # Create ticket object
            ticket = ZendeskTicket(
                subject=kwargs['subject'],
                description=kwargs['description'],
                requester_id=requester_id,
                priority=kwargs.get('priority'),
                status=kwargs.get('status', 'new'),
                type=kwargs.get('type'),
                assignee_id=kwargs.get('assignee_id'),
                group_id=kwargs.get('group_id'),
                organization_id=kwargs.get('organization_id'),
                tags=kwargs.get('tags', []),
                custom_fields=self._format_custom_fields(kwargs.get('custom_fields', {})),
                external_id=kwargs.get('external_id')
            )
            
            result = await self.client.create_ticket(ticket)
            ticket_data = result.get('ticket', {})
            
            return {
                "success": True,
                "message": "Ticket created successfully",
                "ticket_id": ticket_data.get('id'),
                "ticket_url": self.client.get_ticket_url(ticket_data.get('id')),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to create Zendesk ticket: {e}")
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
                'priority': 'priority',
                'status': 'status',
                'type': 'type',
                'assignee_id': 'assignee_id',
                'group_id': 'group_id',
                'tags': 'tags',
                'external_id': 'external_id'
            }
            
            for key, field in field_mapping.items():
                if key in kwargs:
                    updates[field] = kwargs[key]
            
            # Handle custom fields
            if 'custom_fields' in kwargs:
                updates['custom_fields'] = self._format_custom_fields(kwargs['custom_fields'])
            
            result = await self.client.update_ticket(ticket_id, updates)
            
            return {
                "success": True,
                "message": "Ticket updated successfully",
                "ticket_id": ticket_id,
                "ticket_url": self.client.get_ticket_url(ticket_id),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to update Zendesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to update ticket: {str(e)}"
            }
    
    async def add_comment(self, ticket_id: int, body: str, public: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Add comment to ticket
        
        Args:
            ticket_id: Ticket ID
            body: Comment content
            public: Whether comment is public
            **kwargs: Additional comment parameters
            
        Returns:
            Comment creation result
        """
        try:
            comment = ZendeskComment(
                body=body,
                public=public,
                author_id=kwargs.get('author_id')
            )
            
            result = await self.client.add_comment_to_ticket(ticket_id, comment)
            
            return {
                "success": True,
                "message": "Comment added successfully",
                "ticket_id": ticket_id,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to add comment to Zendesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to add comment: {str(e)}"
            }
    
    async def assign_ticket(self, ticket_id: int, assignee_id: int, group_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Assign ticket to agent/group
        
        Args:
            ticket_id: Ticket ID
            assignee_id: Assignee ID
            group_id: Group ID (optional)
            
        Returns:
            Assignment result
        """
        try:
            updates = {"assignee_id": assignee_id}
            if group_id:
                updates["group_id"] = group_id
            
            result = await self.client.update_ticket(ticket_id, updates)
            
            return {
                "success": True,
                "message": "Ticket assigned successfully",
                "ticket_id": ticket_id,
                "assignee_id": assignee_id,
                "group_id": group_id,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to assign Zendesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to assign ticket: {str(e)}"
            }
    
    async def change_status(self, ticket_id: int, status: str) -> Dict[str, Any]:
        """
        Change ticket status
        
        Args:
            ticket_id: Ticket ID
            status: New status (new, open, pending, hold, solved, closed)
            
        Returns:
            Status change result
        """
        try:
            result = await self.client.update_ticket(ticket_id, {"status": status})
            
            return {
                "success": True,
                "message": f"Ticket status changed to {status}",
                "ticket_id": ticket_id,
                "status": status,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to change Zendesk ticket {ticket_id} status: {e}")
            return {
                "success": False,
                "message": f"Failed to change status: {str(e)}"
            }
    
    async def set_priority(self, ticket_id: int, priority: str) -> Dict[str, Any]:
        """
        Set ticket priority
        
        Args:
            ticket_id: Ticket ID
            priority: New priority (low, normal, high, urgent)
            
        Returns:
            Priority change result
        """
        try:
            result = await self.client.update_ticket(ticket_id, {"priority": priority})
            
            return {
                "success": True,
                "message": f"Ticket priority set to {priority}",
                "ticket_id": ticket_id,
                "priority": priority,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to set Zendesk ticket {ticket_id} priority: {e}")
            return {
                "success": False,
                "message": f"Failed to set priority: {str(e)}"
            }
    
    async def add_tags(self, ticket_id: int, tags: List[str]) -> Dict[str, Any]:
        """
        Add tags to ticket
        
        Args:
            ticket_id: Ticket ID
            tags: Tags to add
            
        Returns:
            Tag addition result
        """
        try:
            # Get current ticket to preserve existing tags
            ticket_result = await self.client.get_ticket(ticket_id)
            current_tags = ticket_result.get('ticket', {}).get('tags', [])
            
            # Merge tags
            all_tags = list(set(current_tags + tags))
            
            result = await self.client.update_ticket(ticket_id, {"tags": all_tags})
            
            return {
                "success": True,
                "message": f"Tags added successfully: {', '.join(tags)}",
                "ticket_id": ticket_id,
                "tags_added": tags,
                "all_tags": all_tags,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to add tags to Zendesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to add tags: {str(e)}"
            }
    
    async def apply_macro(self, ticket_id: int, macro_id: int) -> Dict[str, Any]:
        """
        Apply macro to ticket
        
        Args:
            ticket_id: Ticket ID
            macro_id: Macro ID
            
        Returns:
            Macro application result
        """
        try:
            result = await self.client.apply_macro(ticket_id, macro_id)
            
            return {
                "success": True,
                "message": "Macro applied successfully",
                "ticket_id": ticket_id,
                "macro_id": macro_id,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to apply macro to Zendesk ticket {ticket_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to apply macro: {str(e)}"
            }
    
    # User Actions
    async def create_user(self, name: str, email: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            name: User name
            email: User email
            **kwargs: Additional user fields
            
        Returns:
            User creation result
        """
        try:
            user = ZendeskUser(
                name=name,
                email=email,
                phone=kwargs.get('phone'),
                role=kwargs.get('role', 'end-user'),
                organization_id=kwargs.get('organization_id'),
                time_zone=kwargs.get('time_zone'),
                locale=kwargs.get('locale'),
                tags=kwargs.get('tags', []),
                user_fields=kwargs.get('user_fields', {}),
                external_id=kwargs.get('external_id')
            )
            
            result = await self.client.create_user(user)
            user_data = result.get('user', {})
            
            return {
                "success": True,
                "message": "User created successfully",
                "user_id": user_data.get('id'),
                "user_url": self.client.get_user_url(user_data.get('id')),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to create Zendesk user: {e}")
            return {
                "success": False,
                "message": f"Failed to create user: {str(e)}"
            }
    
    async def update_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update user
        
        Args:
            user_id: User ID
            **kwargs: Fields to update
            
        Returns:
            Update result
        """
        try:
            result = await self.client.update_user(user_id, kwargs)
            
            return {
                "success": True,
                "message": "User updated successfully",
                "user_id": user_id,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to update Zendesk user {user_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to update user: {str(e)}"
            }
    
    async def search_users(self, query: str) -> Dict[str, Any]:
        """
        Search users
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        try:
            result = await self.client.search_users(query)
            users = result.get('users', [])
            
            return {
                "success": True,
                "message": f"Found {len(users)} users",
                "users": users,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to search Zendesk users: {e}")
            return {
                "success": False,
                "message": f"Failed to search users: {str(e)}"
            }
    
    # Organization Actions
    async def create_organization(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new organization
        
        Args:
            name: Organization name
            **kwargs: Additional organization fields
            
        Returns:
            Organization creation result
        """
        try:
            organization = ZendeskOrganization(
                name=name,
                details=kwargs.get('details'),
                notes=kwargs.get('notes'),
                domain_names=kwargs.get('domain_names', []),
                tags=kwargs.get('tags', []),
                organization_fields=kwargs.get('organization_fields', {}),
                external_id=kwargs.get('external_id')
            )
            
            result = await self.client.create_organization(organization)
            org_data = result.get('organization', {})
            
            return {
                "success": True,
                "message": "Organization created successfully",
                "organization_id": org_data.get('id'),
                "organization_url": self.client.get_organization_url(org_data.get('id')),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to create Zendesk organization: {e}")
            return {
                "success": False,
                "message": f"Failed to create organization: {str(e)}"
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
            result = await self.client.get_ticket(ticket_id, include=['users', 'groups'])
            
            return {
                "success": True,
                "message": "Ticket retrieved successfully",
                "ticket_id": ticket_id,
                "ticket_url": self.client.get_ticket_url(ticket_id),
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to get Zendesk ticket {ticket_id}: {e}")
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
            users = result.get('users', [])
            
            return {
                "success": True,
                "message": f"Retrieved {len(users)} agents",
                "agents": users,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to list Zendesk agents: {e}")
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
            groups = result.get('groups', [])
            
            return {
                "success": True,
                "message": f"Retrieved {len(groups)} groups",
                "groups": groups,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to list Zendesk groups: {e}")
            return {
                "success": False,
                "message": f"Failed to list groups: {str(e)}"
            }
    
    async def search_tickets(self, query: str) -> Dict[str, Any]:
        """
        Search tickets
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        try:
            result = await self.client.search_tickets(query)
            tickets = result.get('results', [])
            
            return {
                "success": True,
                "message": f"Found {len(tickets)} tickets",
                "tickets": tickets,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Failed to search Zendesk tickets: {e}")
            return {
                "success": False,
                "message": f"Failed to search tickets: {str(e)}"
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
            logger.error(f"Failed to bulk update Zendesk tickets: {e}")
            return {
                "success": False,
                "message": f"Failed to bulk update tickets: {str(e)}"
            }
    
    # Helper Methods
    async def _find_or_create_user(self, email: str, name: str) -> Dict[str, Any]:
        """Find existing user or create new one"""
        try:
            # Search for existing user
            search_result = await self.client.search_users(f"email:{email}")
            users = search_result.get('users', [])
            
            if users:
                return {
                    "success": True,
                    "user_id": users[0]['id'],
                    "created": False
                }
            
            # Create new user
            user = ZendeskUser(name=name, email=email)
            create_result = await self.client.create_user(user)
            user_data = create_result.get('user', {})
            
            return {
                "success": True,
                "user_id": user_data.get('id'),
                "created": True
            }
            
        except Exception as e:
            logger.error(f"Failed to find or create user {email}: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def _format_custom_fields(self, custom_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format custom fields for Zendesk API"""
        return [
            {"id": field_id, "value": value}
            for field_id, value in custom_fields.items()
        ]
    
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
                    {"name": "requester_email", "type": "string", "required": False, "description": "Requester email"},
                    {"name": "requester_name", "type": "string", "required": False, "description": "Requester name"},
                    {"name": "priority", "type": "string", "required": False, "description": "Priority (low, normal, high, urgent)"},
                    {"name": "status", "type": "string", "required": False, "description": "Status", "default": "new"},
                    {"name": "type", "type": "string", "required": False, "description": "Type (problem, incident, question, task)"},
                    {"name": "assignee_id", "type": "integer", "required": False, "description": "Assignee ID"},
                    {"name": "group_id", "type": "integer", "required": False, "description": "Group ID"},
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
                    {"name": "priority", "type": "string", "required": False, "description": "New priority"},
                    {"name": "status", "type": "string", "required": False, "description": "New status"},
                    {"name": "assignee_id", "type": "integer", "required": False, "description": "New assignee ID"},
                    {"name": "group_id", "type": "integer", "required": False, "description": "New group ID"},
                ]
            },
            {
                "name": "add_comment",
                "display_name": "Add Comment",
                "description": "Add a comment to a ticket",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "body", "type": "string", "required": True, "description": "Comment content"},
                    {"name": "public", "type": "boolean", "required": False, "description": "Public comment", "default": True},
                ]
            },
            {
                "name": "assign_ticket",
                "display_name": "Assign Ticket",
                "description": "Assign ticket to agent/group",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "assignee_id", "type": "integer", "required": True, "description": "Assignee ID"},
                    {"name": "group_id", "type": "integer", "required": False, "description": "Group ID"},
                ]
            },
            {
                "name": "change_status",
                "display_name": "Change Status",
                "description": "Change ticket status",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "status", "type": "string", "required": True, "description": "New status (new, open, pending, hold, solved, closed)"},
                ]
            },
            {
                "name": "set_priority",
                "display_name": "Set Priority",
                "description": "Set ticket priority",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "priority", "type": "string", "required": True, "description": "Priority (low, normal, high, urgent)"},
                ]
            },
            {
                "name": "add_tags",
                "display_name": "Add Tags",
                "description": "Add tags to ticket",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "tags", "type": "array", "required": True, "description": "Tags to add"},
                ]
            },
            {
                "name": "apply_macro",
                "display_name": "Apply Macro",
                "description": "Apply macro to ticket",
                "parameters": [
                    {"name": "ticket_id", "type": "integer", "required": True, "description": "Ticket ID"},
                    {"name": "macro_id", "type": "integer", "required": True, "description": "Macro ID"},
                ]
            },
            {
                "name": "create_user",
                "display_name": "Create User",
                "description": "Create a new user",
                "parameters": [
                    {"name": "name", "type": "string", "required": True, "description": "User name"},
                    {"name": "email", "type": "string", "required": True, "description": "User email"},
                    {"name": "role", "type": "string", "required": False, "description": "User role", "default": "end-user"},
                    {"name": "organization_id", "type": "integer", "required": False, "description": "Organization ID"},
                ]
            }
        ]

