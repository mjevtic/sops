"""
Integration management routes
This file serves as a bridge between the old structure and the new modular structure.
"""

# Re-export the router from the integrations package
from .integrations.routes import router

# For backward compatibility
__all__ = ["router"]
