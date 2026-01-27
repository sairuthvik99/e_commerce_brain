from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class RootCause(BaseModel):
    root_cause: str = Field(..., description="Narrative summary of the root cause")
    primary_cause: str = Field(..., description="Agent name of the primary cause")
    contributing_causes: List[str] = Field(default_factory=list, description="List of contributing agent names")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    causal_chain: List[str] = Field(default_factory=list, description="Ordered list of agent names in causal chain")
    evidence_summary: Dict[str, List[str]] = Field(default_factory=dict, description="Agent name to evidence list")
    timestamp: Optional[str] = Field(None, description="Timestamp of analysis")