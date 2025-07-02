"""
Integration management routes with enhanced Freshdesk and Zendesk support
"""
from fastapi import APIRouter
from .handlers import (
    create_integration,
    get_integrations,
    get_integration,
    update_integration,
    delete_integration,
    test_integration,
    get_available_platforms,
    execute_integration_action
)
from .utils import get_platform_actions, get_supported_platforms

# Create router
router = APIRouter(
    prefix="/integrations",
    tags=["integrations"],
    responses={404: {"description": "Not found"}},
)

# Register routes
router.add_api_route("/", create_integration, methods=["POST"])
router.add_api_route("/", get_integrations, methods=["GET"])
router.add_api_route("/platforms", get_available_platforms, methods=["GET"])
router.add_api_route("/platforms/{platform}/actions", get_platform_actions, methods=["GET"])
router.add_api_route("/{integration_id}", get_integration, methods=["GET"])
router.add_api_route("/{integration_id}", update_integration, methods=["PUT"])
router.add_api_route("/{integration_id}", delete_integration, methods=["DELETE"])
router.add_api_route("/{integration_id}/test", test_integration, methods=["POST"])
router.add_api_route("/{integration_id}/execute", execute_integration_action, methods=["POST"])
