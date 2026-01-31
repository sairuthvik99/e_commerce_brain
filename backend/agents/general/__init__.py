"""
General Agent Package

Handles general business inquiries and unknown intents.
Provides cross-domain analysis capabilities.
"""

from .agent import GeneralAgent, GeneralAgentContext
from .tools import get_general_tools, GeneralLLMAnalyzer, get_tool_descriptions

__all__ = [
    "GeneralAgent",
    "GeneralAgentContext",
    "get_general_tools",
    "GeneralLLMAnalyzer",
    "get_tool_descriptions",
]
