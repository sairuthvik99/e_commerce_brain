from pydantic import BaseModel, Field
from typing import List, Optional

# BaseModel validates the output structure of agents
# ge -> Greater than or equal to
# le -> Less than or equal to
# `...` -> implies that the field is required
# `BaseModel` gives you the validation engine, while `Field` lets you fine-tune how each attribute should be validated and documented.

class AgentOutput(BaseModel):
    finding: str = Field(..., description="Agent's main finding")
    evidence: List[str] = Field(..., description="List of evidence metric names")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    agent: str = Field(..., description="Agent name")