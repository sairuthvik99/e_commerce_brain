"""
API Middleware Package

Contains middleware components for request/response processing.
"""

from backend.api.middleware.error_handler import setup_error_handlers

__all__ = ["setup_error_handlers"]