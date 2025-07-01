"""
Google Sheets integration actions
"""
import asyncio
import httpx
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


async def execute_append_row(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Append a new row to a Google Sheets spreadsheet
    """
    try:
        access_token = credentials.get("access_token")
        if not access_token:
            raise ValueError("Google Sheets access token is required")
        
        # Get spreadsheet configuration
        spreadsheet_id = action_config.get("spreadsheet_id") or integration_config.get("spreadsheet_id")
        sheet_name = action_config.get("sheet_name") or integration_config.get("default_sheet_name", "Sheet1")
        
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required")
        
        # Build row data
        row_data = build_row_data(action_config, trigger_data)
        
        # Prepare Google Sheets API request
        range_name = f"{sheet_name}!A:Z"  # Auto-detect range
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}:append"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "values": [row_data],
            "majorDimension": "ROWS"
        }
        
        params = {
            "valueInputOption": "USER_ENTERED",
            "insertDataOption": "INSERT_ROWS"
        }
        
        # Append row
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Google Sheets row appended successfully to {spreadsheet_id}")
            
            return {
                "status": "success",
                "message": "Row appended successfully",
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name,
                "updated_range": result.get("updates", {}).get("updatedRange"),
                "updated_rows": result.get("updates", {}).get("updatedRows", 0),
                "row_data": row_data
            }
            
    except Exception as e:
        logger.error(f"Google Sheets append_row error: {e}")
        raise


async def execute_update_row(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update an existing row in a Google Sheets spreadsheet
    """
    try:
        access_token = credentials.get("access_token")
        if not access_token:
            raise ValueError("Google Sheets access token is required")
        
        # Get spreadsheet configuration
        spreadsheet_id = action_config.get("spreadsheet_id") or integration_config.get("spreadsheet_id")
        sheet_name = action_config.get("sheet_name") or integration_config.get("default_sheet_name", "Sheet1")
        
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required")
        
        # Find row to update
        row_number = action_config.get("row_number")
        if not row_number:
            # Try to find row by criteria
            row_number = await find_row_by_criteria(access_token, spreadsheet_id, sheet_name, action_config, trigger_data)
        
        if not row_number:
            raise ValueError("Row number is required or row not found")
        
        # Build row data
        row_data = build_row_data(action_config, trigger_data)
        
        # Update row
        range_name = f"{sheet_name}!A{row_number}:Z{row_number}"
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "values": [row_data],
            "majorDimension": "ROWS"
        }
        
        params = {
            "valueInputOption": "USER_ENTERED"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(url, headers=headers, json=payload, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Google Sheets row updated successfully in {spreadsheet_id}")
            
            return {
                "status": "success",
                "message": "Row updated successfully",
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name,
                "row_number": row_number,
                "updated_range": result.get("updatedRange"),
                "updated_cells": result.get("updatedCells", 0),
                "row_data": row_data
            }
            
    except Exception as e:
        logger.error(f"Google Sheets update_row error: {e}")
        raise


async def execute_create_sheet(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new sheet in a Google Sheets spreadsheet
    """
    try:
        access_token = credentials.get("access_token")
        if not access_token:
            raise ValueError("Google Sheets access token is required")
        
        # Get spreadsheet configuration
        spreadsheet_id = action_config.get("spreadsheet_id") or integration_config.get("spreadsheet_id")
        
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required")
        
        # Format sheet name
        sheet_name = format_text(action_config.get("sheet_name", "New Sheet"), trigger_data)
        
        # Create sheet
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                            "gridProperties": {
                                "rowCount": action_config.get("row_count", 1000),
                                "columnCount": action_config.get("column_count", 26)
                            }
                        }
                    }
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Get the new sheet ID
            sheet_id = result.get("replies", [{}])[0].get("addSheet", {}).get("properties", {}).get("sheetId")
            
            logger.info(f"Google Sheets sheet created successfully: {sheet_name}")
            
            # Add headers if specified
            if action_config.get("headers"):
                await add_headers(access_token, spreadsheet_id, sheet_name, action_config["headers"])
            
            return {
                "status": "success",
                "message": "Sheet created successfully",
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name,
                "sheet_id": sheet_id
            }
            
    except Exception as e:
        logger.error(f"Google Sheets create_sheet error: {e}")
        raise


async def execute_clear_range(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Clear a range of cells in a Google Sheets spreadsheet
    """
    try:
        access_token = credentials.get("access_token")
        if not access_token:
            raise ValueError("Google Sheets access token is required")
        
        # Get spreadsheet configuration
        spreadsheet_id = action_config.get("spreadsheet_id") or integration_config.get("spreadsheet_id")
        sheet_name = action_config.get("sheet_name") or integration_config.get("default_sheet_name", "Sheet1")
        
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required")
        
        # Get range to clear
        range_to_clear = action_config.get("range", "A:Z")
        range_name = f"{sheet_name}!{range_to_clear}"
        
        # Clear range
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}:clear"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Google Sheets range cleared successfully: {range_name}")
            
            return {
                "status": "success",
                "message": "Range cleared successfully",
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name,
                "cleared_range": result.get("clearedRange")
            }
            
    except Exception as e:
        logger.error(f"Google Sheets clear_range error: {e}")
        raise


async def execute_batch_update(
    credentials: Dict[str, Any],
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any],
    integration_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform batch updates on a Google Sheets spreadsheet
    """
    try:
        access_token = credentials.get("access_token")
        if not access_token:
            raise ValueError("Google Sheets access token is required")
        
        # Get spreadsheet configuration
        spreadsheet_id = action_config.get("spreadsheet_id") or integration_config.get("spreadsheet_id")
        
        if not spreadsheet_id:
            raise ValueError("Spreadsheet ID is required")
        
        # Build batch update requests
        requests = []
        
        # Process different types of updates
        if action_config.get("format_updates"):
            requests.extend(build_format_requests(action_config["format_updates"], trigger_data))
        
        if action_config.get("value_updates"):
            value_requests = build_value_requests(action_config["value_updates"], trigger_data)
            
        if not requests and not action_config.get("value_updates"):
            raise ValueError("No update requests specified")
        
        # Perform batch update for formatting/structure changes
        if requests:
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {"requests": requests}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        
        # Perform batch update for values
        if action_config.get("value_updates"):
            await batch_update_values(access_token, spreadsheet_id, action_config["value_updates"], trigger_data)
        
        logger.info(f"Google Sheets batch update completed successfully")
        
        return {
            "status": "success",
            "message": "Batch update completed successfully",
            "spreadsheet_id": spreadsheet_id,
            "requests_processed": len(requests)
        }
        
    except Exception as e:
        logger.error(f"Google Sheets batch_update error: {e}")
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


def build_row_data(action_config: Dict[str, Any], trigger_data: Dict[str, Any]) -> List[str]:
    """Build row data from configuration and trigger data"""
    try:
        row_data = []
        
        # Get column mappings
        column_mappings = action_config.get("columns", [])
        
        if not column_mappings:
            # Default mapping - use common fields
            default_fields = ["timestamp", "platform", "event", "id", "subject", "status", "priority"]
            for field in default_fields:
                value = trigger_data.get(field, "")
                row_data.append(str(value) if value is not None else "")
        else:
            # Use configured mappings
            for column_config in column_mappings:
                if isinstance(column_config, str):
                    # Simple field name
                    value = trigger_data.get(column_config, "")
                    row_data.append(str(value) if value is not None else "")
                elif isinstance(column_config, dict):
                    # Complex mapping with template
                    template = column_config.get("template", column_config.get("field", ""))
                    formatted_value = format_text(template, trigger_data)
                    row_data.append(formatted_value)
                else:
                    row_data.append("")
        
        return row_data
        
    except Exception as e:
        logger.error(f"Error building row data: {e}")
        return []


async def find_row_by_criteria(
    access_token: str,
    spreadsheet_id: str,
    sheet_name: str,
    action_config: Dict[str, Any],
    trigger_data: Dict[str, Any]
) -> Optional[int]:
    """Find row by search criteria"""
    try:
        search_config = action_config.get("search_criteria")
        if not search_config:
            return None
        
        search_column = search_config.get("column", "A")
        search_value = format_text(search_config.get("value", ""), trigger_data)
        
        # Get data from the search column
        range_name = f"{sheet_name}!{search_column}:{search_column}"
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            values = result.get("values", [])
            
            # Find matching row
            for i, row in enumerate(values):
                if row and len(row) > 0 and row[0] == search_value:
                    return i + 1  # Sheets are 1-indexed
            
            return None
            
    except Exception as e:
        logger.error(f"Error finding row by criteria: {e}")
        return None


async def add_headers(access_token: str, spreadsheet_id: str, sheet_name: str, headers: List[str]):
    """Add headers to a sheet"""
    try:
        range_name = f"{sheet_name}!A1:Z1"
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}"
        
        headers_api = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "values": [headers],
            "majorDimension": "ROWS"
        }
        
        params = {
            "valueInputOption": "USER_ENTERED"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(url, headers=headers_api, json=payload, params=params)
            response.raise_for_status()
            
    except Exception as e:
        logger.error(f"Error adding headers: {e}")


def build_format_requests(format_updates: List[Dict[str, Any]], trigger_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build formatting requests for batch update"""
    try:
        requests = []
        
        for format_update in format_updates:
            request_type = format_update.get("type")
            
            if request_type == "merge_cells":
                requests.append({
                    "mergeCells": {
                        "range": format_update.get("range"),
                        "mergeType": format_update.get("merge_type", "MERGE_ALL")
                    }
                })
            elif request_type == "format_cells":
                requests.append({
                    "repeatCell": {
                        "range": format_update.get("range"),
                        "cell": {
                            "userEnteredFormat": format_update.get("format")
                        },
                        "fields": "userEnteredFormat"
                    }
                })
            elif request_type == "auto_resize":
                requests.append({
                    "autoResizeDimensions": {
                        "dimensions": format_update.get("dimensions")
                    }
                })
        
        return requests
        
    except Exception as e:
        logger.error(f"Error building format requests: {e}")
        return []


async def batch_update_values(
    access_token: str,
    spreadsheet_id: str,
    value_updates: List[Dict[str, Any]],
    trigger_data: Dict[str, Any]
):
    """Perform batch value updates"""
    try:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values:batchUpdate"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        data = []
        for update in value_updates:
            range_name = update.get("range")
            values = update.get("values", [])
            
            # Format values with trigger data
            formatted_values = []
            for row in values:
                formatted_row = []
                for cell in row:
                    if isinstance(cell, str):
                        formatted_row.append(format_text(cell, trigger_data))
                    else:
                        formatted_row.append(cell)
                formatted_values.append(formatted_row)
            
            data.append({
                "range": range_name,
                "values": formatted_values,
                "majorDimension": "ROWS"
            })
        
        payload = {
            "valueInputOption": "USER_ENTERED",
            "data": data
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
    except Exception as e:
        logger.error(f"Error in batch value update: {e}")
        raise

