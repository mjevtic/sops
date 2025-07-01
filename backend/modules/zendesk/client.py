"""
Zendesk API client for comprehensive ticket and user management
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ZendeskTicket(BaseModel):
    """Zendesk ticket model"""
    id: Optional[int] = None
    subject: str
    comment: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    status: str = "new"  # new, open, pending, hold, solved, closed
    priority: Optional[str] = None  # low, normal, high, urgent
    type: Optional[str] = None  # problem, incident, question, task
    requester_id: Optional[int] = None
    submitter_id: Optional[int] = None
    assignee_id: Optional[int] = None
    group_id: Optional[int] = None
    organization_id: Optional[int] = None
    collaborator_ids: List[int] = Field(default_factory=list)
    follower_ids: List[int] = Field(default_factory=list)
    email_cc_ids: List[int] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    custom_fields: List[Dict[str, Any]] = Field(default_factory=list)
    external_id: Optional[str] = None
    due_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ZendeskUser(BaseModel):
    """Zendesk user model"""
    id: Optional[int] = None
    name: str
    email: str
    phone: Optional[str] = None
    role: str = "end-user"  # end-user, agent, admin
    verified: bool = False
    active: bool = True
    organization_id: Optional[int] = None
    time_zone: Optional[str] = None
    locale: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    user_fields: Dict[str, Any] = Field(default_factory=dict)
    external_id: Optional[str] = None
    alias: Optional[str] = None
    details: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ZendeskOrganization(BaseModel):
    """Zendesk organization model"""
    id: Optional[int] = None
    name: str
    details: Optional[str] = None
    notes: Optional[str] = None
    domain_names: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    organization_fields: Dict[str, Any] = Field(default_factory=dict)
    external_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ZendeskComment(BaseModel):
    """Zendesk comment model"""
    id: Optional[int] = None
    body: str
    html_body: Optional[str] = None
    plain_body: Optional[str] = None
    public: bool = True
    author_id: Optional[int] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    audit_id: Optional[int] = None
    via: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class ZendeskClient:
    """
    Comprehensive Zendesk API client with full CRUD operations
    """
    
    # Zendesk ticket statuses
    STATUS_NEW = "new"
    STATUS_OPEN = "open"
    STATUS_PENDING = "pending"
    STATUS_HOLD = "hold"
    STATUS_SOLVED = "solved"
    STATUS_CLOSED = "closed"
    
    # Zendesk ticket priorities
    PRIORITY_LOW = "low"
    PRIORITY_NORMAL = "normal"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"
    
    # Zendesk ticket types
    TYPE_PROBLEM = "problem"
    TYPE_INCIDENT = "incident"
    TYPE_QUESTION = "question"
    TYPE_TASK = "task"
    
    def __init__(self, subdomain: str, email: str, api_token: str):
        """
        Initialize Zendesk client
        
        Args:
            subdomain: Zendesk subdomain (e.g., 'company' for company.zendesk.com)
            email: Agent email address
            api_token: Zendesk API token
        """
        self.subdomain = subdomain
        self.email = email
        self.api_token = api_token
        self.base_url = f"https://{subdomain}.zendesk.com/api/v2"
        
        # Setup authentication
        self.auth = aiohttp.BasicAuth(f"{email}/token", api_token)
        
        # Rate limiting
        self.rate_limit_remaining = 700  # Zendesk default
        self.rate_limit_reset = None
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict:
        """
        Make authenticated request to Zendesk API
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            files: File uploads
            
        Returns:
            Response data
            
        Raises:
            Exception: If request fails
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'SupportOps-Automator/1.0'
        }
        
        # Handle file uploads
        if files:
            headers.pop('Content-Type')  # Let aiohttp set multipart content-type
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    auth=self.auth,
                    headers=headers,
                    json=data if not files else None,
                    data=files if files else None,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    # Update rate limit info
                    self.rate_limit_remaining = int(response.headers.get('X-Rate-Limit-Remaining', 0))
                    
                    if response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        return await self._make_request(method, endpoint, data, params, files)
                    
                    response_text = await response.text()
                    
                    if response.status >= 400:
                        logger.error(f"Zendesk API error {response.status}: {response_text}")
                        raise Exception(f"Zendesk API error {response.status}: {response_text}")
                    
                    # Handle empty responses
                    if not response_text:
                        return {}
                    
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        return {"raw_response": response_text}
                        
        except aiohttp.ClientError as e:
            logger.error(f"Zendesk API request failed: {e}")
            raise Exception(f"Zendesk API request failed: {e}")
    
    # Ticket Management
    async def create_ticket(self, ticket: ZendeskTicket) -> Dict:
        """Create a new ticket"""
        ticket_data = ticket.dict(exclude_none=True, exclude={'id', 'created_at', 'updated_at'})
        
        # Handle comment/description
        if ticket.description and not ticket.comment:
            ticket_data['comment'] = {'body': ticket.description}
        
        # Convert datetime objects to ISO format
        if ticket.due_at:
            ticket_data['due_at'] = ticket.due_at.isoformat()
        
        data = {'ticket': ticket_data}
        return await self._make_request('POST', '/tickets.json', data=data)
    
    async def get_ticket(self, ticket_id: int, include: Optional[List[str]] = None) -> Dict:
        """Get ticket by ID"""
        params = {}
        if include:
            params['include'] = ','.join(include)
        
        return await self._make_request('GET', f'/tickets/{ticket_id}.json', params=params)
    
    async def update_ticket(self, ticket_id: int, updates: Dict) -> Dict:
        """Update ticket"""
        data = {'ticket': updates}
        return await self._make_request('PUT', f'/tickets/{ticket_id}.json', data=data)
    
    async def delete_ticket(self, ticket_id: int) -> bool:
        """Delete ticket"""
        await self._make_request('DELETE', f'/tickets/{ticket_id}.json')
        return True
    
    async def list_tickets(
        self,
        page: int = 1,
        per_page: int = 100,
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
        include: Optional[List[str]] = None
    ) -> Dict:
        """List tickets with pagination"""
        params = {
            'page': page,
            'per_page': min(per_page, 100),  # Max 100 per page
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        
        if include:
            params['include'] = ','.join(include)
        
        return await self._make_request('GET', '/tickets.json', params=params)
    
    async def search_tickets(self, query: str, sort_by: str = 'created_at', sort_order: str = 'desc') -> Dict:
        """Search tickets"""
        params = {
            'query': query,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        return await self._make_request('GET', '/search.json', params=params)
    
    async def add_comment_to_ticket(self, ticket_id: int, comment: ZendeskComment) -> Dict:
        """Add comment to ticket"""
        comment_data = comment.dict(exclude_none=True, exclude={'id', 'created_at', 'audit_id'})
        data = {'ticket': {'comment': comment_data}}
        return await self._make_request('PUT', f'/tickets/{ticket_id}.json', data=data)
    
    async def get_ticket_comments(self, ticket_id: int, include_inline_images: bool = False) -> Dict:
        """Get ticket comments"""
        params = {}
        if include_inline_images:
            params['include_inline_images'] = 'true'
        
        return await self._make_request('GET', f'/tickets/{ticket_id}/comments.json', params=params)
    
    # User Management
    async def create_user(self, user: ZendeskUser) -> Dict:
        """Create a new user"""
        user_data = user.dict(exclude_none=True, exclude={'id', 'created_at', 'updated_at'})
        data = {'user': user_data}
        return await self._make_request('POST', '/users.json', data=data)
    
    async def get_user(self, user_id: int) -> Dict:
        """Get user by ID"""
        return await self._make_request('GET', f'/users/{user_id}.json')
    
    async def update_user(self, user_id: int, updates: Dict) -> Dict:
        """Update user"""
        data = {'user': updates}
        return await self._make_request('PUT', f'/users/{user_id}.json', data=data)
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        await self._make_request('DELETE', f'/users/{user_id}.json')
        return True
    
    async def search_users(self, query: str) -> Dict:
        """Search users"""
        params = {'query': query}
        return await self._make_request('GET', '/users/search.json', params=params)
    
    async def list_users(self, page: int = 1, per_page: int = 100, role: Optional[str] = None) -> Dict:
        """List users"""
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }
        
        if role:
            params['role'] = role
        
        return await self._make_request('GET', '/users.json', params=params)
    
    # Organization Management
    async def create_organization(self, organization: ZendeskOrganization) -> Dict:
        """Create a new organization"""
        org_data = organization.dict(exclude_none=True, exclude={'id', 'created_at', 'updated_at'})
        data = {'organization': org_data}
        return await self._make_request('POST', '/organizations.json', data=data)
    
    async def get_organization(self, org_id: int) -> Dict:
        """Get organization by ID"""
        return await self._make_request('GET', f'/organizations/{org_id}.json')
    
    async def update_organization(self, org_id: int, updates: Dict) -> Dict:
        """Update organization"""
        data = {'organization': updates}
        return await self._make_request('PUT', f'/organizations/{org_id}.json', data=data)
    
    async def list_organizations(self, page: int = 1, per_page: int = 100) -> Dict:
        """List organizations"""
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }
        return await self._make_request('GET', '/organizations.json', params=params)
    
    # Groups and Agents
    async def list_groups(self) -> Dict:
        """List all groups"""
        return await self._make_request('GET', '/groups.json')
    
    async def get_group(self, group_id: int) -> Dict:
        """Get group by ID"""
        return await self._make_request('GET', f'/groups/{group_id}.json')
    
    async def list_agents(self) -> Dict:
        """List all agents"""
        return await self._make_request('GET', '/users.json?role=agent')
    
    async def get_current_user(self) -> Dict:
        """Get current authenticated user"""
        return await self._make_request('GET', '/users/me.json')
    
    # Ticket Fields and Forms
    async def list_ticket_fields(self) -> Dict:
        """List ticket fields"""
        return await self._make_request('GET', '/ticket_fields.json')
    
    async def list_ticket_forms(self) -> Dict:
        """List ticket forms"""
        return await self._make_request('GET', '/ticket_forms.json')
    
    # Attachments
    async def upload_attachment(self, file_path: str, filename: str) -> Dict:
        """Upload attachment"""
        # This would need actual file handling implementation
        # For now, return a placeholder
        return {"upload": {"token": "placeholder_token"}}
    
    # Bulk Operations
    async def bulk_update_tickets(self, ticket_ids: List[int], updates: Dict) -> Dict:
        """Bulk update multiple tickets"""
        data = {
            'tickets': [
                {'id': ticket_id, **updates}
                for ticket_id in ticket_ids
            ]
        }
        return await self._make_request('PUT', '/tickets/update_many.json', data=data)
    
    async def bulk_delete_tickets(self, ticket_ids: List[int]) -> Dict:
        """Bulk delete multiple tickets"""
        params = {'ids': ','.join(map(str, ticket_ids))}
        return await self._make_request('DELETE', '/tickets/destroy_many.json', params=params)
    
    # Macros
    async def list_macros(self) -> Dict:
        """List macros"""
        return await self._make_request('GET', '/macros.json')
    
    async def apply_macro(self, ticket_id: int, macro_id: int) -> Dict:
        """Apply macro to ticket"""
        return await self._make_request('GET', f'/tickets/{ticket_id}/macros/{macro_id}/apply.json')
    
    # Views
    async def list_views(self) -> Dict:
        """List views"""
        return await self._make_request('GET', '/views.json')
    
    async def execute_view(self, view_id: int, page: int = 1, per_page: int = 100) -> Dict:
        """Execute view"""
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }
        return await self._make_request('GET', f'/views/{view_id}/execute.json', params=params)
    
    # Statistics and Reports
    async def get_ticket_metrics(self, start_time: datetime, end_time: datetime) -> Dict:
        """Get ticket metrics for date range"""
        params = {
            'start_time': int(start_time.timestamp()),
            'end_time': int(end_time.timestamp())
        }
        return await self._make_request('GET', '/incremental/ticket_metric_events.json', params=params)
    
    async def get_satisfaction_ratings(self, start_time: datetime, end_time: datetime) -> Dict:
        """Get satisfaction ratings"""
        params = {
            'start_time': int(start_time.timestamp()),
            'end_time': int(end_time.timestamp())
        }
        return await self._make_request('GET', '/satisfaction_ratings.json', params=params)
    
    # Utility Methods
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            await self._make_request('GET', '/users/me.json')
            return True
        except Exception as e:
            logger.error(f"Zendesk connection test failed: {e}")
            return False
    
    def get_ticket_url(self, ticket_id: int) -> str:
        """Get ticket URL"""
        return f"https://{self.subdomain}.zendesk.com/agent/tickets/{ticket_id}"
    
    def get_user_url(self, user_id: int) -> str:
        """Get user URL"""
        return f"https://{self.subdomain}.zendesk.com/agent/users/{user_id}"
    
    def get_organization_url(self, org_id: int) -> str:
        """Get organization URL"""
        return f"https://{self.subdomain}.zendesk.com/agent/organizations/{org_id}"
    
    @staticmethod
    def parse_zendesk_datetime(date_string: str) -> datetime:
        """Parse Zendesk datetime string"""
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def format_zendesk_datetime(dt: datetime) -> str:
        """Format datetime for Zendesk API"""
        return dt.isoformat().replace('+00:00', 'Z')

