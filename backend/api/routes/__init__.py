"""
API Routes Package

Contains all route modules for the FastAPI application.
"""

from fastapi import APIRouter

from backend.api.routes.health import router as health_router
from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.jobs import router as jobs_router

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(analysis_router, tags=["Analysis"])
api_router.include_router(jobs_router, tags=["Jobs"])

__all__ = ["api_router"]