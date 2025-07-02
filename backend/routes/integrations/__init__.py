"""
Integration management routes package
"""
from fastapi import APIRouter
from .routes import router

# Re-export the router
__all__ = ["router"]
