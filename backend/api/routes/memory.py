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


# ============================================================
# Short-Term Memory Endpoints (Conversation History)
# ============================================================

class ConversationEntry(BaseModel):
    """A single conversation history entry."""
    id: int = Field(..., description="Entry ID")
    question: str = Field(..., description="User's question")
    response: str = Field(default="", description="Agent's response")
    intent: str = Field(default="", description="Detected intent")
    agent_outputs: Optional[Dict[str, Any]] = Field(None, description="Outputs from each agent")
    root_cause: Optional[Dict[str, Any]] = Field(None, description="Root cause analysis")
    timestamp: Optional[str] = Field(None, description="When the conversation occurred")


class ShortTermMemoryResponse(BaseModel):
    """Response containing short-term memory (conversation history)."""
    entries: List[ConversationEntry]
    total_count: int
    max_entries: int = 10
    message: str


@router.get(
    "/memory/short-term",
    response_model=ShortTermMemoryResponse,
    summary="Get Short-Term Memory",
    description="Retrieve the conversation history (last 10 entries)"
)
async def get_short_term_memory(
    limit: int = Query(10, ge=1, le=10, description="Max entries to retrieve")
) -> ShortTermMemoryResponse:
    """
    Get the short-term memory (conversation history).
    
    Returns the last N conversation entries stored in the database.
    The system keeps a maximum of 10 entries.
    """
    try:
        from backend.memory import ShortTermMemory
        
        stm = ShortTermMemory()
        history = stm.get_conversation_history(limit=limit)
        
        entries = [
            ConversationEntry(
                id=entry.get("id", 0),
                question=entry.get("question", ""),
                response=entry.get("response", ""),
                intent=entry.get("intent", ""),
                agent_outputs=entry.get("agent_outputs"),
                root_cause=entry.get("root_cause"),
                timestamp=entry.get("timestamp")
            )
            for entry in history
        ]
        
        return ShortTermMemoryResponse(
            entries=entries,
            total_count=len(entries),
            max_entries=10,
            message=f"Retrieved {len(entries)} conversation entries"
        )
    except Exception as e:
        logger.error(f"Failed to get short-term memory: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve short-term memory: {str(e)}"
        )


@router.delete(
    "/memory/short-term",
    summary="Clear Short-Term Memory",
    description="Clear all conversation history"
)
async def clear_short_term_memory() -> Dict[str, Any]:
    """Clear all short-term memory (conversation history)."""
    try:
        from backend.memory import ShortTermMemory
        
        stm = ShortTermMemory()
        stm.clear_history()
        
        return {
            "success": True,
            "message": "Short-term memory cleared successfully"
        }
    except Exception as e:
        logger.error(f"Failed to clear short-term memory: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear short-term memory: {str(e)}"
        )


# ============================================================
# Long-Term Memory Endpoints (Preferences, Facts, Knowledge)
# ============================================================

class PreferenceEntry(BaseModel):
    """A preference entry."""
    key: str = Field(..., description="Preference key")
    value: Any = Field(..., description="Preference value")


class FactEntry(BaseModel):
    """A fact entry."""
    key: str = Field(..., description="Fact key")
    fact: str = Field(..., description="The fact content")
    category: str = Field(default="general", description="Fact category")
    created_at: Optional[str] = Field(None, description="When the fact was created")


class KnowledgeEntry(BaseModel):
    """A knowledge entry."""
    key: str = Field(..., description="Knowledge key")
    topic: str = Field(..., description="Topic/title")
    content: str = Field(..., description="Knowledge content")
    source: str = Field(default="", description="Source of knowledge")
    created_at: Optional[str] = Field(None, description="When the knowledge was created")


class LongTermMemoryResponse(BaseModel):
    """Response containing long-term memory."""
    preferences: List[PreferenceEntry]
    facts: List[FactEntry]
    knowledge: List[KnowledgeEntry]
    message: str


@router.get(
    "/memory/long-term",
    response_model=LongTermMemoryResponse,
    summary="Get Long-Term Memory",
    description="Retrieve all long-term memory (preferences, facts, knowledge)"
)
async def get_long_term_memory() -> LongTermMemoryResponse:
    """
    Get the long-term memory.
    
    Returns all stored preferences, facts, and knowledge entries.
    """
    try:
        from backend.memory import LongTermMemory
        
        ltm = LongTermMemory()
        
        # Get all preferences
        raw_preferences = ltm.get_all_preferences()
        preferences = [
            PreferenceEntry(key=k, value=v)
            for k, v in raw_preferences.items()
        ]
        
        # Get all facts
        raw_facts = ltm.get_facts(limit=50)
        facts = [
            FactEntry(
                key=f.get("key", ""),
                fact=f.get("fact", ""),
                category=f.get("category", "general"),
                created_at=f.get("created_at")
            )
            for f in raw_facts
        ]
        
        # Get all knowledge
        raw_knowledge = ltm.get_knowledge(limit=50)
        knowledge = [
            KnowledgeEntry(
                key=k.get("key", ""),
                topic=k.get("topic", ""),
                content=k.get("content", ""),
                source=k.get("source", ""),
                created_at=k.get("created_at")
            )
            for k in raw_knowledge
        ]
        
        return LongTermMemoryResponse(
            preferences=preferences,
            facts=facts,
            knowledge=knowledge,
            message=f"Retrieved {len(preferences)} preferences, {len(facts)} facts, {len(knowledge)} knowledge entries"
        )
    except Exception as e:
        logger.error(f"Failed to get long-term memory: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve long-term memory: {str(e)}"
        )


@router.delete(
    "/memory/long-term",
    summary="Clear Long-Term Memory",
    description="Clear all long-term memory (use with caution)"
)
async def clear_long_term_memory() -> Dict[str, Any]:
    """Clear all long-term memory (preferences, facts, knowledge)."""
    try:
        from backend.memory import LongTermMemory
        
        ltm = LongTermMemory()
        ltm.clear_all()
        
        return {
            "success": True,
            "message": "Long-term memory cleared successfully"
        }
    except Exception as e:
        logger.error(f"Failed to clear long-term memory: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear long-term memory: {str(e)}"
        )


# ============================================================
# Long-Term Memory Write Endpoints
# ============================================================

class SavePreferenceRequest(BaseModel):
    """Request to save a preference."""
    key: str = Field(..., min_length=1, description="Preference key")
    value: Any = Field(..., description="Preference value")


class SaveFactRequest(BaseModel):
    """Request to save a fact."""
    fact: str = Field(..., min_length=5, description="The fact to store")
    category: str = Field(default="general", description="Category of the fact")


class SaveKnowledgeRequest(BaseModel):
    """Request to save knowledge."""
    topic: str = Field(..., min_length=3, description="Topic/title")
    content: str = Field(..., min_length=10, description="Knowledge content")
    source: str = Field(default="user", description="Source of knowledge")


@router.post(
    "/memory/long-term/preference",
    summary="Save Preference",
    description="Save a user or system preference to long-term memory"
)
async def save_preference(request: SavePreferenceRequest) -> Dict[str, Any]:
    """Save a preference to long-term memory."""
    try:
        from backend.memory import LongTermMemory
        
        ltm = LongTermMemory()
        ltm.save_preference(request.key, request.value)
        
        return {
            "success": True,
            "message": f"Preference '{request.key}' saved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to save preference: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save preference: {str(e)}"
        )


@router.post(
    "/memory/long-term/fact",
    summary="Save Fact",
    description="Save a learned fact to long-term memory"
)
async def save_fact(request: SaveFactRequest) -> Dict[str, Any]:
    """Save a fact to long-term memory."""
    try:
        from backend.memory import LongTermMemory
        
        ltm = LongTermMemory()
        key = ltm.save_fact(request.fact, request.category)
        
        return {
            "success": True,
            "key": key,
            "message": "Fact saved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to save fact: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save fact: {str(e)}"
        )


@router.post(
    "/memory/long-term/knowledge",
    summary="Save Knowledge",
    description="Save accumulated knowledge to long-term memory"
)
async def save_knowledge(request: SaveKnowledgeRequest) -> Dict[str, Any]:
    """Save knowledge to long-term memory."""
    try:
        from backend.memory import LongTermMemory
        
        ltm = LongTermMemory()
        key = ltm.save_knowledge(request.topic, request.content, request.source)
        
        return {
            "success": True,
            "key": key,
            "message": "Knowledge saved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to save knowledge: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save knowledge: {str(e)}"
        )
