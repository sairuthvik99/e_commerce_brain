"""
API Pydantic Schemas

Request and response models for all API endpoints.
Designed to be flexible while maintaining type safety.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


from ..schemas.agent_output import AgentOutput
from ..schemas.root_cause import RootCause
from ..schemas.reflection_result import ReflectionResult
from ..schemas.action_proposal import ActionProposal
from ..schemas.hitl_decision import HITLDecision
from ..schemas.memory_record import MemoryRecord

# ============================================================
# Enums
# ============================================================

class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    AWAITING_APPROVAL = "awaiting_approval"


class AgentType(str, Enum):
    """Agent type enumeration."""
    SUPERVISOR = "supervisor"
    INVENTORY = "inventory"
    SALES = "sales"
    MARKETING = "marketing"
    SUPPORT = "support"
    SYNTHESIS = "synthesis"
    REFLECTION = "reflection"


class ServiceStatus(str, Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# ============================================================
# Health Check Schemas
# ============================================================

class ServiceHealth(BaseModel):
    """Individual service health status."""
    status: ServiceStatus = Field(..., description="Service status")
    latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")
    message: Optional[str] = Field(None, description="Additional status message")
    last_checked: datetime = Field(default_factory=datetime.utcnow, description="Last health check time")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: ServiceStatus = Field(..., description="Overall system status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    services: Dict[str, ServiceHealth] = Field(
        default_factory=dict, 
        description="Individual service health statuses"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-01-27T10:30:00Z",
                "services": {
                    "database": {
                        "status": "healthy",
                        "latency_ms": 15.5,
                        "message": "Connected to PostgreSQL",
                        "last_checked": "2025-01-27T10:30:00Z"
                    }
                }
            }
        }


# ============================================================
# Analysis Request/Response Schemas
# ============================================================

class AnalysisContext(BaseModel):
    """Optional context for analysis requests."""
    time_range: Optional[str] = Field(None, description="Time range for analysis (e.g., 'last_7_days')")
    priority: Optional[str] = Field(None, description="Analysis priority (low, medium, high)")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Any additional context")


class AnalysisRequest(BaseModel):
    """Request model for submitting an analysis."""
    question: str = Field(
        ..., 
        min_length=10, 
        max_length=1000,
        description="Business question to analyze"
    )
    context: Optional[AnalysisContext] = Field(None, description="Optional analysis context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Why did sales drop 40% yesterday compared to last week?",
                "context": {
                    "time_range": "last_7_days",
                    "priority": "high",
                    "focus_areas": ["inventory", "marketing"]
                }
            }
        }


class AnalysisSubmitResponse(BaseModel):
    """Response model for analysis submission."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Initial job status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Job creation timestamp")
    message: str = Field(..., description="Status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_abc123def456",
                "status": "pending",
                "created_at": "2025-01-27T10:30:00Z",
                "message": "Analysis job created successfully"
            }
        }


# ============================================================
# Job Progress Schemas
# ============================================================

class AgentProgress(BaseModel):
    """Progress information for a single agent."""
    agent: AgentType = Field(..., description="Agent type")
    status: str = Field(..., description="Agent status (pending, running, completed, failed)")
    started_at: Optional[datetime] = Field(None, description="When agent started")
    completed_at: Optional[datetime] = Field(None, description="When agent completed")
    findings_summary: Optional[str] = Field(None, description="Brief summary of findings")


class JobProgress(BaseModel):
    """Job progress information."""
    current_agent: Optional[AgentType] = Field(None, description="Currently running agent")
    completed_agents: List[AgentType] = Field(default_factory=list, description="Completed agents")
    pending_agents: List[AgentType] = Field(default_factory=list, description="Pending agents")
    percentage: int = Field(0, ge=0, le=100, description="Overall progress percentage")
    agent_details: List[AgentProgress] = Field(default_factory=list, description="Detailed agent progress")


# ============================================================
# Flexible Result Schemas (Allow Any Structure)
# ============================================================

class JobResult(BaseModel):
    """
    Complete analysis result.
    
    Uses flexible Dict types to accommodate various agent output formats.
    """
    question: str = Field(..., description="Original question")
    agent_findings: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Findings from each agent (flexible structure)"
    )
    root_cause: Optional[Dict[str, Any]] = Field(
        None, 
        description="Root cause analysis (flexible structure)"
    )
    reflection: Optional[Dict[str, Any]] = Field(
        None, 
        description="Self-reflection result (flexible structure)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Why did sales drop 40% yesterday?",
                "agent_findings": {
                    "inventory": {
                        "findings": [{"description": "Low stock on SKU-1234"}],
                        "summary": "Found 3 products with stock issues",
                        "confidence_score": 0.92
                    },
                    "sales": {
                        "findings": [{"description": "Revenue dropped 40%"}],
                        "summary": "Significant revenue decline",
                        "confidence_score": 0.94
                    }
                },
                "root_cause": {
                    "primary_cause": "Supply chain disruption",
                    "confidence_score": 0.87
                },
                "reflection": {
                    "quality_score": 0.85,
                    "recommendations": ["Extend analysis time range"]
                }
            }
        }


# ============================================================
# Complete Job Response Schema
# ============================================================

class JobResponse(BaseModel):
    """Complete job status and result response."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress: Optional[JobProgress] = Field(None, description="Job progress information")
    result: Optional[JobResult] = Field(None, description="Analysis result (when completed)")
    error: Optional[str] = Field(None, description="Error message (when failed)")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_abc123def456",
                "status": "completed",
                "progress": None,
                "result": {
                    "question": "Why did sales drop 40% yesterday?",
                    "agent_findings": {},
                    "root_cause": {},
                    "reflection": {}
                },
                "error": None,
                "created_at": "2025-01-27T10:30:00Z",
                "updated_at": "2025-01-27T10:32:00Z",
                "completed_at": "2025-01-27T10:32:00Z"
            }
        }


# ============================================================
# Job List Schemas
# ============================================================

class JobSummary(BaseModel):
    """Summary of a job for list views."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    question: str = Field(..., description="Original question (truncated)")
    created_at: datetime = Field(..., description="Job creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


class JobListResponse(BaseModel):
    """Response model for job listing."""
    jobs: List[JobSummary] = Field(default_factory=list, description="List of jobs")
    total: int = Field(..., description="Total number of jobs matching criteria")
    page: int = Field(1, ge=1, description="Current page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")


# ============================================================
# Error Schemas
# ============================================================

class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


# ============================================================
# Generic Response Schemas
# ============================================================

class MessageResponse(BaseModel):
    """Simple message response."""
    message: str = Field(..., description="Response message")
    success: bool = Field(True, description="Operation success status")


class JobCancelResponse(BaseModel):
    """Response for job cancellation."""
    job_id: str = Field(..., description="Cancelled job ID")
    status: JobStatus = Field(..., description="New job status")
    message: str = Field(..., description="Cancellation message")