"""
Analysis Service

Bridges the API layer with the LangGraph workflow.
Handles job execution, progress updates, and result processing.
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import traceback

from loguru import logger

from backend.api.schemas import JobStatus, AgentType
from backend.api.services.job_manager import JobManager, Job, get_job_manager
from backend.api.config import get_api_settings


class AnalysisService:
    """
    Service for executing analysis workflows.
    
    Manages the execution of LangGraph workflows and updates job progress.
    """
    
    def __init__(self, job_manager: JobManager):
        """
        Initialize the analysis service.
        
        Args:
            job_manager: JobManager instance for job state management
        """
        self.job_manager = job_manager
        self._settings = get_api_settings()
        
        # WebSocket callbacks for real-time updates
        self._progress_callbacks: Dict[str, Callable] = {}
        
        # Check if LangGraph is available
        self._langgraph_available = self._check_langgraph_available()
        
        logger.info(f"AnalysisService initialized (LangGraph available: {self._langgraph_available})")
    
    def _check_langgraph_available(self) -> bool:
        """
        Check if LangGraph is properly configured and available.
        
        Uses the singleton GraphManager to avoid redundant initialization.
        The graph is built only once and reused across all requests.
        
        Returns:
            bool: True if LangGraph can be used
        """
        try:
            from backend.graph import get_graph_manager, GraphManager
            
            # Check if already initialized (fast path)
            if GraphManager.is_initialized():
                return True
            
            # Initialize the graph manager (this builds the graph once)
            manager = get_graph_manager()
            return manager.graph is not None
        except Exception as e:
            logger.warning(f"LangGraph not available: {e}")
            return False
    
    def register_progress_callback(
        self, 
        job_id: str, 
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """
        Register a callback for job progress updates.
        
        Args:
            job_id: The job identifier
            callback: Callback function(event_type, data)
        """
        self._progress_callbacks[job_id] = callback
        logger.debug(f"Registered progress callback for job {job_id}")
    
    def unregister_progress_callback(self, job_id: str) -> None:
        """
        Unregister a progress callback.
        
        Args:
            job_id: The job identifier
        """
        if job_id in self._progress_callbacks:
            del self._progress_callbacks[job_id]
            logger.debug(f"Unregistered progress callback for job {job_id}")
    
    async def _notify_progress(
        self, 
        job_id: str, 
        event_type: str, 
        data: Dict[str, Any]
    ) -> None:
        """
        Notify registered callbacks of progress updates.
        
        Args:
            job_id: The job identifier
            event_type: Type of event
            data: Event data
        """
        if job_id in self._progress_callbacks:
            try:
                callback = self._progress_callbacks[job_id]
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.warning(f"Progress callback error for job {job_id}: {e}")
    
    async def submit_analysis(
        self, 
        question: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Job:
        """
        Submit a new analysis job.
        
        Args:
            question: The business question to analyze
            context: Optional analysis context
            
        Returns:
            Job: The created job instance
        """
        # Create job
        job = await self.job_manager.create_job(question, context)
        
        # Start background task
        task = asyncio.create_task(
            self._run_analysis(job.job_id),
            name=f"analysis_{job.job_id}"
        )
        
        # Store task reference
        await self.job_manager.set_task(job.job_id, task)
        
        # Add callback to handle task completion
        task.add_done_callback(
            lambda t: asyncio.create_task(self._handle_task_done(job.job_id, t))
        )
        
        logger.info(f"Analysis submitted: {job.job_id}")
        
        return job
    
    async def _handle_task_done(self, job_id: str, task: asyncio.Task) -> None:
        """
        Handle task completion/cancellation/error.
        
        Args:
            job_id: The job identifier
            task: The completed task
        """
        try:
            # Check if task was cancelled
            if task.cancelled():
                await self.job_manager.update_job_status(
                    job_id, 
                    JobStatus.CANCELLED
                )
                await self._notify_progress(job_id, "job_cancelled", {
                    "job_id": job_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                return
            
            # Check for exceptions
            exception = task.exception()
            if exception:
                error_msg = f"{type(exception).__name__}: {str(exception)}"
                logger.error(f"Task exception for job {job_id}: {error_msg}")
                await self.job_manager.update_job_status(
                    job_id, 
                    JobStatus.FAILED,
                    error=error_msg
                )
                await self._notify_progress(job_id, "job_failed", {
                    "job_id": job_id,
                    "error": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except asyncio.CancelledError:
            pass
        except asyncio.InvalidStateError:
            # Task completed normally
            pass
        except Exception as e:
            logger.error(f"Error handling task done for {job_id}: {e}")
    
    async def _run_analysis(self, job_id: str) -> None:
        """
        Run the analysis workflow for a job.
        
        Args:
            job_id: The job identifier
        """
        logger.info(f"Starting analysis for job {job_id}")
        
        try:
            # Get job details
            job = await self.job_manager.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            # Update status to running
            await self.job_manager.update_job_status(job_id, JobStatus.RUNNING)
            await self._notify_progress(job_id, "job_started", {
                "job_id": job_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Always use real LangGraph workflow
            logger.info(f"Running LangGraph workflow for job {job_id}")
            await self._run_langgraph_workflow(job_id, job.question, job.context)
            
            # Mark as completed
            await self.job_manager.update_job_status(job_id, JobStatus.COMPLETED)
            await self._notify_progress(job_id, "job_completed", {
                "job_id": job_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Analysis completed for job {job_id}")
            
        except asyncio.CancelledError:
            logger.info(f"Analysis cancelled for job {job_id}")
            raise
            
        except Exception as e:
            logger.error(f"Analysis failed for job {job_id}: {e}\n{traceback.format_exc()}")
            await self.job_manager.update_job_status(
                job_id, 
                JobStatus.FAILED,
                error=str(e)
            )
            await self._notify_progress(job_id, "job_failed", {
                "job_id": job_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _run_langgraph_workflow(
        self, 
        job_id: str, 
        question: str,
        context: Optional[Dict[str, Any]]
    ) -> None:
        """
        Run the actual LangGraph workflow.
        
        Args:
            job_id: The job identifier
            question: The business question
            context: Optional context
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        try:
            from backend.graph import run_graph
            
            # Run LangGraph in a thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                final_state = await loop.run_in_executor(
                    executor, 
                    run_graph, 
                    question
                )
            
            # Check for errors in the graph execution
            if final_state.get("error"):
                raise RuntimeError(f"Graph execution error: {final_state['error']}")
            
            # Extract results from final state
            agent_outputs = final_state.get("agent_outputs", {})
            root_cause = final_state.get("root_cause", {})
            reflection_result = final_state.get("reflection_result", {})
            
            # Update job with agent findings
            for agent_name, output in agent_outputs.items():
                try:
                    agent_type = AgentType(agent_name)
                    summary = output.get("finding", "Analysis completed") if isinstance(output, dict) else str(output)
                    
                    await self.job_manager.start_agent(job_id, agent_type)
                    await self._notify_progress(job_id, "agent_started", {
                        "agent": agent_name,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    await self.job_manager.complete_agent(
                        job_id,
                        agent_type,
                        findings=output if isinstance(output, dict) else {"output": output},
                        summary=summary[:200] if summary else None
                    )
                    await self._notify_progress(job_id, "agent_completed", {
                        "agent": agent_name,
                        "summary": summary[:100] if summary else None,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except ValueError:
                    # Skip non-standard agent names
                    logger.debug(f"Skipping non-standard agent: {agent_name}")
            
            # Set root cause
            if root_cause:
                await self.job_manager.set_root_cause(job_id, root_cause)
            
            # Set reflection
            if reflection_result:
                await self.job_manager.set_reflection(job_id, reflection_result)
            
            logger.info(f"LangGraph workflow completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"LangGraph workflow failed for job {job_id}: {e}")
            # Re-raise the exception instead of falling back to mock
            raise RuntimeError(f"LangGraph workflow failed: {e}")


# Singleton instance
_analysis_service: Optional[AnalysisService] = None


def get_analysis_service() -> AnalysisService:
    """
    Get the singleton AnalysisService instance.
    
    Returns:
        AnalysisService: The analysis service instance
    """
    global _analysis_service
    
    if _analysis_service is None:
        _analysis_service = AnalysisService(get_job_manager())
    
    return _analysis_service