"""
Integration connection test utilities
"""
import json
import logging
from typing import Dict, Any
from models.integration import Integration, IntegrationType

logger = logging.getLogger(__name__)

def test_integration_connection(integration: Integration, credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test integration connection
    """
    try:
        handler = get_integration_handler(integration.platform.value, credentials)
        result = handler.test_connection()
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Connection test completed"),
            "platform": integration.platform.value,
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Integration connection test failed for {integration.platform.value}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Connection test failed: {str(e)}",
            "platform": integration.platform.value
        }

def test_slack_connection(credentials: dict) -> dict:
    """Test Slack connection"""
    try:
        import requests
        bot_token = credentials.get("bot_token")
        if not bot_token:
            return {"success": False, "error": "Bot token is required"}
        
        url = "https://slack.com/api/auth.test"
        headers = {"Authorization": f"Bearer {bot_token}"}
        
        response = requests.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        
        result = response.json()
        if result.get("ok"):
            return {
                "success": True, 
                "message": "Slack connection successful", 
                "details": {
                    "team": result.get("team"), 
                    "user": result.get("user")
                }
            }
        else:
            return {"success": False, "error": result.get("error", "Unknown Slack API error")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_trello_connection(credentials: dict) -> dict:
    """Test Trello connection"""
    try:
        import requests
        api_key = credentials.get("api_key")
        api_token = credentials.get("api_token")
        
        if not api_key or not api_token:
            return {"success": False, "error": "API key and token are required"}
        
        url = "https://api.trello.com/1/members/me"
        params = {"key": api_key, "token": api_token}
        
        response = requests.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        
        result = response.json()
        return {
            "success": True, 
            "message": "Trello connection successful", 
            "details": {
                "username": result.get("username"), 
                "full_name": result.get("fullName")
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_notion_connection(credentials: dict) -> dict:
    """Test Notion connection"""
    try:
        import requests
        api_token = credentials.get("api_token")
        
        if not api_token:
            return {"success": False, "error": "API token is required"}
        
        url = "https://api.notion.com/v1/users/me"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Notion-Version": "2022-06-28"
        }
        
        response = requests.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "success": True,
            "message": "Notion connection successful",
            "details": {
                "name": result.get("name"),
                "user_id": result.get("id")
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_google_sheets_connection(credentials: dict) -> dict:
    """Test Google Sheets connection"""
    try:
        import requests
        
        access_token = credentials.get("access_token")
        if not access_token:
            return {"success": False, "error": "Access token is required"}
        
        url = "https://www.googleapis.com/oauth2/v1/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = requests.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "success": True,
            "message": "Google Sheets connection successful",
            "details": {
                "email": result.get("email"),
                "name": result.get("name")
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Import at the bottom to avoid circular imports
from .utils import get_integration_handler
