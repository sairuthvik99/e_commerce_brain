"""
Job Manager Service

Manages analysis job state, progress tracking, and lifecycle.
Uses in-memory storage (can be replaced with Redis for production).
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
from dataclasses import dataclass, field
from collections import OrderedDict

from loguru import logger

from backend.api.schemas import (
    JobStatus,
    AgentType,
    JobProgress,
    AgentProgress,
    JobResult,
    AgentOutput,
    ReflectionResult,
)
from backend.api.config import get_api_settings


@dataclass
class Job:
    """Internal job representation."""
    job_id: str
    question: str
    context: Optional[Dict[str, Any]]
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Progress tracking
    current_agent: Optional[AgentType] = None
    completed_agents: List[AgentType] = field(default_factory=list)
    agent_progress: Dict[str, AgentProgress] = field(default_factory=dict)
    
    # Results
    agent_findings: Dict[str, Any] = field(default_factory=dict)
    root_cause: Optional[Dict[str, Any]] = None
    reflection: Optional[Dict[str, Any]] = None
    
    # Error handling
    error: Optional[str] = None
    
    # Task reference for cancellation
    task: Optional[asyncio.Task] = None


class JobManager:
    """
    Manages analysis jobs with in-memory storage.
    
    Thread-safe implementation using asyncio locks.
    Supports job lifecycle management, progress tracking, and cleanup.
    """
    
    # Agent execution order
    AGENT_ORDER = [
        AgentType.SUPERVISOR,
        AgentType.INVENTORY,
        AgentType.SALES,
        AgentType.MARKETING,
        AgentType.SUPPORT,
        AgentType.GENERAL,
        AgentType.SYNTHESIS,
        AgentType.REFLECTION,
    ]
    
    def __init__(self, max_jobs: int = 1000, retention_hours: int = 24):
        """
        Initialize the job manager.
        
        Args:
            max_jobs: Maximum number of jobs to keep in memory
            retention_hours: How long to keep completed jobs
        """
        self._jobs: OrderedDict[str, Job] = OrderedDict()
        self._lock = asyncio.Lock()
        self._max_jobs = max_jobs
        self._retention_hours = retention_hours
        
        logger.info(f"JobManager initialized (max_jobs={max_jobs}, retention={retention_hours}h)")
    
    def _generate_job_id(self) -> str:
        """Generate a unique job ID."""
        return f"job_{uuid.uuid4().hex[:12]}"
    
    async def create_job(
        self, 
        question: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Job:
        """
        Create a new analysis job.
        
        Args:
            question: The business question to analyze
            context: Optional analysis context
            
        Returns:
            Job: The created job instance
        """
        async with self._lock:
            # Cleanup old jobs if at capacity
            await self._cleanup_old_jobs_unsafe()
            
            job_id = self._generate_job_id()
            now = datetime.utcnow()
            
            # Initialize agent progress
            agent_progress = {}
            for agent in self.AGENT_ORDER:
                agent_progress[agent.value] = AgentProgress(
                    agent=agent,
                    status="pending",
                    started_at=None,
                    completed_at=None,
                    findings_summary=None
                )
            
            job = Job(
                job_id=job_id,
                question=question,
                context=context,
                status=JobStatus.PENDING,
                created_at=now,
                updated_at=now,
                agent_progress=agent_progress
            )
            
            self._jobs[job_id] = job
            
            logger.info(f"Created job {job_id}: {question[:50]}...")
            
            return job
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a job by ID.
        
        Args:
            job_id: The job identifier
            
        Returns:
            Optional[Job]: The job if found, None otherwise
        """
        async with self._lock:
            return self._jobs.get(job_id)
    
    async def get_all_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[List[Job], int]:
        """
        Get all jobs with optional filtering.
        
        Args:
            status: Filter by job status
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            tuple: (list of jobs, total count)
        """
        async with self._lock:
            # Filter jobs
            jobs = list(self._jobs.values())
            
            if status:
                jobs = [j for j in jobs if j.status == status]
            
            # Sort by created_at descending (newest first)
            jobs.sort(key=lambda j: j.created_at, reverse=True)
            
            total = len(jobs)
            
            # Apply pagination
            jobs = jobs[offset:offset + limit]
            
            return jobs, total
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: JobStatus,
        error: Optional[str] = None
    ) -> Optional[Job]:
        """
        Update job status.
        
        Args:
            job_id: The job identifier
            status: New job status
            error: Optional error message
            
        Returns:
            Optional[Job]: Updated job if found
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            
            job.status = status
            job.updated_at = datetime.utcnow()
            
            if error:
                job.error = error
            
            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job.completed_at = datetime.utcnow()
            
            logger.info(f"Job {job_id} status updated to {status.value}")
            
            return job
    
    async def start_agent(self, job_id: str, agent: AgentType) -> Optional[Job]:
        """
        Mark an agent as started.
        
        Args:
            job_id: The job identifier
            agent: The agent type starting
            
        Returns:
            Optional[Job]: Updated job if found
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            
            job.current_agent = agent
            job.status = JobStatus.RUNNING
            job.updated_at = datetime.utcnow()
            
            if agent.value in job.agent_progress:
                job.agent_progress[agent.value].status = "running"
                job.agent_progress[agent.value].started_at = datetime.utcnow()
            
            logger.debug(f"Job {job_id}: Agent {agent.value} started")
            
            return job
    
    async def complete_agent(
        self,
        job_id: str,
        agent: AgentType,
        findings: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None
    ) -> Optional[Job]:
        """
        Mark an agent as completed.
        
        Args:
            job_id: The job identifier
            agent: The agent type that completed
            findings: Agent findings
            summary: Brief summary of findings
            
        Returns:
            Optional[Job]: Updated job if found
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            
            # Update agent progress
            if agent.value in job.agent_progress:
                job.agent_progress[agent.value].status = "completed"
                job.agent_progress[agent.value].completed_at = datetime.utcnow()
                job.agent_progress[agent.value].findings_summary = summary
            
            # Add to completed agents
            if agent not in job.completed_agents:
                job.completed_agents.append(agent)
            
            # Store findings
            if findings:
                job.agent_findings[agent.value] = findings
            
            # Clear current agent
            job.current_agent = None
            job.updated_at = datetime.utcnow()
            
            logger.debug(f"Job {job_id}: Agent {agent.value} completed")
            
            return job
    
    async def set_root_cause(
        self, 
        job_id: str, 
        root_cause: Dict[str, Any]
    ) -> Optional[Job]:
        """
        Set the root cause analysis result.
        
        Args:
            job_id: The job identifier
            root_cause: Root cause analysis result
            
        Returns:
            Optional[Job]: Updated job if found
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            
            job.root_cause = root_cause
            job.updated_at = datetime.utcnow()
            
            logger.debug(f"Job {job_id}: Root cause set")
            
            return job
    
    async def set_reflection(
        self, 
        job_id: str, 
        reflection: Dict[str, Any]
    ) -> Optional[Job]:
        """
        Set the reflection analysis result.
        
        Args:
            job_id: The job identifier
            reflection: Reflection analysis result
            
        Returns:
            Optional[Job]: Updated job if found
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            
            job.reflection = reflection
            job.updated_at = datetime.utcnow()
            
            logger.debug(f"Job {job_id}: Reflection set")
            
            return job
    
    async def set_task(self, job_id: str, task: asyncio.Task) -> Optional[Job]:
        """
        Associate an asyncio task with a job.
        
        Args:
            job_id: The job identifier
            task: The asyncio task
            
        Returns:
            Optional[Job]: Updated job if found
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.task = task
            return job
    
    async def cancel_job(self, job_id: str) -> Optional[Job]:
        """
        Cancel a running job.
        
        Args:
            job_id: The job identifier
            
        Returns:
            Optional[Job]: Cancelled job if found and cancellable
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            
            # Can only cancel pending or running jobs
            if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
                logger.warning(f"Cannot cancel job {job_id} with status {job.status}")
                return job
            
            # Cancel the task if it exists
            if job.task and not job.task.done():
                job.task.cancel()
                logger.info(f"Cancelled task for job {job_id}")
            
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            
            logger.info(f"Job {job_id} cancelled")
            
            return job
    
    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from storage.
        
        Args:
            job_id: The job identifier
            
        Returns:
            bool: True if deleted, False if not found
        """
        async with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                
                # Cancel task if running
                if job.task and not job.task.done():
                    job.task.cancel()
                
                del self._jobs[job_id]
                logger.info(f"Job {job_id} deleted")
                return True
            
            return False
    
    async def _cleanup_old_jobs_unsafe(self) -> int:
        """
        Clean up old completed jobs. Must be called with lock held.
        
        Returns:
            int: Number of jobs cleaned up
        """
        cutoff = datetime.utcnow() - timedelta(hours=self._retention_hours)
        cleaned = 0
        
        # Find jobs to delete
        to_delete = []
        for job_id, job in self._jobs.items():
            if job.completed_at and job.completed_at < cutoff:
                to_delete.append(job_id)
        
        # Also cleanup if over max_jobs (remove oldest completed first)
        if len(self._jobs) >= self._max_jobs:
            completed_jobs = [
                (jid, j) for jid, j in self._jobs.items() 
                if j.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
            ]
            completed_jobs.sort(key=lambda x: x[1].completed_at or x[1].created_at)
            
            excess = len(self._jobs) - self._max_jobs + 10  # Keep some buffer
            for jid, _ in completed_jobs[:excess]:
                if jid not in to_delete:
                    to_delete.append(jid)
        
        # Delete jobs
        for job_id in to_delete:
            del self._jobs[job_id]
            cleaned += 1
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old jobs")
        
        return cleaned
    
    def get_job_progress(self, job: Job) -> JobProgress:
        """
        Calculate job progress information.
        
        Args:
            job: The job instance
            
        Returns:
            JobProgress: Progress information
        """
        completed = len(job.completed_agents)
        total = len(self.AGENT_ORDER)
        percentage = int((completed / total) * 100) if total > 0 else 0
        
        pending_agents = [
            agent for agent in self.AGENT_ORDER 
            if agent not in job.completed_agents and agent != job.current_agent
        ]
        
        agent_details = [
            job.agent_progress.get(agent.value, AgentProgress(
                agent=agent,
                status="pending",
                started_at=None,
                completed_at=None,
                findings_summary=None
            ))
            for agent in self.AGENT_ORDER
        ]
        
        return JobProgress(
            current_agent=job.current_agent,
            completed_agents=job.completed_agents,
            pending_agents=pending_agents,
            percentage=percentage,
            agent_details=agent_details
        )
    
    def job_to_response(self, job: Job) -> Dict[str, Any]:
        """
        Convert a Job to API response format.
        
        Args:
            job: The job instance
            
        Returns:
            Dict: Response-ready job data
        """
        progress = None
        if job.status == JobStatus.RUNNING:
            progress = self.get_job_progress(job)
        
        # Build result if job is completed
        result = None
        if job.status == JobStatus.COMPLETED:
            result = {
                "question": job.question,
                "agent_findings": job.agent_findings or {},
                "root_cause": job.root_cause,
                "reflection": job.reflection
            }
        
        return {
            "job_id": job.job_id,
            "status": job.status,
            "progress": progress.model_dump() if progress else None,
            "result": result,
            "error": job.error,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "completed_at": job.completed_at
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get job manager statistics.
        
        Returns:
            Dict: Statistics about jobs
        """
        async with self._lock:
            total = len(self._jobs)
            by_status = {}
            
            for job in self._jobs.values():
                status = job.status.value
                by_status[status] = by_status.get(status, 0) + 1
            
            return {
                "total_jobs": total,
                "max_jobs": self._max_jobs,
                "by_status": by_status,
                "retention_hours": self._retention_hours
            }


# Singleton instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """
    Get the singleton JobManager instance.
    
    Returns:
        JobManager: The job manager instance
    """
    global _job_manager
    
    if _job_manager is None:
        settings = get_api_settings()
        _job_manager = JobManager(
            max_jobs=1000,
            retention_hours=settings.job_retention_hours
        )
    
    return _job_manager