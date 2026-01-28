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
        
        Returns:
            bool: True if LangGraph can be used
        """
        try:
            from backend.graph import create_graph
            # Try to create the graph
            graph = create_graph()
            return True
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
            
            # Always use mock analysis for now until graph is properly integrated
            # You can change this once your graph.py is ready
            logger.info(f"Running mock analysis for job {job_id}")
            await self._run_mock_analysis(job_id, job.question)
            
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
        # This will be implemented when graph.py is properly set up
        # For now, fall back to mock analysis
        logger.warning("LangGraph workflow not yet implemented, using mock")
        await self._run_mock_analysis(job_id, question)
    
    async def _run_mock_analysis(self, job_id: str, question: str) -> None:
        """
        Run a mock analysis for testing when LangGraph is not available.
        
        Args:
            job_id: The job identifier
            question: The business question
        """
        logger.info(f"Running mock analysis for job {job_id}")
        
        # Simulate agent execution
        agents = [
            (AgentType.SUPERVISOR, "Classified intent as operational_issue", 0.5),
            (AgentType.INVENTORY, "Found 3 products with low stock levels", 1.0),
            (AgentType.SALES, "Detected 40% decrease in daily revenue", 1.0),
            (AgentType.MARKETING, "Campaign performance dropped 25%", 0.8),
            (AgentType.SUPPORT, "Ticket volume increased by 60%", 0.7),
            (AgentType.SYNTHESIS, "Root cause: Supply chain disruption", 1.0),
            (AgentType.REFLECTION, "Analysis quality score: 0.85", 0.5),
        ]
        
        for agent, summary, delay in agents:
            # Check for cancellation
            job = await self.job_manager.get_job(job_id)
            if not job or job.status == JobStatus.CANCELLED:
                logger.info(f"Job {job_id} was cancelled, stopping mock analysis")
                return
            
            # Start agent
            await self.job_manager.start_agent(job_id, agent)
            await self._notify_progress(job_id, "agent_started", {
                "agent": agent.value,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Simulate processing time
            await asyncio.sleep(delay)
            
            # Generate mock findings
            findings = self._generate_mock_findings(agent, question)
            
            # Complete agent
            await self.job_manager.complete_agent(
                job_id,
                agent,
                findings=findings,
                summary=summary
            )
            await self._notify_progress(job_id, "agent_completed", {
                "agent": agent.value,
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Set mock root cause
        root_cause = {
            "primary_cause": "Supply chain disruption affecting key product availability",
            "explanation": f"Based on analysis of the question: '{question[:100]}...', we identified that recent supply chain issues have led to stockouts of high-demand products, directly impacting sales performance.",
            "contributing_factors": [
                {
                    "factor": "Low inventory levels for top 3 selling products",
                    "impact": "high",
                    "source_agent": "inventory",
                    "confidence": 0.92
                },
                {
                    "factor": "Marketing campaigns driving demand for out-of-stock items",
                    "impact": "medium",
                    "source_agent": "marketing",
                    "confidence": 0.78
                },
                {
                    "factor": "Increased customer complaints about product availability",
                    "impact": "medium",
                    "source_agent": "support",
                    "confidence": 0.85
                }
            ],
            "confidence_score": 0.87,
            "affected_areas": ["inventory", "sales", "customer_satisfaction"],
            "timeline": "Issues began approximately 5 days ago with gradual escalation"
        }
        await self.job_manager.set_root_cause(job_id, root_cause)
        
        # Set mock reflection
        reflection = {
            "quality_score": 0.85,
            "issues_found": [
                {
                    "issue_type": "data_gap",
                    "description": "Limited historical data for seasonal comparison",
                    "severity": "low",
                    "affected_agent": "sales"
                }
            ],
            "recommendations": [
                "Consider extending analysis time range for better context",
                "Cross-reference with supplier delivery data if available"
            ],
            "confidence_assessment": "High confidence in primary root cause identification",
            "reasoning_gaps": [
                "Unable to determine if competitor actions contributed to sales drop"
            ]
        }
        await self.job_manager.set_reflection(job_id, reflection)
        
        logger.info(f"Mock analysis completed for job {job_id}")
    
    def _generate_mock_findings(
        self, 
        agent: AgentType, 
        question: str
    ) -> Dict[str, Any]:
        """
        Generate mock findings for an agent.
        
        Args:
            agent: The agent type
            question: The business question
            
        Returns:
            Dict: Mock findings
        """
        mock_findings = {
            AgentType.SUPERVISOR: {
                "intent": "operational_issue",
                "confidence": 0.95,
                "routing": ["inventory", "sales", "marketing", "support"],
                "question_analysis": {
                    "type": "root_cause_analysis",
                    "urgency": "high",
                    "domain": "sales_operations"
                }
            },
            AgentType.INVENTORY: {
                "findings": [
                    {
                        "finding_id": "INV-001",
                        "category": "stockout",
                        "description": "Product SKU-1234 (Wireless Headphones) has 0 units in stock",
                        "severity": "high",
                        "confidence": 0.95,
                        "evidence": [
                            "Last stock update: 3 days ago",
                            "Pending orders: 45",
                            "Average daily sales: 15 units"
                        ],
                        "metrics": {
                            "current_stock": 0,
                            "pending_orders": 45,
                            "days_out_of_stock": 3
                        }
                    },
                    {
                        "finding_id": "INV-002",
                        "category": "low_stock",
                        "description": "Product SKU-5678 (Bluetooth Speaker) below reorder point",
                        "severity": "medium",
                        "confidence": 0.88,
                        "evidence": [
                            "Current stock: 12 units",
                            "Reorder point: 50 units",
                            "Lead time: 7 days"
                        ],
                        "metrics": {
                            "current_stock": 12,
                            "reorder_point": 50,
                            "lead_time_days": 7
                        }
                    },
                    {
                        "finding_id": "INV-003",
                        "category": "low_stock",
                        "description": "Product SKU-9012 (USB-C Cable) approaching stockout",
                        "severity": "medium",
                        "confidence": 0.82,
                        "evidence": [
                            "Current stock: 25 units",
                            "Daily sales velocity: 8 units"
                        ],
                        "metrics": {
                            "current_stock": 25,
                            "daily_velocity": 8,
                            "days_of_stock": 3
                        }
                    }
                ],
                "summary": "Found 3 products with critical stock issues affecting sales",
                "confidence_score": 0.92,
                "recommendations": [
                    "Expedite reorder for SKU-1234",
                    "Place emergency order for SKU-5678",
                    "Monitor SKU-9012 daily"
                ]
            },
            AgentType.SALES: {
                "findings": [
                    {
                        "finding_id": "SAL-001",
                        "category": "revenue_drop",
                        "description": "Daily revenue decreased 40% compared to last week average",
                        "severity": "critical",
                        "confidence": 0.97,
                        "evidence": [
                            "Yesterday revenue: $12,450",
                            "Last week daily average: $20,750",
                            "Variance: -$8,300 (-40%)"
                        ],
                        "metrics": {
                            "yesterday_revenue": 12450,
                            "last_week_avg": 20750,
                            "variance_percent": -40
                        }
                    },
                    {
                        "finding_id": "SAL-002",
                        "category": "order_volume",
                        "description": "Order count dropped 35% from baseline",
                        "severity": "high",
                        "confidence": 0.94,
                        "evidence": [
                            "Yesterday orders: 156",
                            "Normal daily orders: 240"
                        ],
                        "metrics": {
                            "yesterday_orders": 156,
                            "baseline_orders": 240,
                            "variance_percent": -35
                        }
                    },
                    {
                        "finding_id": "SAL-003",
                        "category": "conversion_rate",
                        "description": "Cart abandonment rate increased to 78%",
                        "severity": "high",
                        "confidence": 0.89,
                        "evidence": [
                            "Current abandonment: 78%",
                            "Normal abandonment: 65%",
                            "Top reason: 'Item unavailable'"
                        ],
                        "metrics": {
                            "current_abandonment": 78,
                            "normal_abandonment": 65,
                            "increase_percent": 20
                        }
                    }
                ],
                "summary": "Significant revenue decline of 40% with increased cart abandonment",
                "confidence_score": 0.94,
                "time_range_analyzed": "last_7_days"
            },
            AgentType.MARKETING: {
                "findings": [
                    {
                        "finding_id": "MKT-001",
                        "category": "campaign_performance",
                        "description": "Email campaign click-through rate dropped 25%",
                        "severity": "medium",
                        "confidence": 0.82,
                        "evidence": [
                            "Current CTR: 2.1%",
                            "Previous CTR: 2.8%",
                            "Campaign: 'Summer Sale'"
                        ],
                        "metrics": {
                            "current_ctr": 2.1,
                            "previous_ctr": 2.8,
                            "variance_percent": -25
                        }
                    },
                    {
                        "finding_id": "MKT-002",
                        "category": "traffic_source",
                        "description": "Paid search traffic converting at lower rate",
                        "severity": "low",
                        "confidence": 0.75,
                        "evidence": [
                            "Paid conversion: 1.8%",
                            "Organic conversion: 3.2%"
                        ],
                        "metrics": {
                            "paid_conversion": 1.8,
                            "organic_conversion": 3.2
                        }
                    }
                ],
                "summary": "Marketing campaigns showing reduced effectiveness, possibly due to inventory issues",
                "confidence_score": 0.78,
                "active_campaigns": ["Summer Sale", "Newsletter Weekly"]
            },
            AgentType.SUPPORT: {
                "findings": [
                    {
                        "finding_id": "SUP-001",
                        "category": "ticket_volume",
                        "description": "Support ticket volume increased 60% in last 48 hours",
                        "severity": "high",
                        "confidence": 0.91,
                        "evidence": [
                            "Current tickets (48h): 156",
                            "Normal tickets (48h): 97",
                            "Increase: 59 tickets"
                        ],
                        "metrics": {
                            "current_volume": 156,
                            "normal_volume": 97,
                            "increase_percent": 60
                        }
                    },
                    {
                        "finding_id": "SUP-002",
                        "category": "complaint_category",
                        "description": "68% of tickets mention product availability issues",
                        "severity": "high",
                        "confidence": 0.88,
                        "evidence": [
                            "Availability complaints: 106 tickets",
                            "Keywords: 'out of stock', 'unavailable', 'when back'",
                            "Top products mentioned: SKU-1234, SKU-5678"
                        ],
                        "metrics": {
                            "availability_tickets": 106,
                            "total_tickets": 156,
                            "percentage": 68
                        }
                    },
                    {
                        "finding_id": "SUP-003",
                        "category": "sentiment",
                        "description": "Customer sentiment score dropped to 3.2/5",
                        "severity": "medium",
                        "confidence": 0.85,
                        "evidence": [
                            "Current sentiment: 3.2/5",
                            "Previous sentiment: 4.1/5",
                            "Main complaints: stock availability"
                        ],
                        "metrics": {
                            "current_sentiment": 3.2,
                            "previous_sentiment": 4.1,
                            "scale": 5
                        }
                    }
                ],
                "summary": "Support volume surge primarily driven by product availability complaints",
                "confidence_score": 0.89,
                "avg_response_time_hours": 4.2
            },
            AgentType.SYNTHESIS: {
                "synthesis_complete": True,
                "agents_analyzed": ["inventory", "sales", "marketing", "support"],
                "cross_correlations_found": 3,
                "primary_pattern": "inventory_shortage_cascade"
            },
            AgentType.REFLECTION: {
                "reflection_complete": True,
                "quality_validated": True,
                "confidence_calibrated": True,
                "reasoning_chain_verified": True
            }
        }
        
        return mock_findings.get(agent, {"status": "completed", "agent": agent.value})


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