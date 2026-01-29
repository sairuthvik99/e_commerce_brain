"""
WebSocket Endpoints

Real-time updates for analysis job progress via WebSocket connections.
"""

import asyncio
from typing import Dict, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from loguru import logger

from backend.api.services.job_manager import JobManager, get_job_manager
from backend.api.services.analysis_service import AnalysisService, get_analysis_service
from backend.api.schemas import JobStatus


router = APIRouter()


# ============================================================
# WebSocket Connection Manager
# ============================================================

class ConnectionManager:
    """Manages active WebSocket connections for job progress updates."""
    
    def __init__(self):
        # Map of job_id -> set of active websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # All connected websockets (for broadcast)
        self.all_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, job_id: str = None):
        """
        Accept a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            job_id: Optional job ID to subscribe to specific job updates
        """
        await websocket.accept()
        self.all_connections.add(websocket)
        
        if job_id:
            if job_id not in self.active_connections:
                self.active_connections[job_id] = set()
            self.active_connections[job_id].add(websocket)
        
        logger.info(f"WebSocket connected. Job: {job_id}, Total: {len(self.all_connections)}")
    
    def disconnect(self, websocket: WebSocket, job_id: str = None):
        """Remove a WebSocket connection."""
        self.all_connections.discard(websocket)
        
        if job_id and job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        
        logger.info(f"WebSocket disconnected. Remaining: {len(self.all_connections)}")
    
    async def send_to_job(self, job_id: str, message: dict):
        """Send a message to all connections subscribed to a job."""
        if job_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.disconnect(conn, job_id)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.all_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)


# Singleton connection manager
_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the singleton ConnectionManager."""
    return _manager


# ============================================================
# WebSocket Endpoints
# ============================================================

@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_progress(
    websocket: WebSocket,
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager)
):
    """
    WebSocket endpoint for real-time job progress updates.
    
    Connect to receive updates for a specific job:
    - Agent started/completed events
    - Progress percentage updates
    - Job completion/failure notifications
    
    Example client code:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/jobs/job_abc123');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Update:', data);
    };
    ```
    """
    manager = get_connection_manager()
    await manager.connect(websocket, job_id)
    
    try:
        # Send initial job status
        job = await job_manager.get_job(job_id)
        if job:
            await websocket.send_json({
                "type": "initial_status",
                "job_id": job_id,
                "status": job.status.value,
                "current_agent": job.current_agent.value if job.current_agent else None,
                "completed_agents": [a.value for a in job.completed_agents],
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Job {job_id} not found",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Keep connection alive and listen for messages
        while True:
            try:
                # Wait for any client message (ping/pong or control messages)
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # Send ping every 30 seconds
                )
                
                # Handle client messages
                if message == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message == "status":
                    # Send current status on demand
                    job = await job_manager.get_job(job_id)
                    if job:
                        progress = job_manager.get_job_progress(job)
                        await websocket.send_json({
                            "type": "status",
                            "job_id": job_id,
                            "status": job.status.value,
                            "progress": progress.model_dump() if progress else None,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
            except asyncio.TimeoutError:
                # Send periodic ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        manager.disconnect(websocket, job_id)


@router.websocket("/ws/jobs")
async def websocket_all_jobs(websocket: WebSocket):
    """
    WebSocket endpoint for all job updates.
    
    Connect to receive updates for all jobs:
    - New job created
    - Job status changes
    - Job completions
    
    Useful for dashboards monitoring all activity.
    """
    manager = get_connection_manager()
    await manager.connect(websocket)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Subscribed to all job updates",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                if message == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
                    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected from all jobs feed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


# ============================================================
# Helper Functions for Sending Updates
# ============================================================

async def notify_job_progress(
    job_id: str,
    event_type: str,
    data: dict
):
    """
    Send a progress update to all WebSocket clients subscribed to a job.
    
    This function should be called from the analysis service when
    progress events occur.
    
    Args:
        job_id: The job identifier
        event_type: Type of event (agent_started, agent_completed, etc.)
        data: Event data
    """
    manager = get_connection_manager()
    
    message = {
        "type": event_type,
        "job_id": job_id,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Send to job-specific subscribers
    await manager.send_to_job(job_id, message)
    
    # Also broadcast to all-jobs subscribers
    await manager.broadcast(message)


async def notify_job_created(job_id: str, question: str):
    """Notify about a new job creation."""
    await notify_job_progress(job_id, "job_created", {
        "question": question[:100]
    })


async def notify_job_completed(job_id: str, result_summary: str = None):
    """Notify about job completion."""
    await notify_job_progress(job_id, "job_completed", {
        "result_summary": result_summary
    })


async def notify_job_failed(job_id: str, error: str):
    """Notify about job failure."""
    await notify_job_progress(job_id, "job_failed", {
        "error": error
    })
