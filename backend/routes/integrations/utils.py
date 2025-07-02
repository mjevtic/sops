"""
Integration utilities and helper functions
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from models.integration import IntegrationType

logger = logging.getLogger(__name__)

def get_integration_handler(platform: str, credentials: Dict[str, Any]):
    """
    Get integration handler for platform
    """
    if platform == IntegrationType.SLACK.value:
        from integrations.slack import SlackIntegration
        return SlackIntegration(credentials)
    elif platform == IntegrationType.TRELLO.value:
        from integrations.trello import TrelloIntegration
        return TrelloIntegration(credentials)
    elif platform == IntegrationType.NOTION.value:
        from integrations.notion import NotionIntegration
        return NotionIntegration(credentials)
    elif platform == IntegrationType.GOOGLE_SHEETS.value:
        from integrations.google_sheets import GoogleSheetsIntegration
        return GoogleSheetsIntegration(credentials)
    elif platform == IntegrationType.FRESHDESK.value:
        from integrations.freshdesk import FreshdeskIntegration
        return FreshdeskIntegration(credentials)
    elif platform == IntegrationType.ZENDESK.value:
        from integrations.zendesk import ZendeskIntegration
        return ZendeskIntegration(credentials)
    elif platform == IntegrationType.JIRA.value:
        from integrations.jira import JiraIntegration
        return JiraIntegration(credentials)
    elif platform == IntegrationType.GITHUB.value:
        from integrations.github import GithubIntegration
        return GithubIntegration(credentials)
    else:
        raise ValueError(f"Unsupported platform: {platform}")

def get_supported_platforms():
    """
    Get list of supported integration platforms with their requirements
    """
    return {
        IntegrationType.SLACK.value: {
            "name": "Slack",
            "description": "Integrate with Slack for messaging and notifications",
            "icon": "slack",
            "credential_types": ["bot_token"],
            "credential_requirements": {
                "bot_token": {
                    "type": "string",
                    "format": "password",
                    "description": "Slack Bot Token (xoxb-...)",
                    "required": True
                }
            },
            "actions": ["send_message", "create_channel", "list_channels"],
            "documentation_url": "https://api.slack.com/docs"
        },
        IntegrationType.TRELLO.value: {
            "name": "Trello",
            "description": "Integrate with Trello for task management",
            "icon": "trello",
            "credential_types": ["api_key", "api_token"],
            "credential_requirements": {
                "api_key": {
                    "type": "string",
                    "description": "Trello API Key",
                    "required": True
                },
                "api_token": {
                    "type": "string",
                    "format": "password",
                    "description": "Trello API Token",
                    "required": True
                }
            },
            "actions": ["create_card", "list_boards", "list_lists", "add_comment"],
            "documentation_url": "https://developer.atlassian.com/cloud/trello/rest/"
        },
        IntegrationType.NOTION.value: {
            "name": "Notion",
            "description": "Integrate with Notion for documentation and knowledge base",
            "icon": "notion",
            "credential_types": ["api_token"],
            "credential_requirements": {
                "api_token": {
                    "type": "string",
                    "format": "password",
                    "description": "Notion Integration Token",
                    "required": True
                }
            },
            "actions": ["create_page", "search_pages", "append_block"],
            "documentation_url": "https://developers.notion.com/"
        },
        IntegrationType.GOOGLE_SHEETS.value: {
            "name": "Google Sheets",
            "description": "Integrate with Google Sheets for data management",
            "icon": "google",
            "credential_types": ["access_token", "refresh_token", "client_id", "client_secret"],
            "credential_requirements": {
                "access_token": {
                    "type": "string",
                    "format": "password",
                    "description": "Google OAuth Access Token",
                    "required": True
                },
                "refresh_token": {
                    "type": "string",
                    "format": "password",
                    "description": "Google OAuth Refresh Token",
                    "required": False
                },
                "client_id": {
                    "type": "string",
                    "description": "Google OAuth Client ID",
                    "required": False
                },
                "client_secret": {
                    "type": "string",
                    "format": "password",
                    "description": "Google OAuth Client Secret",
                    "required": False
                }
            },
            "actions": ["read_sheet", "append_row", "create_sheet"],
            "documentation_url": "https://developers.google.com/sheets/api"
        },
        IntegrationType.FRESHDESK.value: {
            "name": "Freshdesk",
            "description": "Integrate with Freshdesk for customer support",
            "icon": "freshdesk",
            "credential_types": ["api_key", "domain"],
            "credential_requirements": {
                "api_key": {
                    "type": "string",
                    "format": "password",
                    "description": "Freshdesk API Key",
                    "required": True
                },
                "domain": {
                    "type": "string",
                    "description": "Freshdesk Domain (example.freshdesk.com)",
                    "required": True
                }
            },
            "actions": ["create_ticket", "get_ticket", "list_tickets", "update_ticket"],
            "documentation_url": "https://developers.freshdesk.com/api/"
        },
        IntegrationType.ZENDESK.value: {
            "name": "Zendesk",
            "description": "Integrate with Zendesk for customer support",
            "icon": "zendesk",
            "credential_types": ["api_token", "email", "subdomain"],
            "credential_requirements": {
                "api_token": {
                    "type": "string",
                    "format": "password",
                    "description": "Zendesk API Token",
                    "required": True
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Zendesk Email",
                    "required": True
                },
                "subdomain": {
                    "type": "string",
                    "description": "Zendesk Subdomain (example.zendesk.com)",
                    "required": True
                }
            },
            "actions": ["create_ticket", "get_ticket", "list_tickets", "update_ticket"],
            "documentation_url": "https://developer.zendesk.com/api-reference/"
        }
    }

def get_platform_actions(platform: str) -> Dict[str, Any]:
    """
    Get available actions for a specific platform
    """
    platforms = get_supported_platforms()
    
    if platform not in platforms:
        return {
            "platform": platform,
            "actions": [],
            "error": "Platform not supported"
        }
    
    platform_info = platforms[platform]
    
    return {
        "platform": platform,
        "name": platform_info["name"],
        "actions": platform_info["actions"],
        "documentation_url": platform_info.get("documentation_url", "")
    }

def get_platform_info(platform: IntegrationType) -> dict:
    """Get platform information"""
    platform_configs = {
        IntegrationType.SLACK: {
            "name": "Slack",
            "icon": "slack",
            "color": "#4A154B",
            "credential_type": "bot_token"
        },
        IntegrationType.TRELLO: {
            "name": "Trello",
            "icon": "trello",
            "color": "#0079BF",
            "credential_type": "api_key_token"
        },
        IntegrationType.NOTION: {
            "name": "Notion",
            "icon": "notion",
            "color": "#000000",
            "credential_type": "api_token"
        },
        IntegrationType.GOOGLE_SHEETS: {
            "name": "Google Sheets",
            "icon": "google",
            "color": "#0F9D58",
            "credential_type": "oauth"
        },
        IntegrationType.FRESHDESK: {
            "name": "Freshdesk",
            "icon": "freshdesk",
            "color": "#72A8C9",
            "credential_type": "api_key"
        },
        IntegrationType.ZENDESK: {
            "name": "Zendesk",
            "icon": "zendesk",
            "color": "#03363D",
            "credential_type": "api_token"
        },
        IntegrationType.JIRA: {
            "name": "Jira",
            "icon": "jira",
            "color": "#0052CC",
            "credential_type": "api_token"
        },
        IntegrationType.GITHUB: {
            "name": "GitHub",
            "icon": "github",
            "color": "#24292E",
            "credential_type": "oauth"
        }
    }
    
    return platform_configs.get(platform, {
        "name": platform.value,
        "icon": "integration",
        "color": "#666666",
        "credential_type": "unknown"
    })

def determine_credential_type(platform: str, credentials: Dict[str, Any]) -> str:
    """
    Determine credential type based on platform and credentials
    """
    if platform == IntegrationType.SLACK.value:
        return "bot_token"
    elif platform == IntegrationType.TRELLO.value:
        return "api_key_token"
    elif platform == IntegrationType.NOTION.value:
        return "api_token"
    elif platform == IntegrationType.GOOGLE_SHEETS.value:
        return "oauth"
    elif platform == IntegrationType.FRESHDESK.value:
        return "api_key"
    elif platform == IntegrationType.ZENDESK.value:
        return "api_token"
    elif platform == IntegrationType.JIRA.value:
        return "api_token"
    elif platform == IntegrationType.GITHUB.value:
        return "oauth"
    else:
        return "unknown"
