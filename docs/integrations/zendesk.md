# Zendesk Integration Guide

## Overview

The Zendesk integration provides comprehensive support for customer service automation, advanced ticket management, and user/organization handling. This integration offers full API coverage with enterprise-grade features including macro support, advanced search capabilities, and bulk operations.

## Features

### 🎫 **Advanced Ticket Management**
- **Create Tickets** - Generate new tickets with full field support and custom fields
- **Update Tickets** - Modify existing tickets with comprehensive field updates
- **Assign Tickets** - Automatic assignment to agents, groups, and organizations
- **Status Management** - Complete status lifecycle management
- **Priority Handling** - Dynamic priority assignment and escalation
- **Tag Management** - Advanced tagging with bulk operations

### 💬 **Communication System**
- **Public Comments** - Customer-facing responses with rich formatting
- **Private Comments** - Internal team communication
- **Comment Threading** - Maintain conversation context
- **Attachment Support** - Handle files, images, and media

### 👥 **User & Organization Management**
- **Create Users** - Add customers, agents, and admins
- **Update Users** - Modify user profiles and permissions
- **Search Users** - Advanced user discovery with filters
- **Organization Handling** - Manage customer organizations and relationships
- **Role Management** - Handle user roles and permissions

### 🔧 **Advanced Features**
- **Macro Support** - Apply predefined actions for consistent workflows
- **Search Capabilities** - Advanced search across tickets, users, and organizations
- **Bulk Operations** - Mass updates for efficiency
- **Custom Fields** - Handle custom ticket and user fields
- **Views & Filters** - Execute saved views and custom filters

### 📊 **Analytics & Reporting**
- **Ticket Metrics** - Comprehensive ticket analytics
- **User Statistics** - Track user engagement and activity
- **Satisfaction Ratings** - Monitor customer satisfaction scores
- **Performance Metrics** - Agent and team performance tracking

## Setup Instructions

### 1. Generate API Token

1. Log in to your Zendesk account as an admin
2. Go to **Admin Center** → **Apps and integrations** → **Zendesk API**
3. Click **Settings** tab
4. Enable **Token Access**
5. Click **Add API token**
6. Copy the generated token

### 2. Configure Integration

```json
{
  "platform": "zendesk",
  "name": "My Zendesk Integration",
  "credentials": {
    "subdomain": "yourcompany",
    "email": "admin@yourcompany.com",
    "api_token": "your-api-token-here"
  },
  "config": {
    "default_group_id": 123,
    "default_priority": "normal",
    "auto_assign": true,
    "enable_macros": true
  }
}
```

### 3. Test Connection

Use the test endpoint to verify your configuration:

```bash
POST /api/integrations/{integration_id}/test
```

Expected response:
```json
{
  "success": true,
  "message": "Connection successful",
  "platform": "zendesk",
  "subdomain": "yourcompany"
}
```

## Available Actions

### Ticket Actions

#### Create Ticket
```json
{
  "action": "create_ticket",
  "parameters": {
    "subject": "Customer Issue",
    "description": "Detailed description of the issue",
    "requester_email": "customer@example.com",
    "requester_name": "Customer Name",
    "priority": "high",
    "status": "open",
    "type": "incident",
    "assignee_id": 456,
    "group_id": 123,
    "organization_id": 789,
    "tags": ["urgent", "billing"],
    "custom_fields": {
      "360001234567": "Technical Issue",
      "360001234568": "Enterprise"
    }
  }
}
```

#### Update Ticket
```json
{
  "action": "update_ticket",
  "parameters": {
    "ticket_id": 12345,
    "subject": "Updated Subject",
    "priority": "urgent",
    "status": "pending",
    "assignee_id": 789,
    "tags": ["resolved", "customer-satisfied"]
  }
}
```

#### Add Comment
```json
{
  "action": "add_comment",
  "parameters": {
    "ticket_id": 12345,
    "body": "Thank you for contacting us. We're investigating this issue.",
    "public": true,
    "author_id": 456
  }
}
```

#### Assign Ticket
```json
{
  "action": "assign_ticket",
  "parameters": {
    "ticket_id": 12345,
    "assignee_id": 456,
    "group_id": 123
  }
}
```

#### Change Status
```json
{
  "action": "change_status",
  "parameters": {
    "ticket_id": 12345,
    "status": "solved"
  }
}
```

Status values:
- `new` - New ticket
- `open` - Open and being worked on
- `pending` - Waiting for customer response
- `hold` - On hold
- `solved` - Resolved
- `closed` - Closed

#### Set Priority
```json
{
  "action": "set_priority",
  "parameters": {
    "ticket_id": 12345,
    "priority": "urgent"
  }
}
```

Priority values:
- `low` - Low priority
- `normal` - Normal priority
- `high` - High priority
- `urgent` - Urgent priority

#### Add Tags
```json
{
  "action": "add_tags",
  "parameters": {
    "ticket_id": 12345,
    "tags": ["escalated", "vip-customer", "technical-issue"]
  }
}
```

#### Apply Macro
```json
{
  "action": "apply_macro",
  "parameters": {
    "ticket_id": 12345,
    "macro_id": 678
  }
}
```

### User Actions

#### Create User
```json
{
  "action": "create_user",
  "parameters": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "role": "end-user",
    "organization_id": 789,
    "phone": "+1-555-123-4567",
    "time_zone": "America/New_York",
    "locale": "en-US",
    "tags": ["vip", "enterprise"],
    "user_fields": {
      "department": "Engineering",
      "employee_id": "EMP001"
    }
  }
}
```

#### Update User
```json
{
  "action": "update_user",
  "parameters": {
    "user_id": 12345,
    "name": "John Smith",
    "phone": "+1-555-987-6543",
    "role": "agent",
    "tags": ["senior", "technical-expert"]
  }
}
```

#### Search Users
```json
{
  "action": "search_users",
  "parameters": {
    "query": "email:john.doe@example.com"
  }
}
```

### Organization Actions

#### Create Organization
```json
{
  "action": "create_organization",
  "parameters": {
    "name": "Acme Corporation",
    "details": "Large enterprise customer",
    "notes": "VIP customer with premium support",
    "domain_names": ["acme.com", "acme.org"],
    "tags": ["enterprise", "vip"],
    "organization_fields": {
      "account_type": "Enterprise",
      "contract_value": "100000"
    }
  }
}
```

### Utility Actions

#### Get Ticket Info
```json
{
  "action": "get_ticket_info",
  "parameters": {
    "ticket_id": 12345
  }
}
```

#### List Agents
```json
{
  "action": "list_agents",
  "parameters": {}
}
```

#### List Groups
```json
{
  "action": "list_groups",
  "parameters": {}
}
```

#### Search Tickets
```json
{
  "action": "search_tickets",
  "parameters": {
    "query": "status:open priority:urgent"
  }
}
```

#### Bulk Update Tickets
```json
{
  "action": "bulk_update_tickets",
  "parameters": {
    "ticket_ids": [12345, 12346, 12347],
    "updates": {
      "status": "pending",
      "assignee_id": 456,
      "tags": ["bulk-updated"]
    }
  }
}
```

## Webhook Configuration

### 1. Setup Webhook in Zendesk

1. Go to **Admin Center** → **Apps and integrations** → **Webhooks**
2. Click **Create webhook**
3. Configure the webhook:
   - **Endpoint URL**: `https://your-domain.com/api/webhooks/zendesk`
   - **Request method**: POST
   - **Request format**: JSON
   - **Authentication**: Bearer token or Basic auth (optional)

### 2. Configure Triggers

Create triggers to send webhook events:

1. Go to **Admin Center** → **Objects and rules** → **Business rules** → **Triggers**
2. Create new trigger
3. Set conditions (e.g., "Ticket is created")
4. Add action: "Notify webhook"
5. Select your webhook endpoint

### 3. Select Events

Configure triggers for these events:
- ✅ Ticket Created
- ✅ Ticket Updated
- ✅ Ticket Solved
- ✅ Ticket Closed
- ✅ Comment Created
- ✅ User Created
- ✅ User Updated
- ✅ Organization Created
- ✅ Organization Updated

### 4. Configure Security

Set the webhook secret in your environment:
```bash
ZENDESK_WEBHOOK_SECRET=your-webhook-secret-here
```

### 5. Test Webhook

Use Zendesk's webhook testing feature to verify the configuration.

## Supported Events

### Ticket Events
- **ticket.created** - New ticket created
- **ticket.updated** - Ticket properties changed
- **ticket.solved** - Ticket marked as solved
- **ticket.closed** - Ticket closed
- **comment.created** - Comment added to ticket

### User Events
- **user.created** - New user added
- **user.updated** - User information changed

### Organization Events
- **organization.created** - New organization added
- **organization.updated** - Organization information changed

## Error Handling

### Common Errors

#### Authentication Errors
```json
{
  "success": false,
  "message": "Authentication failed: Invalid API token"
}
```

**Solution**: Verify your API token, email, and subdomain configuration.

#### Rate Limiting
```json
{
  "success": false,
  "message": "Rate limit exceeded. Please try again later."
}
```

**Solution**: The integration automatically handles rate limiting with exponential backoff.

#### Invalid Ticket ID
```json
{
  "success": false,
  "message": "Ticket not found: Invalid ticket ID"
}
```

**Solution**: Verify the ticket ID exists and is accessible.

#### Permission Denied
```json
{
  "success": false,
  "message": "Permission denied: Insufficient privileges"
}
```

**Solution**: Ensure the API user has required permissions for the operation.

### Retry Logic

The integration includes automatic retry logic for:
- Network timeouts
- Rate limiting (429 errors)
- Temporary server errors (5xx)
- Authentication token refresh

## Best Practices

### 1. **API Token Security**
- Store API tokens securely using environment variables
- Rotate API tokens regularly
- Use dedicated API tokens for automation
- Enable IP restrictions when possible

### 2. **Rate Limiting**
- Respect Zendesk's rate limits (700 requests/minute)
- Use bulk operations when possible
- Implement exponential backoff for retries
- Monitor rate limit headers

### 3. **Error Handling**
- Always check response status
- Implement proper error logging
- Use try-catch blocks for API calls
- Handle partial failures in bulk operations

### 4. **Data Validation**
- Validate input data before API calls
- Check required fields
- Sanitize user input
- Validate custom field IDs

### 5. **Performance Optimization**
- Use bulk operations for mass updates
- Cache frequently accessed data (agents, groups)
- Minimize API calls with efficient queries
- Use pagination for large datasets

## Advanced Features

### Custom Fields

Handle custom fields in tickets and users:

```json
{
  "custom_fields": [
    {
      "id": 360001234567,
      "value": "Technical Issue"
    },
    {
      "id": 360001234568,
      "value": "High"
    }
  ]
}
```

### Macro Management

Apply macros for consistent ticket handling:

```json
{
  "action": "apply_macro",
  "parameters": {
    "ticket_id": 12345,
    "macro_id": 678
  }
}
```

### Advanced Search

Use Zendesk's search syntax:

```json
{
  "query": "status:open priority:urgent created>2024-01-01 assignee:john@company.com"
}
```

Search operators:
- `status:open` - Filter by status
- `priority:urgent` - Filter by priority
- `created>2024-01-01` - Date range filters
- `assignee:email` - Filter by assignee
- `organization:name` - Filter by organization
- `tags:tag_name` - Filter by tags

### Bulk Operations

Efficiently update multiple tickets:

```json
{
  "action": "bulk_update_tickets",
  "parameters": {
    "ticket_ids": [1, 2, 3, 4, 5],
    "updates": {
      "status": "pending",
      "assignee_id": 456,
      "priority": "high"
    }
  }
}
```

## Troubleshooting

### Connection Issues

1. **Verify Subdomain**: Ensure subdomain is correct (without .zendesk.com)
2. **Check API Token**: Verify token is valid and not expired
3. **Email Verification**: Ensure email matches the token owner
4. **Network Access**: Ensure server can reach Zendesk APIs
5. **SSL/TLS**: Verify SSL certificate validation

### Webhook Issues

1. **URL Accessibility**: Ensure webhook URL is publicly accessible
2. **SSL Certificate**: Use valid SSL certificate for HTTPS
3. **Response Time**: Ensure webhook endpoint responds within 10 seconds
4. **Trigger Configuration**: Verify triggers are properly configured
5. **Authentication**: Check webhook authentication settings

### Permission Issues

1. **API Permissions**: Verify API token has required permissions
2. **User Role**: Check if the API user has appropriate role
3. **Organization Access**: Ensure user has access to target organizations
4. **Custom Field Access**: Verify permissions for custom fields

### Performance Issues

1. **Rate Limiting**: Monitor rate limit usage
2. **Bulk Operations**: Use bulk endpoints for mass updates
3. **Pagination**: Implement proper pagination for large datasets
4. **Caching**: Cache frequently accessed data

## API Reference

### Base URL
```
https://your-subdomain.zendesk.com/api/v2
```

### Authentication
```
Authorization: Basic base64(email/token:api_token)
```

### Rate Limits
- **700 requests per minute** per account
- **Rate limit headers** included in responses
- **Automatic retry** with exponential backoff

### Response Format
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    "ticket_id": 12345,
    "ticket_url": "https://company.zendesk.com/agent/tickets/12345"
  }
}
```

## Support

For additional help with Zendesk integration:

1. **Documentation**: [Zendesk API Documentation](https://developer.zendesk.com/api-reference/)
2. **Support**: Contact your system administrator
3. **Logs**: Check application logs for detailed error information
4. **Testing**: Use the integration test endpoint for troubleshooting
5. **Community**: Zendesk Developer Community

