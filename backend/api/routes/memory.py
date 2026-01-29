"""
Memory Endpoints

Endpoints for searching similar past analyses and retrieving historical context.
"""

from typing import Optional, Any, Dict, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from backend.api.config import APISettings, get_settings


# ============================================================
# Memory Request/Response Schemas
# ============================================================

class SimilarAnalysis(BaseModel):
    """A similar past analysis result."""
    question: str = Field(..., description="Original question")
    intent: str = Field(default="", description="Detected intent")
    root_cause: Optional[Dict[str, Any]] = Field(None, description="Root cause analysis")
    primary_cause: Optional[str] = Field(None, description="Primary cause identified")
    confidence: float = Field(default=0.0, description="Confidence score")
    timestamp: Optional[str] = Field(None, description="When analysis was performed")
    actions_taken: Optional[List[Dict[str, Any]]] = Field(None, description="Actions that were taken")
    outcome: Optional[str] = Field(None, description="Outcome of actions")
    similarity_score: Optional[float] = Field(None, description="How similar to query")


class MemorySearchRequest(BaseModel):
    """Request for searching memory."""
    query: str = Field(..., min_length=5, description="Search query")
    limit: int = Field(default=5, ge=1, le=20, description="Max results to return")
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum confidence filter")


class MemorySearchResponse(BaseModel):
    """Response from memory search."""
    query: str
    results: List[SimilarAnalysis]
    total_found: int
    message: str


class MemoryInsight(BaseModel):
    """An insight derived from historical memory."""
    insight_type: str = Field(..., description="Type: pattern, recommendation, warning")
    description: str = Field(..., description="Human-readable insight")
    confidence: float = Field(default=0.0)
    source_count: int = Field(default=0, description="How many past analyses support this")
    related_actions: Optional[List[str]] = Field(None)


class MemoryInsightsResponse(BaseModel):
    """Response containing derived insights from memory."""
    question: str
    insights: List[MemoryInsight]
    similar_situations_count: int
    most_effective_action: Optional[str] = None
    success_rate: Optional[float] = None


router = APIRouter()


# ============================================================
# Memory Helper Functions
# ============================================================

def _get_history_store():
    """Get the HistoryStore instance."""
    try:
        from backend.vector_db.history_store import HistoryStore
        return HistoryStore()
    except Exception as e:
        logger.warning(f"Failed to initialize HistoryStore: {e}")
        return None


def _derive_insights(analyses: List[SimilarAnalysis]) -> List[MemoryInsight]:
    """Derive insights from similar past analyses."""
    insights = []
    
    if not analyses:
        return insights
    
    # Pattern: Most common root cause
    causes = {}
    for a in analyses:
        if a.primary_cause:
            cause_key = a.primary_cause.lower()[:50]
            causes[cause_key] = causes.get(cause_key, 0) + 1
    
    if causes:
        most_common = max(causes, key=causes.get)
        insights.append(MemoryInsight(
            insight_type="pattern",
            description=f"Most common cause in similar situations: {most_common}",
            confidence=causes[most_common] / len(analyses),
            source_count=causes[most_common]
        ))
    
    # Pattern: Most effective action
    action_success = {}
    for a in analyses:
        if a.actions_taken:
            for action in a.actions_taken:
                if action.get("result") == "success":
                    action_type = action.get("action", "unknown")
                    action_success[action_type] = action_success.get(action_type, 0) + 1
    
    if action_success:
        best_action = max(action_success, key=action_success.get)
        insights.append(MemoryInsight(
            insight_type="recommendation",
            description=f"Most effective action historically: {best_action}",
            confidence=action_success[best_action] / len(analyses),
            source_count=action_success[best_action],
            related_actions=[best_action]
        ))
    
    # Warning: Low confidence patterns
    low_conf = [a for a in analyses if a.confidence < 0.75]
    if len(low_conf) > len(analyses) / 2:
        insights.append(MemoryInsight(
            insight_type="warning",
            description="Similar past situations had uncertain diagnoses. Consider gathering more data.",
            confidence=0.7,
            source_count=len(low_conf)
        ))
    
    return insights


# ============================================================
# Memory Endpoints
# ============================================================

@router.post(
    "/memory/search",
    response_model=MemorySearchResponse,
    summary="Search Similar Analyses",
    description="Search for similar past analyses using semantic search",
    responses={
        200: {"description": "Search results returned"},
        503: {"description": "Vector database unavailable"}
    }
)
async def search_similar_analyses(
    request: MemorySearchRequest,
    settings: APISettings = Depends(get_settings)
) -> MemorySearchResponse:
    """
    Search for similar past analyses.
    
    Uses semantic search over stored analysis history to find
    similar situations and their outcomes.
    
    Example queries:
    - "Why did sales drop yesterday?"
    - "Has this happened before?"
    - "What did we do last time sales dropped?"
    """
    logger.info(f"Memory search: '{request.query[:50]}...'")
    
    history_store = _get_history_store()
    
    if history_store:
        try:
            # Use real vector search
            raw_results = history_store.search_similar_analyses(
                request.query, 
                k=request.limit
            )
            
            # Convert to response format
            results = []
            for r in raw_results:
                analysis = SimilarAnalysis(
                    question=r.get("question", ""),
                    intent=r.get("intent", ""),
                    root_cause=r.get("root_cause"),
                    primary_cause=r.get("root_cause", {}).get("primary_cause") if r.get("root_cause") else None,
                    confidence=r.get("quality_score", r.get("confidence", 0.0)),
                    timestamp=r.get("timestamp"),
                    actions_taken=r.get("actions_taken"),
                    outcome=r.get("outcome")
                )
                
                # Filter by min confidence
                if analysis.confidence >= request.min_confidence:
                    results.append(analysis)
            
            return MemorySearchResponse(
                query=request.query,
                results=results,
                total_found=len(results),
                message=f"Found {len(results)} similar past analyses"
            )
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Vector database search failed: {str(e)}"
            )
    
    # Vector DB not available
    raise HTTPException(
        status_code=503,
        detail="Vector database is not configured or unavailable"
    )


@router.get(
    "/memory/search",
    response_model=MemorySearchResponse,
    summary="Search Similar Analyses (GET)",
    description="Search for similar past analyses using query parameters"
)
async def search_similar_analyses_get(
    query: str = Query(..., min_length=5, description="Search query"),
    limit: int = Query(5, ge=1, le=20),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    settings: APISettings = Depends(get_settings)
) -> MemorySearchResponse:
    """GET version of memory search for convenience."""
    request = MemorySearchRequest(
        query=query,
        limit=limit,
        min_confidence=min_confidence
    )
    return await search_similar_analyses(request, settings)


@router.get(
    "/memory/insights/{job_id}",
    response_model=MemoryInsightsResponse,
    summary="Get Memory Insights",
    description="Get insights derived from similar past analyses for a specific job",
    responses={
        200: {"description": "Insights retrieved"},
        404: {"description": "Job not found"}
    }
)
async def get_memory_insights(
    job_id: str,
    settings: APISettings = Depends(get_settings)
) -> MemoryInsightsResponse:
    """
    Get insights from historical memory for a specific analysis job.
    
    This endpoint:
    1. Retrieves the job's question
    2. Searches for similar past situations
    3. Derives patterns and recommendations
    """
    from backend.api.services.job_manager import get_job_manager
    
    job_manager = get_job_manager()
    job = await job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    
    # Search for similar analyses
    history_store = _get_history_store()
    
    if history_store:
        try:
            raw_results = history_store.search_similar_analyses(job.question, k=10)
            analyses = [
                SimilarAnalysis(
                    question=r.get("question", ""),
                    intent=r.get("intent", ""),
                    primary_cause=r.get("root_cause", {}).get("primary_cause") if r.get("root_cause") else None,
                    confidence=r.get("quality_score", 0.0),
                    timestamp=r.get("timestamp"),
                    actions_taken=r.get("actions_taken"),
                    outcome=r.get("outcome")
                )
                for r in raw_results
            ]
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            analyses = []
    else:
        analyses = []
    
    # Derive insights
    insights = _derive_insights(analyses)
    
    # Calculate success rate and most effective action
    most_effective = None
    success_rate = None
    
    if analyses:
        successful = sum(1 for a in analyses if a.outcome and "success" in a.outcome.lower())
        success_rate = successful / len(analyses)
        
        # Find most common successful action
        action_counts = {}
        for a in analyses:
            if a.actions_taken:
                for action in a.actions_taken:
                    if action.get("result") == "success":
                        action_type = action.get("action", "unknown")
                        action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        if action_counts:
            most_effective = max(action_counts, key=action_counts.get)
    
    return MemoryInsightsResponse(
        question=job.question,
        insights=insights,
        similar_situations_count=len(analyses),
        most_effective_action=most_effective,
        success_rate=success_rate
    )


@router.get(
    "/memory/stats",
    summary="Get Memory Statistics",
    description="Get statistics about stored analyses"
)
async def get_memory_stats() -> Dict[str, Any]:
    """Get statistics about the memory store."""
    history_store = _get_history_store()
    
    if history_store:
        try:
            # Get index stats from Pinecone
            stats = history_store.index.describe_index_stats()
            return {
                "status": "connected",
                "total_vectors": stats.get("total_vector_count", 0),
                "index_name": history_store.index_name,
                "dimensions": stats.get("dimension", "unknown")
            }
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
    
    return {
        "status": "unavailable",
        "total_vectors": 0,
        "message": "Vector database not connected"
    }
