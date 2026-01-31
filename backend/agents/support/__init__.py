"""
Support agent module.

LLM-driven support analysis with LangChain tools.
"""

from backend.agents.support.agent import SupportAgent, SupportAgentContext
from backend.agents.support.tools import (
    get_support_tools,
    get_tool_descriptions,
    analyze_support_status,
    analyze_ticket_volume,
    analyze_customer_sentiment,
    analyze_issue_categories,
    analyze_support_trend,
    analyze_refunds_returns,
    identify_support_spike_cause,
    get_support_summary,
    analyze_support_sales_correlation,
)

__all__ = [
    "SupportAgent",
    "SupportAgentContext",
    "get_support_tools",
    "get_tool_descriptions",
    "analyze_support_status",
    "analyze_ticket_volume",
    "analyze_customer_sentiment",
    "analyze_issue_categories",
    "analyze_support_trend",
    "analyze_refunds_returns",
    "identify_support_spike_cause",
    "get_support_summary",
    "analyze_support_sales_correlation",
]