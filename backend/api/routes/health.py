"""
Health Check Endpoint

Provides system health status including all dependent services.
"""

import time
import asyncio
from typing import Dict
from datetime import datetime

from fastapi import APIRouter, Depends
from loguru import logger

from backend.api.config import APISettings, get_settings
from backend.api.schemas import (
    HealthResponse,
    ServiceHealth,
    ServiceStatus,
    MessageResponse
)

router = APIRouter()


async def check_database_health(settings: APISettings) -> ServiceHealth:
    """
    Check PostgreSQL database health.
    
    Args:
        settings: API settings containing database configuration
        
    Returns:
        ServiceHealth: Database health status
    """
    start_time = time.time()
    
    try:
        # Import here to avoid circular imports
        from backend.database.connection import get_db_session
        
        # Try to execute a simple query
        async with get_db_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        
        latency_ms = (time.time() - start_time) * 1000
        
        return ServiceHealth(
            status=ServiceStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
            message="Connected to PostgreSQL",
            last_checked=datetime.utcnow()
        )
        
    except ImportError:
        # Database module not yet implemented
        return ServiceHealth(
            status=ServiceStatus.UNKNOWN,
            latency_ms=None,
            message="Database module not implemented",
            last_checked=datetime.utcnow()
        )
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Database health check failed: {e}")
        
        return ServiceHealth(
            status=ServiceStatus.UNHEALTHY,
            latency_ms=round(latency_ms, 2),
            message=f"Connection failed: {str(e)[:100]}",
            last_checked=datetime.utcnow()
        )


async def check_vector_db_health(settings: APISettings) -> ServiceHealth:
    """
    Check Pinecone Vector DB health.
    
    Args:
        settings: API settings containing Pinecone configuration
        
    Returns:
        ServiceHealth: Vector DB health status
    """
    start_time = time.time()
    
    try:
        # Check if Pinecone is configured
        if not settings.pinecone_api_key:
            return ServiceHealth(
                status=ServiceStatus.UNKNOWN,
                latency_ms=None,
                message="Pinecone not configured",
                last_checked=datetime.utcnow()
            )
        
        # Import and check Pinecone
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=settings.pinecone_api_key)
        
        # List indexes to verify connection
        indexes = pc.list_indexes()
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Check if our index exists
        index_names = [idx.name for idx in indexes]
        if settings.pinecone_index_name in index_names:
            message = f"Pinecone index '{settings.pinecone_index_name}' accessible"
            status = ServiceStatus.HEALTHY
        else:
            message = f"Index '{settings.pinecone_index_name}' not found"
            status = ServiceStatus.DEGRADED
        
        return ServiceHealth(
            status=status,
            latency_ms=round(latency_ms, 2),
            message=message,
            last_checked=datetime.utcnow()
        )
        
    except ImportError:
        return ServiceHealth(
            status=ServiceStatus.UNKNOWN,
            latency_ms=None,
            message="Pinecone package not installed",
            last_checked=datetime.utcnow()
        )
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Vector DB health check failed: {e}")
        
        return ServiceHealth(
            status=ServiceStatus.UNHEALTHY,
            latency_ms=round(latency_ms, 2),
            message=f"Connection failed: {str(e)[:100]}",
            last_checked=datetime.utcnow()
        )


async def check_llm_health(settings: APISettings) -> ServiceHealth:
    """
    Check Azure OpenAI LLM health.
    
    Args:
        settings: API settings containing Azure OpenAI configuration
        
    Returns:
        ServiceHealth: LLM health status
    """
    start_time = time.time()
    
    try:
        # Check if Azure OpenAI is configured
        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            return ServiceHealth(
                status=ServiceStatus.UNKNOWN,
                latency_ms=None,
                message="Azure OpenAI not configured",
                last_checked=datetime.utcnow()
            )
        
        # Import and check Azure OpenAI
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint
        )
        
        # Simple completion to verify connection
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return ServiceHealth(
            status=ServiceStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
            message="Azure OpenAI responding",
            last_checked=datetime.utcnow()
        )
        
    except ImportError:
        return ServiceHealth(
            status=ServiceStatus.UNKNOWN,
            latency_ms=None,
            message="OpenAI package not installed",
            last_checked=datetime.utcnow()
        )
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"LLM health check failed: {e}")
        
        return ServiceHealth(
            status=ServiceStatus.UNHEALTHY,
            latency_ms=round(latency_ms, 2),
            message=f"Connection failed: {str(e)[:100]}",
            last_checked=datetime.utcnow()
        )


async def check_langfuse_health(settings: APISettings) -> ServiceHealth:
    """
    Check Langfuse observability service health.
    
    Args:
        settings: API settings containing Langfuse configuration
        
    Returns:
        ServiceHealth: Langfuse health status
    """
    start_time = time.time()
    
    try:
        # Check if Langfuse is configured
        if not settings.langfuse_public_key or not settings.langfuse_secret_key:
            return ServiceHealth(
                status=ServiceStatus.UNKNOWN,
                latency_ms=None,
                message="Langfuse not configured",
                last_checked=datetime.utcnow()
            )
        
        # Import and check Langfuse
        from langfuse import Langfuse
        
        langfuse = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host
        )
        
        # Auth check
        langfuse.auth_check()
        
        latency_ms = (time.time() - start_time) * 1000
        
        return ServiceHealth(
            status=ServiceStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
            message="Langfuse connected",
            last_checked=datetime.utcnow()
        )
        
    except ImportError:
        return ServiceHealth(
            status=ServiceStatus.UNKNOWN,
            latency_ms=None,
            message="Langfuse package not installed",
            last_checked=datetime.utcnow()
        )
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.warning(f"Langfuse health check failed: {e}")
        
        # Langfuse is optional, so degraded not unhealthy
        return ServiceHealth(
            status=ServiceStatus.DEGRADED,
            latency_ms=round(latency_ms, 2),
            message=f"Connection issue: {str(e)[:100]}",
            last_checked=datetime.utcnow()
        )


def determine_overall_status(services: Dict[str, ServiceHealth]) -> ServiceStatus:
    """
    Determine overall system status based on individual service statuses.
    
    Args:
        services: Dictionary of service health statuses
        
    Returns:
        ServiceStatus: Overall system status
    """
    statuses = [s.status for s in services.values()]
    
    # If any critical service is unhealthy, system is unhealthy
    critical_services = ["database", "llm"]
    for service_name in critical_services:
        if service_name in services and services[service_name].status == ServiceStatus.UNHEALTHY:
            return ServiceStatus.UNHEALTHY
    
    # If any service is unhealthy, system is degraded
    if ServiceStatus.UNHEALTHY in statuses:
        return ServiceStatus.DEGRADED
    
    # If any service is degraded, system is degraded
    if ServiceStatus.DEGRADED in statuses:
        return ServiceStatus.DEGRADED
    
    # If all critical services are healthy, system is healthy
    all_healthy = all(
        services.get(svc, ServiceHealth(status=ServiceStatus.UNKNOWN)).status 
        in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN]
        for svc in critical_services
    )
    
    if all_healthy:
        return ServiceStatus.HEALTHY
    
    return ServiceStatus.UNKNOWN


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the API and all dependent services",
    responses={
        200: {"description": "Health status retrieved successfully"},
        503: {"description": "Service unavailable - critical services down"}
    }
)
async def health_check(
    settings: APISettings = Depends(get_settings)
) -> HealthResponse:
    """
    Comprehensive health check endpoint.
    
    Checks the status of:
    - PostgreSQL Database
    - Pinecone Vector DB
    - Azure OpenAI LLM
    - Langfuse Observability
    
    Returns:
        HealthResponse: Complete health status of all services
    """
    logger.info("Performing health check...")
    
    # Run all health checks concurrently
    database_health, vector_db_health, llm_health, langfuse_health = await asyncio.gather(
        check_database_health(settings),
        check_vector_db_health(settings),
        check_llm_health(settings),
        check_langfuse_health(settings),
        return_exceptions=True
    )
    
    # Handle any exceptions from gather
    def safe_health(result, service_name: str) -> ServiceHealth:
        if isinstance(result, Exception):
            logger.error(f"Health check for {service_name} raised exception: {result}")
            return ServiceHealth(
                status=ServiceStatus.UNHEALTHY,
                message=f"Health check failed: {str(result)[:100]}",
                last_checked=datetime.utcnow()
            )
        return result
    
    services = {
        "database": safe_health(database_health, "database"),
        "vector_db": safe_health(vector_db_health, "vector_db"),
        "llm": safe_health(llm_health, "llm"),
        "langfuse": safe_health(langfuse_health, "langfuse")
    }
    
    # Determine overall status
    overall_status = determine_overall_status(services)
    
    response = HealthResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        services=services
    )
    
    logger.info(f"Health check completed: {overall_status.value}")
    
    return response


@router.get(
    "/health/live",
    response_model=MessageResponse,
    summary="Liveness Probe",
    description="Simple liveness check for Kubernetes/container orchestration",
    responses={
        200: {"description": "Service is alive"}
    }
)
async def liveness_probe() -> Dict[str, str]:
    """
    Simple liveness probe endpoint.
    
    Used by Kubernetes or other orchestration tools to check if the service is running.
    Does not check dependent services.
    
    Returns:
        dict: Simple alive status
    """
    return {"status": "alive", "message": "Service is running"}


@router.get(
    "/health/ready",
    response_model=MessageResponse,
    summary="Readiness Probe",
    description="Readiness check for accepting traffic",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"}
    }
)
async def readiness_probe(
    settings: APISettings = Depends(get_settings)
) -> Dict[str, str]:
    """
    Readiness probe endpoint.
    
    Checks if the service is ready to accept traffic.
    Verifies critical services (database, LLM) are available.
    
    Returns:
        dict: Readiness status
        
    Raises:
        HTTPException: If critical services are not available
    """
    from fastapi import HTTPException
    
    # Quick check of critical services
    db_health = await check_database_health(settings)
    llm_health = await check_llm_health(settings)
    
    critical_healthy = (
        db_health.status in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN] and
        llm_health.status in [ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN]
    )
    
    if critical_healthy:
        return {"status": "ready", "message": "Service is ready to accept traffic"}
    
    raise HTTPException(
        status_code=503,
        detail="Service is not ready - critical services unavailable"
    )

