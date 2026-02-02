"""
API Routes Package

Contains all route modules for the FastAPI application.
"""

from fastapi import APIRouter

from backend.api.routes.health import router as health_router
from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.jobs import router as jobs_router
from backend.api.routes.hitl import router as hitl_router
from backend.api.routes.memory import router as memory_router
from backend.api.routes.websocket import router as websocket_router
from backend.api.routes.ecommerce import router as ecommerce_router

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(analysis_router, tags=["Analysis"])
api_router.include_router(jobs_router, tags=["Jobs"])
api_router.include_router(hitl_router, tags=["HITL - Human in the Loop"])
api_router.include_router(memory_router, tags=["Memory"])
api_router.include_router(websocket_router, tags=["WebSocket"])
api_router.include_router(ecommerce_router, tags=["E-Commerce Data"])

__all__ = ["api_router"]