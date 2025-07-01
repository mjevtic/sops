"""
Freshdesk API client for comprehensive ticket and customer management
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


class FreshdeskTicket(BaseModel):
    """Freshdesk ticket model"""
    id: Optional[int] = None
    subject: str
    description: str
    status: int = 2  # Open
    priority: int = 1  # Low
    type: Optional[str] = None
    source: int = 2  # Portal
    requester_id: Optional[int] = None
    responder_id: Optional[int] = None
    group_id: Optional[int] = None
    company_id: Optional[int] = None
    product_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    cc_emails: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    due_by: Optional[datetime] = None
    fr_due_by: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FreshdeskContact(BaseModel):
    """Freshdesk contact model"""
    id: Optional[int] = None
    name: str
    email: str
    phone: Optional[str] = None
    mobile: Optional[str] = None
    twitter_id: Optional[str] = None
    unique_external_id: Optional[str] = None
    company_id: Optional[int] = None
    view_all_tickets: bool = False
    other_emails: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FreshdeskCompany(BaseModel):
    """Freshdesk company model"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    note: Optional[str] = None
    domains: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FreshdeskNote(BaseModel):
    """Freshdesk note model"""
    id: Optional[int] = None
    body: str
    private: bool = False
    incoming: bool = False
    notify_emails: List[str] = Field(default_factory=list)
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FreshdeskTimeEntry(BaseModel):
    """Freshdesk time entry model"""
    id: Optional[int] = None
    time_spent: str  # Format: "01:30" (1 hour 30 minutes)
    billable: bool = True
    note: Optional[str] = None
    agent_id: Optional[int] = None
    executed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FreshdeskClient:
    """
    Comprehensive Freshdesk API client with full CRUD operations
    """
    
    # Freshdesk ticket statuses
    STATUS_OPEN = 2
    STATUS_PENDING = 3
    STATUS_RESOLVED = 4
    STATUS_CLOSED = 5
    
    # Freshdesk ticket priorities
    PRIORITY_LOW = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_HIGH = 3
    PRIORITY_URGENT = 4
    
    # Freshdesk ticket sources
    SOURCE_EMAIL = 1
    SOURCE_PORTAL = 2
    SOURCE_PHONE = 3
    SOURCE_CHAT = 7
    SOURCE_FEEDBACK_WIDGET = 9
    SOURCE_OUTBOUND_EMAIL = 10
    
    def __init__(self, domain: str, api_key: str):
        """
        Initialize Freshdesk client
        
        Args:
            domain: Freshdesk domain (e.g., 'company.freshdesk.com')
            api_key: Freshdesk API key
        """
        self.domain = domain.rstrip('/')
        if not self.domain.startswith('http'):
            self.domain = f"https://{self.domain}"
        
        self.api_key = api_key
        self.base_url = f"{self.domain}/api/v2"
        
        # Setup authentication
        self.auth = aiohttp.BasicAuth(self.api_key, 'X')
        
        # Rate limiting
        self.rate_limit_remaining = 1000
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
        Make authenticated request to Freshdesk API
        
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
                    self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                    
                    if response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        return await self._make_request(method, endpoint, data, params, files)
                    
                    response_text = await response.text()
                    
                    if response.status >= 400:
                        logger.error(f"Freshdesk API error {response.status}: {response_text}")
                        raise Exception(f"Freshdesk API error {response.status}: {response_text}")
                    
                    # Handle empty responses
                    if not response_text:
                        return {}
                    
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        return {"raw_response": response_text}
                        
        except aiohttp.ClientError as e:
            logger.error(f"Freshdesk API request failed: {e}")
            raise Exception(f"Freshdesk API request failed: {e}")
    
    # Ticket Management
    async def create_ticket(self, ticket: FreshdeskTicket) -> Dict:
        """Create a new ticket"""
        data = ticket.dict(exclude_none=True, exclude={'id', 'created_at', 'updated_at'})
        
        # Convert datetime objects to ISO format
        if ticket.due_by:
            data['due_by'] = ticket.due_by.isoformat()
        if ticket.fr_due_by:
            data['fr_due_by'] = ticket.fr_due_by.isoformat()
        
        return await self._make_request('POST', '/tickets', data=data)
    
    async def get_ticket(self, ticket_id: int, include: Optional[List[str]] = None) -> Dict:
        """Get ticket by ID"""
        params = {}
        if include:
            params['include'] = ','.join(include)
        
        return await self._make_request('GET', f'/tickets/{ticket_id}', params=params)
    
    async def update_ticket(self, ticket_id: int, updates: Dict) -> Dict:
        """Update ticket"""
        return await self._make_request('PUT', f'/tickets/{ticket_id}', data=updates)
    
    async def delete_ticket(self, ticket_id: int) -> bool:
        """Delete ticket"""
        await self._make_request('DELETE', f'/tickets/{ticket_id}')
        return True
    
    async def list_tickets(
        self,
        filter_name: Optional[str] = None,
        page: int = 1,
        per_page: int = 30,
        updated_since: Optional[datetime] = None,
        include: Optional[List[str]] = None
    ) -> Dict:
        """List tickets with filtering"""
        params = {
            'page': page,
            'per_page': min(per_page, 100)  # Max 100 per page
        }
        
        if updated_since:
            params['updated_since'] = updated_since.isoformat()
        
        if include:
            params['include'] = ','.join(include)
        
        endpoint = '/tickets'
        if filter_name:
            endpoint = f'/search/tickets?query="{filter_name}"'
        
        return await self._make_request('GET', endpoint, params=params)
    
    async def add_note_to_ticket(self, ticket_id: int, note: FreshdeskNote) -> Dict:
        """Add note to ticket"""
        data = note.dict(exclude_none=True, exclude={'id', 'created_at', 'updated_at'})
        return await self._make_request('POST', f'/tickets/{ticket_id}/notes', data=data)
    
    async def add_reply_to_ticket(self, ticket_id: int, body: str, cc_emails: Optional[List[str]] = None) -> Dict:
        """Add reply to ticket"""
        data = {
            'body': body,
            'cc_emails': cc_emails or []
        }
        return await self._make_request('POST', f'/tickets/{ticket_id}/reply', data=data)
    
    # Contact Management
    async def create_contact(self, contact: FreshdeskContact) -> Dict:
        """Create a new contact"""
        data = contact.dict(exclude_none=True, exclude={'id', 'created_at', 'updated_at'})
        return await self._make_request('POST', '/contacts', data=data)
    
    async def get_contact(self, contact_id: int) -> Dict:
        """Get contact by ID"""
        return await self._make_request('GET', f'/contacts/{contact_id}')
    
    async def update_contact(self, contact_id: int, updates: Dict) -> Dict:
        """Update contact"""
        return await self._make_request('PUT', f'/contacts/{contact_id}', data=updates)
    
    async def delete_contact(self, contact_id: int) -> bool:
        """Delete contact"""
        await self._make_request('DELETE', f'/contacts/{contact_id}')
        return True
    
    async def search_contacts(self, query: str) -> Dict:
        """Search contacts"""
        params = {'query': f'email:{query} OR name:{query}'}
        return await self._make_request('GET', '/search/contacts', params=params)
    
    async def list_contacts(self, page: int = 1, per_page: int = 30) -> Dict:
        """List contacts"""
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }
        return await self._make_request('GET', '/contacts', params=params)
    
    # Company Management
    async def create_company(self, company: FreshdeskCompany) -> Dict:
        """Create a new company"""
        data = company.dict(exclude_none=True, exclude={'id', 'created_at', 'updated_at'})
        return await self._make_request('POST', '/companies', data=data)
    
    async def get_company(self, company_id: int) -> Dict:
        """Get company by ID"""
        return await self._make_request('GET', f'/companies/{company_id}')
    
    async def update_company(self, company_id: int, updates: Dict) -> Dict:
        """Update company"""
        return await self._make_request('PUT', f'/companies/{company_id}', data=updates)
    
    async def list_companies(self, page: int = 1, per_page: int = 30) -> Dict:
        """List companies"""
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }
        return await self._make_request('GET', '/companies', params=params)
    
    # Time Tracking
    async def add_time_entry(self, ticket_id: int, time_entry: FreshdeskTimeEntry) -> Dict:
        """Add time entry to ticket"""
        data = time_entry.dict(exclude_none=True, exclude={'id', 'created_at', 'updated_at'})
        if time_entry.executed_at:
            data['executed_at'] = time_entry.executed_at.isoformat()
        
        return await self._make_request('POST', f'/tickets/{ticket_id}/time_entries', data=data)
    
    async def get_time_entries(self, ticket_id: int) -> Dict:
        """Get time entries for ticket"""
        return await self._make_request('GET', f'/tickets/{ticket_id}/time_entries')
    
    # Agents and Groups
    async def list_agents(self) -> Dict:
        """List all agents"""
        return await self._make_request('GET', '/agents')
    
    async def get_agent(self, agent_id: int) -> Dict:
        """Get agent by ID"""
        return await self._make_request('GET', f'/agents/{agent_id}')
    
    async def list_groups(self) -> Dict:
        """List all groups"""
        return await self._make_request('GET', '/groups')
    
    async def get_group(self, group_id: int) -> Dict:
        """Get group by ID"""
        return await self._make_request('GET', f'/groups/{group_id}')
    
    # Products and Categories
    async def list_products(self) -> Dict:
        """List all products"""
        return await self._make_request('GET', '/products')
    
    async def list_ticket_fields(self) -> Dict:
        """List ticket fields"""
        return await self._make_request('GET', '/ticket_fields')
    
    # Bulk Operations
    async def bulk_update_tickets(self, ticket_ids: List[int], updates: Dict) -> Dict:
        """Bulk update multiple tickets"""
        data = {
            'ids': ticket_ids,
            'properties': updates
        }
        return await self._make_request('PUT', '/tickets/bulk_update', data=data)
    
    # Statistics and Reports
    async def get_ticket_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get ticket metrics for date range"""
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        return await self._make_request('GET', '/reports/ticket_metrics', params=params)
    
    async def get_agent_performance(self, agent_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Get agent performance metrics"""
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        return await self._make_request('GET', f'/reports/agents/{agent_id}', params=params)
    
    # Utility Methods
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            await self._make_request('GET', '/agents/me')
            return True
        except Exception as e:
            logger.error(f"Freshdesk connection test failed: {e}")
            return False
    
    def get_ticket_url(self, ticket_id: int) -> str:
        """Get ticket URL"""
        return f"{self.domain}/a/tickets/{ticket_id}"
    
    def get_contact_url(self, contact_id: int) -> str:
        """Get contact URL"""
        return f"{self.domain}/a/contacts/{contact_id}"
    
    @staticmethod
    def format_time_spent(hours: float) -> str:
        """Format hours as time string (HH:MM)"""
        total_minutes = int(hours * 60)
        hours_part = total_minutes // 60
        minutes_part = total_minutes % 60
        return f"{hours_part:02d}:{minutes_part:02d}"
    
    @staticmethod
    def parse_time_spent(time_str: str) -> float:
        """Parse time string (HH:MM) to hours"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours + (minutes / 60)
        except (ValueError, AttributeError):
            return 0.0

