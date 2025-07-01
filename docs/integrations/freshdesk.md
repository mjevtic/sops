# Freshdesk Integration Guide

## Overview

The Freshdesk integration provides comprehensive support for automating customer support workflows, ticket management, and customer data synchronization. This integration offers full API coverage with advanced features for enterprise-grade support operations.

## Features

### 🎫 **Ticket Management**
- **Create Tickets** - Generate new support tickets with full field support
- **Update Tickets** - Modify existing tickets with bulk update capabilities
- **Assign Tickets** - Automatic assignment to agents and groups
- **Status Management** - Change ticket status with workflow automation
- **Priority Handling** - Set and modify ticket priorities based on rules
- **Tag Management** - Add and manage tags for categorization

### 📝 **Communication**
- **Add Notes** - Internal notes for team collaboration
- **Add Replies** - Customer-facing responses with CC support
- **Time Tracking** - Log billable and non-billable time entries
- **Attachment Support** - Handle file attachments and media

### 👥 **Contact & Company Management**
- **Create Contacts** - Add new customers to the system
- **Update Contacts** - Modify customer information
- **Search Contacts** - Find customers with advanced queries
- **Company Management** - Handle organizational relationships

### 🔄 **Bulk Operations**
- **Mass Updates** - Update multiple tickets simultaneously
- **Bulk Assignment** - Assign multiple tickets to agents/groups
- **Batch Processing** - Efficient handling of large datasets

### 📊 **Analytics & Reporting**
- **Agent Performance** - Track agent productivity and metrics
- **Group Statistics** - Monitor team performance
- **Ticket Metrics** - Analyze ticket volume and resolution times

## Setup Instructions

### 1. Generate API Key

1. Log in to your Freshdesk account as an admin
2. Go to **Admin** → **API Settings**
3. Generate a new API key or use an existing one
4. Copy the API key for configuration

### 2. Configure Integration

```json
{
  "platform": "freshdesk",
  "name": "My Freshdesk Integration",
  "credentials": {
    "domain": "yourcompany.freshdesk.com",
    "api_key": "your-api-key-here"
  },
  "config": {
    "default_group_id": 123,
    "default_priority": 1,
    "auto_assign": true
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
  "platform": "freshdesk",
  "domain": "yourcompany.freshdesk.com"
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
    "email": "customer@example.com",
    "name": "Customer Name",
    "priority": 2,
    "status": 2,
    "type": "Question",
    "group_id": 123,
    "agent_id": 456,
    "tags": ["urgent", "billing"],
    "custom_fields": {
      "cf_category": "Technical"
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
    "priority": 3,
    "status": 3,
    "tags": ["resolved", "customer-satisfied"]
  }
}
```

#### Add Note
```json
{
  "action": "add_note",
  "parameters": {
    "ticket_id": 12345,
    "body": "Internal note for team reference",
    "private": true
  }
}
```

#### Add Reply
```json
{
  "action": "add_reply",
  "parameters": {
    "ticket_id": 12345,
    "body": "Thank you for contacting us. We'll resolve this shortly.",
    "cc_emails": ["manager@company.com"]
  }
}
```

#### Assign Ticket
```json
{
  "action": "assign_ticket",
  "parameters": {
    "ticket_id": 12345,
    "agent_id": 456,
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
    "status": 4
  }
}
```

Status values:
- `2` - Open
- `3` - Pending
- `4` - Resolved
- `5` - Closed

#### Add Time Entry
```json
{
  "action": "add_time_entry",
  "parameters": {
    "ticket_id": 12345,
    "time_spent": "02:30",
    "note": "Troubleshooting customer issue",
    "billable": true
  }
}
```

### Contact Actions

#### Create Contact
```json
{
  "action": "create_contact",
  "parameters": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "company_id": 789,
    "tags": ["vip", "enterprise"]
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

## Webhook Configuration

### 1. Setup Webhook in Freshdesk

1. Go to **Admin** → **Automations** → **Webhooks**
2. Click **"New Webhook"**
3. Configure the webhook:
   - **URL**: `https://your-domain.com/api/webhooks/freshdesk`
   - **Method**: POST
   - **Content Type**: application/json
   - **Secret**: Set a strong webhook secret

### 2. Select Events

Choose the events you want to monitor:
- ✅ Ticket Created
- ✅ Ticket Updated
- ✅ Ticket Resolved
- ✅ Ticket Closed
- ✅ Note Created
- ✅ Contact Created
- ✅ Contact Updated

### 3. Configure Security

Set the webhook secret in your environment:
```bash
FRESHDESK_WEBHOOK_SECRET=your-webhook-secret-here
```

### 4. Test Webhook

Use the webhook test feature in Freshdesk to verify the configuration.

## Supported Events

### Ticket Events
- **ticket_created** - New ticket created
- **ticket_updated** - Ticket properties changed
- **ticket_resolved** - Ticket marked as resolved
- **ticket_closed** - Ticket closed
- **note_created** - Internal note added

### Contact Events
- **contact_created** - New contact added
- **contact_updated** - Contact information changed

## Error Handling

### Common Errors

#### Authentication Errors
```json
{
  "success": false,
  "message": "Authentication failed: Invalid API key"
}
```

**Solution**: Verify your API key and domain configuration.

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

### Retry Logic

The integration includes automatic retry logic for:
- Network timeouts
- Rate limiting (429 errors)
- Temporary server errors (5xx)

## Best Practices

### 1. **API Key Security**
- Store API keys securely using environment variables
- Rotate API keys regularly
- Use dedicated API keys for automation

### 2. **Rate Limiting**
- Respect Freshdesk's rate limits (1000 requests/hour)
- Use bulk operations when possible
- Implement exponential backoff for retries

### 3. **Error Handling**
- Always check response status
- Implement proper error logging
- Use try-catch blocks for API calls

### 4. **Data Validation**
- Validate input data before API calls
- Check required fields
- Sanitize user input

### 5. **Performance Optimization**
- Use bulk operations for mass updates
- Cache frequently accessed data
- Minimize API calls with efficient queries

## Troubleshooting

### Connection Issues

1. **Verify Domain**: Ensure the domain is correct (e.g., `company.freshdesk.com`)
2. **Check API Key**: Verify the API key is valid and has required permissions
3. **Network Access**: Ensure your server can reach Freshdesk APIs
4. **SSL/TLS**: Verify SSL certificate validation

### Webhook Issues

1. **URL Accessibility**: Ensure webhook URL is publicly accessible
2. **SSL Certificate**: Use valid SSL certificate for HTTPS
3. **Signature Verification**: Check webhook secret configuration
4. **Response Time**: Ensure webhook endpoint responds within 10 seconds

### Permission Issues

1. **API Permissions**: Verify API key has required permissions
2. **Agent Permissions**: Check if the API user has access to required resources
3. **Group Access**: Ensure agent has access to target groups

## Advanced Configuration

### Custom Fields

Map custom fields in your integration configuration:

```json
{
  "config": {
    "custom_field_mapping": {
      "cf_category": "category",
      "cf_priority_level": "priority_level",
      "cf_customer_type": "customer_type"
    }
  }
}
```

### Automation Rules

Create automation rules based on Freshdesk events:

```json
{
  "trigger": {
    "platform": "freshdesk",
    "event": "ticket_created",
    "conditions": {
      "priority": 4,
      "type": "Incident"
    }
  },
  "actions": [
    {
      "platform": "slack",
      "action": "send_message",
      "parameters": {
        "channel": "#urgent-tickets",
        "message": "Urgent ticket created: {{ticket.subject}}"
      }
    }
  ]
}
```

## API Reference

### Base URL
```
https://your-domain.freshdesk.com/api/v2
```

### Authentication
```
Authorization: Basic base64(api_key:X)
```

### Rate Limits
- **1000 requests per hour** per API key
- **Rate limit headers** included in responses
- **Automatic retry** with exponential backoff

### Response Format
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    "ticket_id": 12345,
    "ticket_url": "https://company.freshdesk.com/a/tickets/12345"
  }
}
```

## Support

For additional help with Freshdesk integration:

1. **Documentation**: [Freshdesk API Documentation](https://developers.freshdesk.com/api/)
2. **Support**: Contact your system administrator
3. **Logs**: Check application logs for detailed error information
4. **Testing**: Use the integration test endpoint for troubleshooting

