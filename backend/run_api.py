"""
API Entry Point

Run this file to start the FastAPI server.
"""

import sys
import uvicorn
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from backend.api.config import get_api_settings


def configure_logging():
    """Configure loguru for the API."""
    logger.remove()  # Remove default handler
    
    # Console handler with color
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # File handler for all logs
    logger.add(
        "logs/api.log",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    # File handler for errors only
    logger.add(
        "logs/api_errors.log",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR"
    )


def main():
    """Main entry point for the API server."""
    # Configure logging
    configure_logging()
    
    # Get settings
    settings = get_api_settings()
    
    logger.info("=" * 60)
    logger.info("🚀 Starting AI Operations Brain API Server")
    logger.info("=" * 60)
    logger.info(f"Host: {settings.api_host}")
    logger.info(f"Port: {settings.api_port}")
    logger.info(f"Debug: {settings.debug}")
    logger.info(f"Docs: http://{settings.api_host}:{settings.api_port}/docs")
    logger.info("=" * 60)
    
    # Run server
    uvicorn.run(
        "backend.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
        access_log=True
    )


if __name__ == "__main__":
    main()