"""
Analysis Endpoints

Endpoints for submitting and managing analysis requests.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from loguru import logger

from backend.api.schemas import (
    AnalysisRequest,
    AnalysisSubmitResponse,
    JobStatus,
    ErrorResponse,
)
from backend.api.services.job_manager import JobManager, get_job_manager
from backend.api.services.analysis_service import AnalysisService, get_analysis_service
from backend.api.config import APISettings, get_settings

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalysisSubmitResponse,
    status_code=202,
    summary="Submit Analysis Request",
    description="Submit a new business question for analysis by the AI Operations Brain",
    responses={
        202: {"description": "Analysis job created successfully"},
        400: {"description": "Invalid request parameters"},
        429: {"description": "Too many concurrent jobs"},
        500: {"description": "Internal server error"}
    }
)
async def submit_analysis(
    request: AnalysisRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    job_manager: JobManager = Depends(get_job_manager),
    settings: APISettings = Depends(get_settings)
) -> AnalysisSubmitResponse:
    """
    Submit a new analysis request.
    
    This endpoint creates a new analysis job and starts processing in the background.
    The job runs through the following agents:
    1. Supervisor - Intent classification and routing
    2. Inventory - Stock and supply analysis
    3. Sales - Revenue and order analysis
    4. Marketing - Campaign and traffic analysis
    5. Support - Ticket and complaint analysis
    6. Synthesis - Root cause identification
    7. Reflection - Quality validation
    
    Args:
        request: Analysis request containing the business question
        
    Returns:
        AnalysisSubmitResponse: Job ID and initial status
        
    Raises:
        HTTPException: If job cannot be created
    """
    logger.info(f"Received analysis request: {request.question[:100]}...")
    
    # Check concurrent job limit
    stats = await job_manager.get_stats()
    running_jobs = stats["by_status"].get("running", 0) + stats["by_status"].get("pending", 0)
    
    if running_jobs >= settings.max_concurrent_jobs:
        logger.warning(f"Concurrent job limit reached: {running_jobs}/{settings.max_concurrent_jobs}")
        raise HTTPException(
            status_code=429,
            detail=f"Maximum concurrent jobs ({settings.max_concurrent_jobs}) reached. Please try again later."
        )
    
    try:
        # Submit analysis job
        context_dict = request.context.model_dump() if request.context else None
        job = await analysis_service.submit_analysis(
            question=request.question,
            context=context_dict
        )
        
        logger.info(f"Analysis job created: {job.job_id}")
        
        return AnalysisSubmitResponse(
            job_id=job.job_id,
            status=job.status,
            created_at=job.created_at,
            message="Analysis job created successfully. Use the job_id to track progress."
        )
        
    except Exception as e:
        logger.error(f"Failed to create analysis job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create analysis job: {str(e)}"
        )


@router.post(
    "/analyze/sync",
    summary="Submit Synchronous Analysis (for testing)",
    description="Submit an analysis and wait for completion. Use for testing only.",
    responses={
        200: {"description": "Analysis completed"},
        408: {"description": "Analysis timed out"},
        500: {"description": "Analysis failed"}
    }
)
async def submit_analysis_sync(
    request: AnalysisRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    job_manager: JobManager = Depends(get_job_manager),
    settings: APISettings = Depends(get_settings)
):
    """
    Submit an analysis and wait for completion.
    
    WARNING: This endpoint is for testing only. In production, use the
    async /analyze endpoint and poll for results.
    
    Args:
        request: Analysis request
        
    Returns:
        Complete job result
    """
    import asyncio
    
    logger.info(f"Received sync analysis request: {request.question[:100]}...")
    
    try:
        # Submit job
        context_dict = request.context.model_dump() if request.context else None
        job = await analysis_service.submit_analysis(
            question=request.question,
            context=context_dict
        )
        
        # Wait for completion with timeout
        timeout = settings.job_timeout_seconds
        poll_interval = 0.5
        elapsed = 0
        
        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            
            job = await job_manager.get_job(job.job_id)
            if not job:
                raise HTTPException(status_code=500, detail="Job disappeared")
            
            if job.status == JobStatus.COMPLETED:
                return job_manager.job_to_response(job)
            
            if job.status == JobStatus.FAILED:
                raise HTTPException(
                    status_code=500,
                    detail=f"Analysis failed: {job.error}"
                )
            
            if job.status == JobStatus.CANCELLED:
                raise HTTPException(
                    status_code=500,
                    detail="Analysis was cancelled"
                )
        
        # Timeout
        raise HTTPException(
            status_code=408,
            detail=f"Analysis timed out after {timeout} seconds"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))