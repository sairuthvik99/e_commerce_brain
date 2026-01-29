"""
Sales agent module.

LLM-driven sales analysis with LangChain tools.
"""

from backend.agents.sales.agent import SalesAgent, SalesAgentContext
from backend.agents.sales.tools import (
    get_sales_tools,
    get_tool_descriptions,
    analyze_sales_performance,
    compare_sales_periods,
    analyze_sales_trend,
    identify_sales_anomaly,
    identify_drop_cause,
    analyze_regional_performance,
    get_sales_summary,
)

__all__ = [
    "SalesAgent",
    "SalesAgentContext",
    "get_sales_tools",
    "get_tool_descriptions",
    "analyze_sales_performance",
    "compare_sales_periods",
    "analyze_sales_trend",
    "identify_sales_anomaly",
    "identify_drop_cause",
    "analyze_regional_performance",
    "get_sales_summary",
]