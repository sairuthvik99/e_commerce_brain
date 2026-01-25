from pydantic import BaseModel, Field

class ActionProposal(BaseModel):
    action: str = Field(..., description="Proposed corrective action")
    rationale: str = Field(..., description="Reason for this action")