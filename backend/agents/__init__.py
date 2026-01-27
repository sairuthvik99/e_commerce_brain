"""
Domain agents package.

All agents inherit from BaseAgent and follow consistent interface.
"""

from .base_agent import BaseAgent, AgentContext, AnalysisResult
from .sales.agent import SalesAgent
from .inventory.agent import InventoryAgent
from .marketing.agent import MarketingAgent
from .support.agent import SupportAgent

__all__ = [
    "BaseAgent",
    "AgentContext",
    "AnalysisResult",
    "SalesAgent",
    "InventoryAgent",
    "MarketingAgent",
    "SupportAgent"
]