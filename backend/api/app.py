"""
FastAPI Application Factory

Creates and configures the FastAPI application instance.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger

from backend.api.config import get_api_settings, APISettings
from backend.api.routes import api_router
from backend.api.middleware.error_handler import setup_error_handlers
from backend.graph import get_graph_manager

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the application.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None
    """
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Starting AI Operations Brain API...")
    logger.info("=" * 60)
    
    settings = get_api_settings()
    
    logger.info(f"Application: {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"API Prefix: {settings.api_prefix}")
    
    # Initialize connections (if needed)
    try:
        # Database connection pool initialization
        logger.info("Initializing database connection pool...")
        # await init_database()  # Uncomment when database module is ready
        
        # Vector DB initialization
        logger.info("Initializing vector database connection...")
        # await init_vector_db()  # Uncomment when vector_db module is ready
        
        # Pre-initialize the LangGraph (singleton pattern)
        # This ensures graph and all agents are built once at startup
        logger.info("Initializing LangGraph and agents...")
        try:
            graph_manager = get_graph_manager()
            if graph_manager.graph:
                logger.info("✅ LangGraph initialized successfully")
            else:
                logger.warning("⚠️ LangGraph initialization returned None")
        except Exception as e:
            logger.warning(f"⚠️ LangGraph initialization failed: {e}")
        
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        # Don't raise - allow app to start for health check debugging
    
    logger.info("=" * 60)
    logger.info("🟢 API is ready to accept requests")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("🛑 Shutting down AI Operations Brain API...")
    logger.info("=" * 60)
    
    try:
        # Cleanup connections
        logger.info("Closing database connections...")
        # await close_database()  # Uncomment when database module is ready
        
        logger.info("Closing vector database connections...")
        # await close_vector_db()  # Uncomment when vector_db module is ready
        
        logger.info("✅ Cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")
    
    logger.info("=" * 60)
    logger.info("👋 API shutdown complete")
    logger.info("=" * 60)


def create_app(settings: APISettings = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        settings: Optional API settings. If not provided, will load from environment.
        
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    if settings is None:
        settings = get_api_settings()
    
    # Create FastAPI instance
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Add GZip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Include API routes with prefix
    app.include_router(api_router, prefix=settings.api_prefix)
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": settings.app_description,
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health"
        }
    
    logger.info(f"FastAPI application created: {settings.app_name} v{settings.app_version}")
    
    return app


# Create default application instance
app = create_app()