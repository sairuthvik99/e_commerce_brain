"""
Job Management Endpoints

Endpoints for querying and managing analysis jobs.
"""

from typing import Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from loguru import logger

from backend.api.schemas import (
    JobStatus,
    JobResponse,
    JobListResponse,
    JobSummary,
    JobCancelResponse,
    MessageResponse,
)
from backend.api.services.job_manager import JobManager, get_job_manager

router = APIRouter()


@router.get(
    "/jobs",
    response_model=JobListResponse,
    summary="List Jobs",
    description="List all analysis jobs with optional filtering and pagination",
    responses={
        200: {"description": "Jobs retrieved successfully"}
    }
)
async def list_jobs(
    status: Optional[JobStatus] = Query(
        None, 
        description="Filter by job status"
    ),
    limit: int = Query(
        10, 
        ge=1, 
        le=100, 
        description="Maximum number of jobs to return"
    ),
    page: int = Query(
        1, 
        ge=1, 
        description="Page number"
    ),
    job_manager: JobManager = Depends(get_job_manager)
) -> JobListResponse:
    """
    List analysis jobs with filtering and pagination.
    
    Args:
        status: Optional status filter
        limit: Maximum jobs per page (1-100)
        page: Page number (starting from 1)
        
    Returns:
        JobListResponse: Paginated list of jobs
    """
    offset = (page - 1) * limit
    
    jobs, total = await job_manager.get_all_jobs(
        status=status,
        limit=limit,
        offset=offset
    )
    
    # Convert to summaries
    job_summaries = [
        JobSummary(
            job_id=job.job_id,
            status=job.status,
            question=job.question[:100] + "..." if len(job.question) > 100 else job.question,
            created_at=job.created_at,
            completed_at=job.completed_at
        )
        for job in jobs
    ]
    
    has_more = (offset + len(jobs)) < total
    
    return JobListResponse(
        jobs=job_summaries,
        total=total,
        page=page,
        limit=limit,
        has_more=has_more
    )


@router.get(
    "/jobs/stats",
    summary="Get Job Statistics",
    description="Get statistics about job processing",
    responses={
        200: {"description": "Statistics retrieved successfully"}
    }
)
async def get_job_stats(
    job_manager: JobManager = Depends(get_job_manager)
) -> Dict[str, Any]:
    """
    Get job processing statistics.
    
    Returns:
        dict: Job statistics including counts by status
    """
    stats = await job_manager.get_stats()
    return stats


@router.get(
    "/jobs/{job_id}",
    summary="Get Job Details",
    description="Get detailed information about a specific job including progress and results",
    responses={
        200: {"description": "Job details retrieved successfully"},
        404: {"description": "Job not found"}
    }
)
async def get_job(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
) -> Dict[str, Any]:
    """
    Get detailed job information.
    
    Args:
        job_id: The unique job identifier
        
    Returns:
        Dict: Complete job details including progress and results
        
    Raises:
        HTTPException: If job is not found
    """
    job = await job_manager.get_job(job_id)
    
    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found"
        )
    
    # Convert to response format (returns Dict, not strict Pydantic model)
    response_data = job_manager.job_to_response(job)
    
    return response_data


@router.delete(
    "/jobs/{job_id}",
    response_model=JobCancelResponse,
    summary="Cancel Job",
    description="Cancel a pending or running job",
    responses={
        200: {"description": "Job cancelled successfully"},
        404: {"description": "Job not found"},
        409: {"description": "Job cannot be cancelled (already completed/failed)"}
    }
)
async def cancel_job(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
) -> JobCancelResponse:
    """
    Cancel a job.
    
    Can only cancel jobs that are pending or running.
    Completed, failed, or already cancelled jobs cannot be cancelled.
    
    Args:
        job_id: The unique job identifier
        
    Returns:
        JobCancelResponse: Cancellation confirmation
        
    Raises:
        HTTPException: If job not found or cannot be cancelled
    """
    job = await job_manager.get_job(job_id)
    
    if not job:
        logger.warning(f"Job not found for cancellation: {job_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found"
        )
    
    # Check if job can be cancelled
    if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
        logger.warning(f"Cannot cancel job {job_id} with status {job.status}")
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel job with status '{job.status.value}'. "
                   f"Only pending or running jobs can be cancelled."
        )
    
    # Cancel the job
    cancelled_job = await job_manager.cancel_job(job_id)
    
    logger.info(f"Job cancelled: {job_id}")
    
    return JobCancelResponse(
        job_id=job_id,
        status=cancelled_job.status,
        message="Job cancelled successfully"
    )


@router.get(
    "/jobs/{job_id}/result",
    summary="Get Job Result",
    description="Get only the result of a completed job",
    responses={
        200: {"description": "Result retrieved successfully"},
        404: {"description": "Job not found"},
        409: {"description": "Job not completed yet"}
    }
)
async def get_job_result(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
) -> Dict[str, Any]:
    """
    Get only the result of a completed job.
    
    This is a convenience endpoint that returns just the result
    without progress information.
    
    Args:
        job_id: The unique job identifier
        
    Returns:
        dict: Job result including findings, root cause, and reflection
        
    Raises:
        HTTPException: If job not found or not completed
    """
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found"
        )
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not completed. Current status: '{job.status.value}'"
        )
    
    return {
        "job_id": job_id,
        "question": job.question,
        "agent_findings": job.agent_findings,
        "root_cause": job.root_cause,
        "reflection": job.reflection,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }


@router.get(
    "/jobs/{job_id}/progress",
    summary="Get Job Progress",
    description="Get only the progress of a running job",
    responses={
        200: {"description": "Progress retrieved successfully"},
        404: {"description": "Job not found"}
    }
)
async def get_job_progress(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
) -> Dict[str, Any]:
    """
    Get only the progress of a job.
    
    This is useful for lightweight polling during job execution.
    
    Args:
        job_id: The unique job identifier
        
    Returns:
        dict: Job progress information
        
    Raises:
        HTTPException: If job not found
    """
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found"
        )
    
    progress = job_manager.get_job_progress(job)
    
    return {
        "job_id": job_id,
        "status": job.status.value,
        "progress": progress.model_dump() if job.status == JobStatus.RUNNING else None,
        "updated_at": job.updated_at.isoformat()
    }