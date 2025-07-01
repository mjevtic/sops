"""
Trello integration actions
"""
import asyncio
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


async def execute_create_card(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new Trello card
    """
    try:
        api_key = credentials.get("api_key")
        api_token = credentials.get("api_token")
        
        if not api_key or not api_token:
            raise ValueError("Trello API key and token are required")
        
        # Get card configuration
        list_id = action_config.get("list_id") or integration_config.get("default_list_id")
        if not list_id:
            raise ValueError("Trello list ID is required")
        
        # Format card details
        card_name = format_text(action_config.get("name", "New Card from {trigger_platform}"), trigger_data)
        card_desc = format_text(action_config.get("description", ""), trigger_data)
        
        # Prepare Trello API request
        url = "https://api.trello.com/1/cards"
        
        params = {
            "key": api_key,
            "token": api_token,
            "idList": list_id,
            "name": card_name,
            "desc": card_desc
        }
        
        # Add optional parameters
        if action_config.get("due_date"):
            params["due"] = action_config["due_date"]
        
        if action_config.get("position"):
            params["pos"] = action_config["position"]
        
        # Add labels if specified
        if action_config.get("label_ids"):
            params["idLabels"] = ",".join(action_config["label_ids"])
        
        # Add members if specified
        if action_config.get("member_ids"):
            params["idMembers"] = ",".join(action_config["member_ids"])
        
        # Create card
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Trello card created successfully: {result.get('id')}")
            
            # Add custom fields if configured
            if action_config.get("custom_fields"):
                await add_custom_fields(api_key, api_token, result["id"], action_config["custom_fields"], trigger_data)
            
            # Add checklist if configured
            if action_config.get("checklist_items"):
                await add_checklist(api_key, api_token, result["id"], action_config["checklist_items"], trigger_data)
            
            return {
                "status": "success",
                "message": "Card created successfully",
                "card_id": result.get("id"),
                "card_url": result.get("url"),
                "card_name": card_name,
                "list_id": list_id
            }
            
    except Exception as e:
        logger.error(f"Trello create_card error: {e}")
        raise


async def execute_move_card(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Move a Trello card to a different list
    """
    try:
        api_key = credentials.get("api_key")
        api_token = credentials.get("api_token")
        
        if not api_key or not api_token:
            raise ValueError("Trello API key and token are required")
        
        # Get card and list configuration
        card_id = action_config.get("card_id")
        target_list_id = action_config.get("target_list_id")
        
        if not card_id:
            # Try to find card by name or custom field
            card_id = await find_card_by_criteria(api_key, api_token, action_config, trigger_data)
        
        if not card_id:
            raise ValueError("Card ID is required or card not found")
        
        if not target_list_id:
            raise ValueError("Target list ID is required")
        
        # Move card
        url = f"https://api.trello.com/1/cards/{card_id}"
        
        params = {
            "key": api_key,
            "token": api_token,
            "idList": target_list_id
        }
        
        # Add optional position
        if action_config.get("position"):
            params["pos"] = action_config["position"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Trello card moved successfully: {card_id}")
            
            return {
                "status": "success",
                "message": "Card moved successfully",
                "card_id": card_id,
                "target_list_id": target_list_id,
                "card_url": result.get("url")
            }
            
    except Exception as e:
        logger.error(f"Trello move_card error: {e}")
        raise


async def execute_add_comment(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add a comment to a Trello card
    """
    try:
        api_key = credentials.get("api_key")
        api_token = credentials.get("api_token")
        
        if not api_key or not api_token:
            raise ValueError("Trello API key and token are required")
        
        # Get card configuration
        card_id = action_config.get("card_id")
        
        if not card_id:
            # Try to find card by criteria
            card_id = await find_card_by_criteria(api_key, api_token, action_config, trigger_data)
        
        if not card_id:
            raise ValueError("Card ID is required or card not found")
        
        # Format comment
        comment_text = format_text(action_config.get("comment", "Update from {trigger_platform}"), trigger_data)
        
        # Add comment
        url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
        
        params = {
            "key": api_key,
            "token": api_token,
            "text": comment_text
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Trello comment added successfully to card: {card_id}")
            
            return {
                "status": "success",
                "message": "Comment added successfully",
                "card_id": card_id,
                "comment_id": result.get("id"),
                "comment_text": comment_text
            }
            
    except Exception as e:
        logger.error(f"Trello add_comment error: {e}")
        raise


async def execute_create_checklist(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a checklist on a Trello card
    """
    try:
        api_key = credentials.get("api_key")
        api_token = credentials.get("api_token")
        
        if not api_key or not api_token:
            raise ValueError("Trello API key and token are required")
        
        # Get card configuration
        card_id = action_config.get("card_id")
        
        if not card_id:
            # Try to find card by criteria
            card_id = await find_card_by_criteria(api_key, api_token, action_config, trigger_data)
        
        if not card_id:
            raise ValueError("Card ID is required or card not found")
        
        # Get checklist configuration
        checklist_name = format_text(action_config.get("checklist_name", "Checklist"), trigger_data)
        checklist_items = action_config.get("checklist_items", [])
        
        # Create checklist
        url = f"https://api.trello.com/1/cards/{card_id}/checklists"
        
        params = {
            "key": api_key,
            "token": api_token,
            "name": checklist_name
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params)
            response.raise_for_status()
            
            checklist_result = response.json()
            checklist_id = checklist_result.get("id")
            
            # Add checklist items
            added_items = []
            for item in checklist_items:
                item_text = format_text(item, trigger_data)
                item_result = await add_checklist_item(api_key, api_token, checklist_id, item_text)
                if item_result:
                    added_items.append(item_result)
            
            logger.info(f"Trello checklist created successfully on card: {card_id}")
            
            return {
                "status": "success",
                "message": "Checklist created successfully",
                "card_id": card_id,
                "checklist_id": checklist_id,
                "checklist_name": checklist_name,
                "items_added": len(added_items)
            }
            
    except Exception as e:
        logger.error(f"Trello create_checklist error: {e}")
        raise


async def execute_add_label(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add a label to a Trello card
    """
    try:
        api_key = credentials.get("api_key")
        api_token = credentials.get("api_token")
        
        if not api_key or not api_token:
            raise ValueError("Trello API key and token are required")
        
        # Get card configuration
        card_id = action_config.get("card_id")
        
        if not card_id:
            # Try to find card by criteria
            card_id = await find_card_by_criteria(api_key, api_token, action_config, trigger_data)
        
        if not card_id:
            raise ValueError("Card ID is required or card not found")
        
        # Get label configuration
        label_id = action_config.get("label_id")
        label_color = action_config.get("label_color")
        label_name = action_config.get("label_name")
        
        if not label_id and (label_color or label_name):
            # Find or create label
            label_id = await find_or_create_label(api_key, api_token, integration_config.get("board_id"), label_name, label_color)
        
        if not label_id:
            raise ValueError("Label ID is required or label could not be created")
        
        # Add label to card
        url = f"https://api.trello.com/1/cards/{card_id}/idLabels"
        
        params = {
            "key": api_key,
            "token": api_token,
            "value": label_id
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params)
            response.raise_for_status()
            
            logger.info(f"Trello label added successfully to card: {card_id}")
            
            return {
                "status": "success",
                "message": "Label added successfully",
                "card_id": card_id,
                "label_id": label_id
            }
            
    except Exception as e:
        logger.error(f"Trello add_label error: {e}")
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


async def find_card_by_criteria(
    api_key: str,
    api_token: str,
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any]
) -> Optional[str]:
    """Find card by various criteria"""
    try:
        # Search by card name pattern
        if action_config.get("card_name_pattern"):
            card_name = format_text(action_config["card_name_pattern"], trigger_data)
            return await find_card_by_name(api_key, api_token, card_name, action_config.get("board_id"))
        
        # Search by custom field value
        if action_config.get("custom_field_search"):
            field_config = action_config["custom_field_search"]
            return await find_card_by_custom_field(api_key, api_token, field_config, trigger_data)
        
        return None
        
    except Exception as e:
        logger.error(f"Error finding card by criteria: {e}")
        return None


async def find_card_by_name(api_key: str, api_token: str, card_name: str, board_id: Optional[str] = None) -> Optional[str]:
    """Find card by name"""
    try:
        # Search for cards
        url = "https://api.trello.com/1/search"
        
        params = {
            "key": api_key,
            "token": api_token,
            "query": card_name,
            "modelTypes": "cards",
            "card_fields": "id,name"
        }
        
        if board_id:
            params["idBoards"] = board_id
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            cards = result.get("cards", [])
            
            # Find exact match
            for card in cards:
                if card.get("name") == card_name:
                    return card.get("id")
            
            # Return first partial match if no exact match
            if cards:
                return cards[0].get("id")
            
            return None
            
    except Exception as e:
        logger.error(f"Error finding card by name: {e}")
        return None


async def add_custom_fields(api_key: str, api_token: str, card_id: str, custom_fields: Dict[str, Any], trigger_data: Dict[str, Any]):
    """Add custom fields to a card"""
    try:
        for field_name, field_value in custom_fields.items():
            # Format field value
            formatted_value = format_text(str(field_value), trigger_data)
            
            # Note: Custom fields in Trello require the field ID, which would need to be configured
            # This is a simplified implementation
            logger.info(f"Custom field {field_name} would be set to {formatted_value} on card {card_id}")
            
    except Exception as e:
        logger.error(f"Error adding custom fields: {e}")


async def add_checklist(api_key: str, api_token: str, card_id: str, checklist_items: list, trigger_data: Dict[str, Any]):
    """Add checklist to a card"""
    try:
        # Create checklist first
        checklist_url = f"https://api.trello.com/1/cards/{card_id}/checklists"
        
        params = {
            "key": api_key,
            "token": api_token,
            "name": "Auto-generated Checklist"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(checklist_url, params=params)
            response.raise_for_status()
            
            checklist_result = response.json()
            checklist_id = checklist_result.get("id")
            
            # Add items
            for item in checklist_items:
                item_text = format_text(item, trigger_data)
                await add_checklist_item(api_key, api_token, checklist_id, item_text)
            
    except Exception as e:
        logger.error(f"Error adding checklist: {e}")


async def add_checklist_item(api_key: str, api_token: str, checklist_id: str, item_text: str) -> Optional[Dict[str, Any]]:
    """Add item to checklist"""
    try:
        url = f"https://api.trello.com/1/checklists/{checklist_id}/checkItems"
        
        params = {
            "key": api_key,
            "token": api_token,
            "name": item_text
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
    except Exception as e:
        logger.error(f"Error adding checklist item: {e}")
        return None


async def find_or_create_label(api_key: str, api_token: str, board_id: str, label_name: Optional[str], label_color: Optional[str]) -> Optional[str]:
    """Find existing label or create new one"""
    try:
        if not board_id:
            return None
        
        # Get existing labels
        url = f"https://api.trello.com/1/boards/{board_id}/labels"
        
        params = {
            "key": api_key,
            "token": api_token
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            labels = response.json()
            
            # Find existing label
            for label in labels:
                if label_name and label.get("name") == label_name:
                    return label.get("id")
                if label_color and label.get("color") == label_color and not label.get("name"):
                    return label.get("id")
            
            # Create new label if not found
            if label_name or label_color:
                create_url = f"https://api.trello.com/1/boards/{board_id}/labels"
                create_params = {
                    "key": api_key,
                    "token": api_token
                }
                
                if label_name:
                    create_params["name"] = label_name
                if label_color:
                    create_params["color"] = label_color
                
                create_response = await client.post(create_url, params=create_params)
                create_response.raise_for_status()
                
                new_label = create_response.json()
                return new_label.get("id")
            
            return None
            
    except Exception as e:
        logger.error(f"Error finding or creating label: {e}")
        return None

