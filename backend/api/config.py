"""
API Configuration Module

Centralized configuration for the FastAPI application using Pydantic Settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class APISettings(BaseSettings):
    """API-specific configuration settings."""
    
    # Application Info
    app_name: str = Field(default="AI Operations Brain", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_description: str = Field(
        default="Autonomous multi-agent system for e-commerce operations analysis",
        description="Application description"
    )
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_allow_methods: List[str] = Field(default=["*"], description="Allowed HTTP methods")
    cors_allow_headers: List[str] = Field(default=["*"], description="Allowed HTTP headers")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Max requests per window")
    rate_limit_window_seconds: int = Field(default=60, description="Rate limit window in seconds")
    
    # Job Settings
    max_concurrent_jobs: int = Field(default=10, description="Maximum concurrent analysis jobs")
    job_timeout_seconds: int = Field(default=300, description="Job timeout in seconds")
    job_retention_hours: int = Field(default=24, description="How long to keep completed jobs")
    
    # Database Settings (from existing settings)
    database_url: Optional[str] = Field(default=None, description="PostgreSQL connection URL")
    
    # Vector DB Settings
    pinecone_api_key: Optional[str] = Field(default=None, description="Pinecone API key")
    pinecone_environment: Optional[str] = Field(default=None, description="Pinecone environment")
    pinecone_index_name: str = Field(default="ai-ops-brain", description="Pinecone index name")
    
    # LLM Settings
    azure_openai_api_key: Optional[str] = Field(default=None, description="Azure OpenAI API key")
    azure_openai_endpoint: Optional[str] = Field(default=None, description="Azure OpenAI endpoint")
    azure_openai_deployment: str = Field(default="gpt-4", description="Azure OpenAI deployment name")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", description="API version")
    
    # Langfuse Settings
    langfuse_public_key: Optional[str] = Field(default=None, description="Langfuse public key")
    langfuse_secret_key: Optional[str] = Field(default=None, description="Langfuse secret key")
    langfuse_host: Optional[str] = Field(default=None, description="Langfuse host URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_api_settings() -> APISettings:
    """
    Get cached API settings instance.
    
    Returns:
        APISettings: Cached settings instance
    """
    return APISettings()


# Convenience function for dependency injection
def get_settings() -> APISettings:
    """Get API settings (for FastAPI dependency injection)."""
    return get_api_settings()