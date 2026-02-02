"""
Settings Endpoint

Provides endpoints for managing application settings like LLM model selection.
"""

from typing import Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from backend.settings import Settings

router = APIRouter(prefix="/settings", tags=["Settings"])


# ============================================================
# Request/Response Models
# ============================================================

class ChangeModelRequest(BaseModel):
    """Request model for changing the LLM model."""
    model_id: str = Field(..., description="The model ID to set for all agents")


class ModelInfo(BaseModel):
    """Model information response."""
    model_id: str = Field(..., description="Current model ID")
    agents: Dict[str, str] = Field(..., description="Per-agent model mapping")


class ChangeModelResponse(BaseModel):
    """Response model for model change operation."""
    success: bool = Field(..., description="Whether the change was successful")
    message: str = Field(..., description="Status message")
    previous_model: str = Field(..., description="Previous model ID")
    current_model: str = Field(..., description="New model ID")
    agents_updated: List[str] = Field(..., description="List of agents that were updated")


# ============================================================
# Endpoints
# ============================================================

@router.get("/model", response_model=ModelInfo)
async def get_current_model():
    """
    Get the current LLM model configuration.
    
    Returns the current model being used by all agents.
    """
    try:
        # Get the first agent's model as the "current" model
        # (all agents should have the same model after a change)
        agent_models = Settings.AGENT_MODELS
        current_model = next(iter(agent_models.values()), "gpt-4")
        
        return ModelInfo(
            model_id=current_model,
            agents=agent_models
        )
    except Exception as e:
        logger.error(f"Failed to get current model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model", response_model=ChangeModelResponse)
async def change_agent_model(request: ChangeModelRequest):
    """
    Change the LLM model for all agents.
    
    This endpoint updates the model used by all agents in the system.
    The change is applied immediately and affects all subsequent requests.
    
    Args:
        request: ChangeModelRequest containing the new model_id
        
    Returns:
        ChangeModelResponse with success status and updated agent list
    """
    try:
        model_id = request.model_id
        
        if not model_id or not isinstance(model_id, str):
            raise HTTPException(
                status_code=400, 
                detail="model_id must be a non-empty string"
            )
        
        logger.info(f"Changing LLM model to: {model_id}")
        
        # Get the previous model (from first agent)
        previous_model = next(iter(Settings.AGENT_MODELS.values()), "gpt-4")
        
        # Update all agents to use the new model
        agents_updated = []
        for agent_name in Settings.AGENT_MODELS.keys():
            Settings.AGENT_MODELS[agent_name] = model_id
            agents_updated.append(agent_name)
        
        logger.info(f"Successfully updated {len(agents_updated)} agents to model: {model_id}")
        
        return ChangeModelResponse(
            success=True,
            message=f"Successfully changed model to {model_id}",
            previous_model=previous_model,
            current_model=model_id,
            agents_updated=agents_updated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change model: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to change model: {str(e)}"
        )
