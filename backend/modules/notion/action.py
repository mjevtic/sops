"""
Notion integration actions
"""
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def execute_create_page(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new Notion page
    """
    try:
        api_token = credentials.get("api_token")
        if not api_token:
            raise ValueError("Notion API token is required")
        
        # Get page configuration
        parent_id = action_config.get("parent_id") or integration_config.get("database_id")
        if not parent_id:
            raise ValueError("Parent page or database ID is required")
        
        # Format page title and content
        page_title = format_text(action_config.get("title", "New Page from {trigger_platform}"), trigger_data)
        
        # Prepare Notion API request
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Build page payload
        payload = {
            "parent": {"page_id": parent_id} if not action_config.get("is_database") else {"database_id": parent_id},
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": page_title
                            }
                        }
                    ]
                }
            }
        }
        
        # Add database properties if creating in database
        if action_config.get("is_database", True):
            payload["properties"] = build_database_properties(action_config, trigger_data)
        
        # Add page content
        if action_config.get("content"):
            payload["children"] = build_page_content(action_config["content"], trigger_data)
        
        # Create page
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Notion page created successfully: {result.get('id')}")
            
            return {
                "status": "success",
                "message": "Page created successfully",
                "page_id": result.get("id"),
                "page_url": result.get("url"),
                "page_title": page_title
            }
            
    except Exception as e:
        logger.error(f"Notion create_page error: {e}")
        raise


async def execute_update_page(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update an existing Notion page
    """
    try:
        api_token = credentials.get("api_token")
        if not api_token:
            raise ValueError("Notion API token is required")
        
        # Get page ID
        page_id = action_config.get("page_id")
        if not page_id:
            # Try to find page by criteria
            page_id = await find_page_by_criteria(api_token, action_config, trigger_data, integration_config)
        
        if not page_id:
            raise ValueError("Page ID is required or page not found")
        
        # Prepare update payload
        url = f"https://api.notion.com/v1/pages/{page_id}"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        payload = {
            "properties": {}
        }
        
        # Update properties
        if action_config.get("properties"):
            payload["properties"] = build_database_properties(action_config, trigger_data)
        
        # Update page
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Notion page updated successfully: {page_id}")
            
            return {
                "status": "success",
                "message": "Page updated successfully",
                "page_id": page_id,
                "page_url": result.get("url")
            }
            
    except Exception as e:
        logger.error(f"Notion update_page error: {e}")
        raise


async def execute_add_comment(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add a comment to a Notion page
    """
    try:
        api_token = credentials.get("api_token")
        if not api_token:
            raise ValueError("Notion API token is required")
        
        # Get page ID
        page_id = action_config.get("page_id")
        if not page_id:
            # Try to find page by criteria
            page_id = await find_page_by_criteria(api_token, action_config, trigger_data, integration_config)
        
        if not page_id:
            raise ValueError("Page ID is required or page not found")
        
        # Format comment
        comment_text = format_text(action_config.get("comment", "Update from {trigger_platform}"), trigger_data)
        
        # Add comment
        url = f"https://api.notion.com/v1/comments"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        payload = {
            "parent": {"page_id": page_id},
            "rich_text": [
                {
                    "text": {
                        "content": comment_text
                    }
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Notion comment added successfully to page: {page_id}")
            
            return {
                "status": "success",
                "message": "Comment added successfully",
                "page_id": page_id,
                "comment_id": result.get("id"),
                "comment_text": comment_text
            }
            
    except Exception as e:
        logger.error(f"Notion add_comment error: {e}")
        raise


async def execute_create_database_entry(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new entry in a Notion database
    """
    try:
        api_token = credentials.get("api_token")
        if not api_token:
            raise ValueError("Notion API token is required")
        
        # Get database ID
        database_id = action_config.get("database_id") or integration_config.get("database_id")
        if not database_id:
            raise ValueError("Database ID is required")
        
        # Prepare database entry
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        payload = {
            "parent": {"database_id": database_id},
            "properties": build_database_properties(action_config, trigger_data)
        }
        
        # Add content if specified
        if action_config.get("content"):
            payload["children"] = build_page_content(action_config["content"], trigger_data)
        
        # Create database entry
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Notion database entry created successfully: {result.get('id')}")
            
            return {
                "status": "success",
                "message": "Database entry created successfully",
                "page_id": result.get("id"),
                "page_url": result.get("url"),
                "database_id": database_id
            }
            
    except Exception as e:
        logger.error(f"Notion create_database_entry error: {e}")
        raise


async def execute_query_database(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Query a Notion database
    """
    try:
        api_token = credentials.get("api_token")
        if not api_token:
            raise ValueError("Notion API token is required")
        
        # Get database ID
        database_id = action_config.get("database_id") or integration_config.get("database_id")
        if not database_id:
            raise ValueError("Database ID is required")
        
        # Build query
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        payload = {}
        
        # Add filter if specified
        if action_config.get("filter"):
            payload["filter"] = build_database_filter(action_config["filter"], trigger_data)
        
        # Add sorts if specified
        if action_config.get("sorts"):
            payload["sorts"] = action_config["sorts"]
        
        # Add page size
        if action_config.get("page_size"):
            payload["page_size"] = min(action_config["page_size"], 100)
        
        # Query database
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Notion database queried successfully: {len(result.get('results', []))} results")
            
            return {
                "status": "success",
                "message": "Database queried successfully",
                "database_id": database_id,
                "results_count": len(result.get("results", [])),
                "results": result.get("results", []),
                "has_more": result.get("has_more", False)
            }
            
    except Exception as e:
        logger.error(f"Notion query_database error: {e}")
        raise


# Helper functions
def format_text(template: str, trigger_data: Dict[str, Any]) -> str:
    """Format text template with trigger data"""
    try:
        # Basic template variables
        variables = {
            "trigger_platform": trigger_data.get("platform", "Unknown"),
            "trigger_event": trigger_data.get("event", "Unknown"),
            **trigger_data
        }
        
        # Format template
        formatted_text = template.format(**variables)
        
        return formatted_text
        
    except KeyError as e:
        logger.warning(f"Template variable not found: {e}")
        return template
    except Exception as e:
        logger.error(f"Text formatting error: {e}")
        return template


def build_database_properties(action_config: Dict[str, Any], trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build Notion database properties from configuration"""
    try:
        properties = {}
        
        # Get property mappings from action config
        property_mappings = action_config.get("properties", {})
        
        for prop_name, prop_config in property_mappings.items():
            prop_type = prop_config.get("type", "rich_text")
            prop_value = prop_config.get("value", "")
            
            # Format value with trigger data
            if isinstance(prop_value, str):
                formatted_value = format_text(prop_value, trigger_data)
            else:
                formatted_value = prop_value
            
            # Build property based on type
            if prop_type == "title":
                properties[prop_name] = {
                    "title": [
                        {
                            "text": {
                                "content": formatted_value
                            }
                        }
                    ]
                }
            elif prop_type == "rich_text":
                properties[prop_name] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": formatted_value
                            }
                        }
                    ]
                }
            elif prop_type == "number":
                try:
                    properties[prop_name] = {
                        "number": float(formatted_value) if formatted_value else None
                    }
                except (ValueError, TypeError):
                    properties[prop_name] = {"number": None}
            elif prop_type == "select":
                properties[prop_name] = {
                    "select": {
                        "name": formatted_value
                    }
                }
            elif prop_type == "multi_select":
                if isinstance(formatted_value, list):
                    options = [{"name": str(item)} for item in formatted_value]
                else:
                    options = [{"name": str(formatted_value)}]
                properties[prop_name] = {
                    "multi_select": options
                }
            elif prop_type == "date":
                properties[prop_name] = {
                    "date": {
                        "start": formatted_value if formatted_value else datetime.utcnow().isoformat()
                    }
                }
            elif prop_type == "checkbox":
                properties[prop_name] = {
                    "checkbox": bool(formatted_value)
                }
            elif prop_type == "url":
                properties[prop_name] = {
                    "url": formatted_value if formatted_value else None
                }
            elif prop_type == "email":
                properties[prop_name] = {
                    "email": formatted_value if formatted_value else None
                }
            elif prop_type == "phone_number":
                properties[prop_name] = {
                    "phone_number": formatted_value if formatted_value else None
                }
        
        return properties
        
    except Exception as e:
        logger.error(f"Error building database properties: {e}")
        return {}


def build_page_content(content_config: List[Dict[str, Any]], trigger_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build Notion page content blocks"""
    try:
        blocks = []
        
        for block_config in content_config:
            block_type = block_config.get("type", "paragraph")
            block_text = format_text(block_config.get("text", ""), trigger_data)
            
            if block_type == "paragraph":
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": block_text
                                }
                            }
                        ]
                    }
                })
            elif block_type == "heading_1":
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": block_text
                                }
                            }
                        ]
                    }
                })
            elif block_type == "heading_2":
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": block_text
                                }
                            }
                        ]
                    }
                })
            elif block_type == "bulleted_list_item":
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": block_text
                                }
                            }
                        ]
                    }
                })
            elif block_type == "numbered_list_item":
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": block_text
                                }
                            }
                        ]
                    }
                })
            elif block_type == "code":
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": block_text
                                }
                            }
                        ],
                        "language": block_config.get("language", "plain text")
                    }
                })
        
        return blocks
        
    except Exception as e:
        logger.error(f"Error building page content: {e}")
        return []


def build_database_filter(filter_config: Dict[str, Any], trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build Notion database filter"""
    try:
        # Format filter values with trigger data
        formatted_filter = {}
        
        for key, value in filter_config.items():
            if isinstance(value, str):
                formatted_filter[key] = format_text(value, trigger_data)
            elif isinstance(value, dict):
                formatted_filter[key] = build_database_filter(value, trigger_data)
            else:
                formatted_filter[key] = value
        
        return formatted_filter
        
    except Exception as e:
        logger.error(f"Error building database filter: {e}")
        return filter_config


async def find_page_by_criteria(
    api_token: str,
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Optional[str]:
    """Find page by various criteria"""
    try:
        # Search by title pattern
        if action_config.get("page_title_pattern"):
            page_title = format_text(action_config["page_title_pattern"], trigger_data)
            return await find_page_by_title(api_token, page_title, integration_config.get("database_id"))
        
        # Search by property value
        if action_config.get("property_search"):
            return await find_page_by_property(api_token, action_config["property_search"], trigger_data, integration_config.get("database_id"))
        
        return None
        
    except Exception as e:
        logger.error(f"Error finding page by criteria: {e}")
        return None


async def find_page_by_title(api_token: str, page_title: str, database_id: Optional[str] = None) -> Optional[str]:
    """Find page by title"""
    try:
        if not database_id:
            return None
        
        # Query database for page with matching title
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        payload = {
            "filter": {
                "property": "title",
                "title": {
                    "equals": page_title
                }
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            results = result.get("results", [])
            
            if results:
                return results[0].get("id")
            
            return None
            
    except Exception as e:
        logger.error(f"Error finding page by title: {e}")
        return None


async def find_page_by_property(
    api_token: str,
    property_search: Dict[str, Any],
    trigger_data: Dict[str, Any],
    database_id: Optional[str] = None
) -> Optional[str]:
    """Find page by property value"""
    try:
        if not database_id:
            return None
        
        # Build filter from property search config
        filter_config = build_database_filter(property_search, trigger_data)
        
        # Query database
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        payload = {
            "filter": filter_config
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            results = result.get("results", [])
            
            if results:
                return results[0].get("id")
            
            return None
            
    except Exception as e:
        logger.error(f"Error finding page by property: {e}")
        return None

