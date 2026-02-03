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
    list_all_products,
    get_product_details,
    propose_stock_update,
)
from backend.agents.inventory.hitl_actions import (
    store_pending_stock_update,
    get_pending_stock_update,
    get_all_pending_stock_updates,
    approve_stock_update,
    reject_stock_update,
    execute_stock_update,
    get_pending_updates_for_display,
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
    "list_all_products",
    "get_product_details",
    "propose_stock_update",
    # HITL Actions
    "store_pending_stock_update",
    "get_pending_stock_update",
    "get_all_pending_stock_updates",
    "approve_stock_update",
    "reject_stock_update",
    "execute_stock_update",
    "get_pending_updates_for_display",
]