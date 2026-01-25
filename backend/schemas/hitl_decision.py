from pydantic import BaseModel, Field
from typing import Optional

class HITLDecision(BaseModel):
    approved: bool = Field(..., description="Was the action approved?")
    reason: Optional[str] = Field(None, description="Reason for rejection (if any)")