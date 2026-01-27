"""
Reflection Result Schema

Defines the structure for reflection agent output.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any


class ReflectionResult(BaseModel):
    """
    Result of the self-reflection agent's audit.
    
    Contains quality metrics and detected issues.
    """
    quality_score: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Overall quality score (0-1)"
    )
    conflicts_detected: int = Field(
        default=0,
        description="Number of conflicts detected between agent findings"
    )
    conflicts: List[str] = Field(
        default_factory=list,
        description="List of detected conflicts/contradictions"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings/issues found"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Suggested improvements"
    )
    pass_threshold: bool = Field(
        default=True,
        alias="pass",
        description="Whether the reflection passed quality threshold"
    )
    
    class Config:
        populate_by_name = True
