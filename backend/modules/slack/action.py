"""
Slack integration actions
"""
import asyncio
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


async def execute_send_message(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send a message to a Slack channel
    """
    try:
        bot_token = credentials.get("bot_token")
        if not bot_token:
            raise ValueError("Slack bot token is required")
        
        # Get message configuration
        channel = action_config.get("channel") or integration_config.get("default_channel", "#general")
        message_template = action_config.get("message", "New event from {trigger_platform}")
        
        # Format message with trigger data
        message = format_message(message_template, trigger_data, action_config)
        
        # Prepare Slack API request
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "channel": channel,
            "text": message,
            "username": integration_config.get("bot_name", "SupportOps Bot"),
            "icon_emoji": action_config.get("icon_emoji", ":robot_face:")
        }
        
        # Add attachments if configured
        if action_config.get("use_rich_formatting", True):
            payload["attachments"] = create_rich_attachment(trigger_data, action_config)
        
        # Send message
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error', 'Unknown error')}")
            
            logger.info(f"Slack message sent successfully to {channel}")
            
            return {
                "status": "success",
                "message": "Message sent successfully",
                "channel": channel,
                "timestamp": result.get("ts"),
                "message_text": message
            }
            
    except Exception as e:
        logger.error(f"Slack send_message error: {e}")
        raise


async def execute_send_direct_message(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send a direct message to a Slack user
    """
    try:
        bot_token = credentials.get("bot_token")
        if not bot_token:
            raise ValueError("Slack bot token is required")
        
        # Get user configuration
        user_email = action_config.get("user_email")
        user_id = action_config.get("user_id")
        
        if not user_email and not user_id:
            raise ValueError("Either user_email or user_id is required")
        
        # Get user ID if email provided
        if user_email and not user_id:
            user_id = await get_user_id_by_email(bot_token, user_email)
        
        # Format message
        message_template = action_config.get("message", "New event from {trigger_platform}")
        message = format_message(message_template, trigger_data, action_config)
        
        # Send DM
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "channel": user_id,
            "text": message,
            "username": integration_config.get("bot_name", "SupportOps Bot")
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error', 'Unknown error')}")
            
            logger.info(f"Slack DM sent successfully to {user_id}")
            
            return {
                "status": "success",
                "message": "Direct message sent successfully",
                "user_id": user_id,
                "timestamp": result.get("ts")
            }
            
    except Exception as e:
        logger.error(f"Slack send_direct_message error: {e}")
        raise


async def execute_create_channel(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new Slack channel
    """
    try:
        bot_token = credentials.get("bot_token")
        if not bot_token:
            raise ValueError("Slack bot token is required")
        
        # Get channel configuration
        channel_name = action_config.get("channel_name")
        if not channel_name:
            # Generate channel name from trigger data
            channel_name = generate_channel_name(trigger_data, action_config)
        
        # Ensure channel name is valid (lowercase, no spaces, etc.)
        channel_name = sanitize_channel_name(channel_name)
        
        # Create channel
        url = "https://slack.com/api/conversations.create"
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": channel_name,
            "is_private": action_config.get("is_private", False)
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get("ok"):
                if result.get("error") == "name_taken":
                    # Channel already exists, return existing channel info
                    existing_channel = await get_channel_info(bot_token, channel_name)
                    return {
                        "status": "success",
                        "message": "Channel already exists",
                        "channel_id": existing_channel["id"],
                        "channel_name": channel_name,
                        "created": False
                    }
                else:
                    raise Exception(f"Slack API error: {result.get('error', 'Unknown error')}")
            
            channel = result.get("channel", {})
            
            logger.info(f"Slack channel created successfully: {channel_name}")
            
            return {
                "status": "success",
                "message": "Channel created successfully",
                "channel_id": channel.get("id"),
                "channel_name": channel_name,
                "created": True
            }
            
    except Exception as e:
        logger.error(f"Slack create_channel error: {e}")
        raise


async def execute_invite_to_channel(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Invite users to a Slack channel
    """
    try:
        bot_token = credentials.get("bot_token")
        if not bot_token:
            raise ValueError("Slack bot token is required")
        
        # Get configuration
        channel = action_config.get("channel")
        user_emails = action_config.get("user_emails", [])
        user_ids = action_config.get("user_ids", [])
        
        if not channel:
            raise ValueError("Channel is required")
        
        if not user_emails and not user_ids:
            raise ValueError("Either user_emails or user_ids is required")
        
        # Convert emails to user IDs if needed
        all_user_ids = user_ids.copy()
        for email in user_emails:
            user_id = await get_user_id_by_email(bot_token, email)
            if user_id:
                all_user_ids.append(user_id)
        
        if not all_user_ids:
            raise ValueError("No valid users found to invite")
        
        # Invite users
        url = "https://slack.com/api/conversations.invite"
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "channel": channel,
            "users": ",".join(all_user_ids)
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get("ok"):
                raise Exception(f"Slack API error: {result.get('error', 'Unknown error')}")
            
            logger.info(f"Users invited to Slack channel {channel}")
            
            return {
                "status": "success",
                "message": "Users invited successfully",
                "channel": channel,
                "invited_users": all_user_ids
            }
            
    except Exception as e:
        logger.error(f"Slack invite_to_channel error: {e}")
        raise


# Helper functions
def format_message(template: str, trigger_data: Dict[str, Any], action_config: Dict[str, Any]) -> str:
    """Format message template with trigger data"""
    try:
        # Basic template variables
        variables = {
            "trigger_platform": trigger_data.get("platform", "Unknown"),
            "trigger_event": trigger_data.get("event", "Unknown"),
            **trigger_data
        }
        
        # Custom variables from action config
        custom_vars = action_config.get("variables", {})
        variables.update(custom_vars)
        
        # Format template
        formatted_message = template.format(**variables)
        
        return formatted_message
        
    except KeyError as e:
        logger.warning(f"Template variable not found: {e}")
        return template
    except Exception as e:
        logger.error(f"Message formatting error: {e}")
        return template


def create_rich_attachment(trigger_data: Dict[str, Any], action_config: Dict[str, Any]) -> list:
    """Create rich Slack attachment"""
    try:
        attachment = {
            "color": action_config.get("color", "good"),
            "fields": []
        }
        
        # Add fields from trigger data
        important_fields = ["ticket_id", "priority", "status", "assignee", "subject", "description"]
        
        for field in important_fields:
            if field in trigger_data and trigger_data[field]:
                attachment["fields"].append({
                    "title": field.replace("_", " ").title(),
                    "value": str(trigger_data[field]),
                    "short": True
                })
        
        # Add timestamp
        if "timestamp" in trigger_data:
            attachment["ts"] = trigger_data["timestamp"]
        
        return [attachment]
        
    except Exception as e:
        logger.error(f"Rich attachment creation error: {e}")
        return []


async def get_user_id_by_email(bot_token: str, email: str) -> Optional[str]:
    """Get Slack user ID by email"""
    try:
        url = "https://slack.com/api/users.lookupByEmail"
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
        
        params = {"email": email}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                return result.get("user", {}).get("id")
            else:
                logger.warning(f"User not found for email: {email}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting user ID by email: {e}")
        return None


async def get_channel_info(bot_token: str, channel_name: str) -> Optional[Dict[str, Any]]:
    """Get channel information by name"""
    try:
        url = "https://slack.com/api/conversations.list"
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                channels = result.get("channels", [])
                for channel in channels:
                    if channel.get("name") == channel_name:
                        return channel
            
            return None
            
    except Exception as e:
        logger.error(f"Error getting channel info: {e}")
        return None


def generate_channel_name(trigger_data: Dict[str, Any], action_config: Dict[str, Any]) -> str:
    """Generate channel name from trigger data"""
    try:
        template = action_config.get("channel_name_template", "ticket-{ticket_id}")
        
        # Format with trigger data
        channel_name = template.format(**trigger_data)
        
        return channel_name
        
    except Exception as e:
        logger.error(f"Channel name generation error: {e}")
        return f"auto-channel-{trigger_data.get('id', 'unknown')}"


def sanitize_channel_name(name: str) -> str:
    """Sanitize channel name for Slack requirements"""
    import re
    
    # Convert to lowercase
    name = name.lower()
    
    # Replace spaces and special characters with hyphens
    name = re.sub(r'[^a-z0-9\-_]', '-', name)
    
    # Remove multiple consecutive hyphens
    name = re.sub(r'-+', '-', name)
    
    # Remove leading/trailing hyphens
    name = name.strip('-')
    
    # Ensure it's not too long (Slack limit is 21 characters)
    if len(name) > 21:
        name = name[:21].rstrip('-')
    
    return name

