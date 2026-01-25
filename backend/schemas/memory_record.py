from pydantic import BaseModel, Field
from typing import Optional

class MemoryRecord(BaseModel):
    incident_summary: str
    root_cause: str
    action: str = Field(..., description="Proposed corrective action")
    human_decision: str = Field(..., description="Human decision on the action")
    outcome: Optional[str] = Field(None, description="Outcome after action implementation")