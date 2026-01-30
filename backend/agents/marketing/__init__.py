"""
Marketing agent module.

LLM-driven marketing analysis with LangChain tools.
"""

from backend.agents.marketing.agent import MarketingAgent, MarketingAgentContext
from backend.agents.marketing.tools import (
    get_marketing_tools,
    get_tool_descriptions,
    analyze_marketing_performance,
    analyze_campaign_conversions,
    analyze_ad_spend,
    analyze_marketing_roi,
    analyze_campaign_status,
    compare_campaign_periods,
    identify_conversion_drop_cause,
    get_marketing_summary,
    analyze_marketing_sales_correlation,
)

__all__ = [
    "MarketingAgent",
    "MarketingAgentContext",
    "get_marketing_tools",
    "get_tool_descriptions",
    "analyze_marketing_performance",
    "analyze_campaign_conversions",
    "analyze_ad_spend",
    "analyze_marketing_roi",
    "analyze_campaign_status",
    "compare_campaign_periods",
    "identify_conversion_drop_cause",
    "get_marketing_summary",
    "analyze_marketing_sales_correlation",
]