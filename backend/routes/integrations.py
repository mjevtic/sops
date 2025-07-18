"""
Integration management routes
This file is maintained for backward compatibility.
The actual implementation has been moved to the integrations/ package.
"""

# Re-export the router from the integrations package
from .integrations.routes import router

# For backward compatibility
__all__ = ["router"]
