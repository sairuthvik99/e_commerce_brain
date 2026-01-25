from pydantic import BaseModel, Field
from typing import List

class RootCause(BaseModel):
    cause: str = Field(..., description="Root cause summary")
    supporting_agents: List[str] = Field(..., description="Agents supporting this cause")
    overall_confidence: float = Field(..., ge=0, le=1, description="Aggregated confidence")