"""
Inventory agent module.

LLM-driven inventory analysis with LangChain tools.
"""

from backend.agents.inventory.agent import InventoryAgent, InventoryAgentContext
from backend.agents.inventory.tools import (
    get_inventory_tools,
    get_tool_descriptions,
    analyze_inventory_status,
    analyze_stockout_events,
    analyze_stockout_trend,
    identify_critical_stockouts,
    analyze_inventory_impact,
    prioritize_restock,
    get_inventory_summary,
    compare_stockout_severity,
)

__all__ = [
    "InventoryAgent",
    "InventoryAgentContext",
    "get_inventory_tools",
    "get_tool_descriptions",
    "analyze_inventory_status",
    "analyze_stockout_events",
    "analyze_stockout_trend",
    "identify_critical_stockouts",
    "analyze_inventory_impact",
    "prioritize_restock",
    "get_inventory_summary",
    "compare_stockout_severity",
]