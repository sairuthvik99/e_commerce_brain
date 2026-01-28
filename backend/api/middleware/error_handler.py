"""
Global Error Handler Middleware

Provides consistent error responses across the API.
"""

import traceback
from typing import Union
from datetime import datetime
import uuid

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from loguru import logger

from backend.api.schemas import ErrorResponse, ErrorDetail


def setup_error_handlers(app: FastAPI) -> None:
    """
    Setup global error handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, 
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors from request parsing."""
        request_id = str(uuid.uuid4())[:8]
        
        logger.warning(
            f"Validation error [req_id={request_id}]: {exc.errors()}"
        )
        
        details = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body'
            details.append(ErrorDetail(
                field=field if field else None,
                message=error["msg"],
                code=error["type"]
            ))
        
        error_response = ErrorResponse(
            error="ValidationError",
            message="Invalid request parameters",
            details=details,
            request_id=f"req_{request_id}",
            timestamp=datetime.utcnow()
        )
        
        return JSONResponse(
            status_code=422,
            content=error_response.model_dump(mode="json")
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, 
        exc: HTTPException
    ) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        request_id = str(uuid.uuid4())[:8]
        
        logger.warning(
            f"HTTP exception [req_id={request_id}]: {exc.status_code} - {exc.detail}"
        )
        
        error_response = ErrorResponse(
            error=f"HTTPError{exc.status_code}",
            message=str(exc.detail),
            details=None,
            request_id=f"req_{request_id}",
            timestamp=datetime.utcnow()
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(mode="json")
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, 
        exc: ValueError
    ) -> JSONResponse:
        """Handle ValueError exceptions."""
        request_id = str(uuid.uuid4())[:8]
        
        logger.error(
            f"Value error [req_id={request_id}]: {str(exc)}"
        )
        
        error_response = ErrorResponse(
            error="ValueError",
            message=str(exc),
            details=None,
            request_id=f"req_{request_id}",
            timestamp=datetime.utcnow()
        )
        
        return JSONResponse(
            status_code=400,
            content=error_response.model_dump(mode="json")
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Handle all unhandled exceptions."""
        request_id = str(uuid.uuid4())[:8]
        
        # Log full traceback for debugging
        logger.error(
            f"Unhandled exception [req_id={request_id}]: {type(exc).__name__}: {str(exc)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )
        
        # Don't expose internal error details in production
        error_response = ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred. Please try again later.",
            details=[ErrorDetail(
                field=None,
                message=f"{type(exc).__name__}: {str(exc)[:200]}",
                code="internal_error"
            )] if logger.level("DEBUG").no <= logger.level("INFO").no else None,
            request_id=f"req_{request_id}",
            timestamp=datetime.utcnow()
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(mode="json")
        )


class RequestLoggingMiddleware:
    """Middleware for logging all incoming requests."""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        """Process request and log details."""
        request_id = str(uuid.uuid4())[:8]
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log incoming request
        logger.info(
            f"[req_id={request_id}] {request.method} {request.url.path} - Started"
        )
        
        # Process request
        import time
        start_time = time.time()
        
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            f"[req_id={request_id}] {request.method} {request.url.path} - "
            f"Completed {response.status_code} in {process_time:.2f}ms"
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = f"req_{request_id}"
        response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
        
        return response