"""
Integration route handlers
"""
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_

from database import get_session
from models.integration import (
    Integration, IntegrationCredential, IntegrationCreate, IntegrationUpdate, 
    IntegrationResponse, IntegrationType, IntegrationStatus
)
from models.audit import AuditLogCreate, AuditAction
from models.user import User
from services.audit import AuditService
from routes.auth import get_current_user
from middleware import rate_limit_by_user, get_remote_address
from config import encrypt_data, decrypt_data

from .utils import get_integration_handler, get_supported_platforms, get_platform_info, determine_credential_type
from .connection_tests import test_integration_connection

logger = logging.getLogger(__name__)

# Import individual handlers
from .handlers_create import create_integration
from .handlers_read import get_integrations, get_integration, get_available_platforms
from .handlers_update import update_integration
from .handlers_delete import delete_integration
from .handlers_test import test_integration
from .handlers_execute import execute_integration_action

# Re-export all handlers
__all__ = [
    'create_integration',
    'get_integrations',
    'get_integration',
    'update_integration',
    'delete_integration',
    'test_integration',
    'get_available_platforms',
    'execute_integration_action'
]
