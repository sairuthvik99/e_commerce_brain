"""
Database Table Access Permissions

Defines which tables each agent is allowed to access.
This ensures agents can only query data relevant to their domain.
Supports cross-domain access for queries that require multiple data sources.
"""

from typing import Dict, List, Set
from enum import Enum


class AgentType(str, Enum):
    """Agent types in the system."""
    SALES = "sales"
    MARKETING = "marketing"
    INVENTORY = "inventory"
    SUPPORT = "support"
    GENERAL = "general"
    SUPERVISOR = "supervisor"


# Table names in the database
class Tables(str, Enum):
    """Database table names."""
    ORDERS = "orders"
    ORDER_ITEMS = "order_items"
    DAILY_METRICS = "daily_metrics"
    INVENTORY_SNAPSHOTS = "inventory_snapshots"
    MARKETING_CAMPAIGNS_DAILY = "marketing_campaigns_daily"
    SUPPORT_TICKETS = "support_tickets"


# Agent-to-table access mapping (BASE permissions)
AGENT_TABLE_ACCESS: Dict[AgentType, Set[Tables]] = {
    # Sales agent: access to daily_metrics, orders, and order_items
    AgentType.SALES: {
        Tables.DAILY_METRICS,
        Tables.ORDERS,
        Tables.ORDER_ITEMS,
    },
    
    # Marketing agent: access to daily_metrics and marketing_campaigns_daily
    AgentType.MARKETING: {
        Tables.DAILY_METRICS,
        Tables.MARKETING_CAMPAIGNS_DAILY,
    },
    
    # Inventory agent: access to daily_metrics and inventory_snapshots
    AgentType.INVENTORY: {
        Tables.DAILY_METRICS,
        Tables.INVENTORY_SNAPSHOTS,
    },
    
    # Support agent: access to daily_metrics and support_tickets
    AgentType.SUPPORT: {
        Tables.DAILY_METRICS,
        Tables.SUPPORT_TICKETS,
    },
    
    # General agent: access to ALL tables
    AgentType.GENERAL: {
        Tables.ORDERS,
        Tables.ORDER_ITEMS,
        Tables.DAILY_METRICS,
        Tables.INVENTORY_SNAPSHOTS,
        Tables.MARKETING_CAMPAIGNS_DAILY,
        Tables.SUPPORT_TICKETS,
    },
    
    # Supervisor: access to ALL tables (for routing decisions)
    AgentType.SUPERVISOR: {
        Tables.ORDERS,
        Tables.ORDER_ITEMS,
        Tables.DAILY_METRICS,
        Tables.INVENTORY_SNAPSHOTS,
        Tables.MARKETING_CAMPAIGNS_DAILY,
        Tables.SUPPORT_TICKETS,
    },
}


# Cross-domain table access - additional tables agents can access for specific queries
# These are granted when cross-domain access is enabled
CROSS_DOMAIN_TABLE_ACCESS: Dict[AgentType, Set[Tables]] = {
    # Inventory agent can access orders table for "viewed but not purchased" queries
    AgentType.INVENTORY: {
        Tables.ORDERS,
    },
    
    # Marketing agent can access orders for discount/ROI analysis
    AgentType.MARKETING: {
        Tables.ORDERS,
    },
    
    # Support agent can access orders to correlate reviews with conversions
    AgentType.SUPPORT: {
        Tables.ORDERS,
    },
    
    # Sales agent can access inventory and marketing for root cause analysis
    AgentType.SALES: {
        Tables.INVENTORY_SNAPSHOTS,
        Tables.MARKETING_CAMPAIGNS_DAILY,
    },
}


# Cross-domain method access - additional DataLoader methods granted for cross-domain queries
CROSS_DOMAIN_METHOD_ACCESS: Dict[str, Set[str]] = {
    # Inventory agent can load sales data for cross-reference
    "inventory": {"load_sales_data"},
    
    # Marketing agent can load sales data for discount recommendations
    "marketing": {"load_sales_data"},
    
    # Support agent can load sales data for review/conversion correlation
    "support": {"load_sales_data"},
    
    # Sales agent can load inventory/marketing for root cause analysis
    "sales": {"load_inventory_data", "load_marketing_data"},
}


def get_allowed_tables(agent_type: str, include_cross_domain: bool = False) -> Set[str]:
    """
    Get the set of table names an agent is allowed to access.
    
    Args:
        agent_type: The agent type as a string (e.g., "sales", "marketing")
        include_cross_domain: If True, include cross-domain tables
        
    Returns:
        Set of table names the agent can access
    """
    try:
        agent = AgentType(agent_type.lower())
        tables = AGENT_TABLE_ACCESS.get(agent, set()).copy()
        
        # Add cross-domain tables if enabled
        if include_cross_domain:
            cross_domain_tables = CROSS_DOMAIN_TABLE_ACCESS.get(agent, set())
            tables = tables.union(cross_domain_tables)
        
        return {t.value for t in tables}
    except ValueError:
        # Unknown agent type - return empty set (no access)
        return set()


def has_table_access(agent_type: str, table_name: str, include_cross_domain: bool = False) -> bool:
    """
    Check if an agent has access to a specific table.
    
    Args:
        agent_type: The agent type as a string
        table_name: The table name to check access for
        include_cross_domain: If True, include cross-domain permissions
        
    Returns:
        True if agent has access, False otherwise
    """
    allowed_tables = get_allowed_tables(agent_type, include_cross_domain=include_cross_domain)
    return table_name.lower() in allowed_tables


def validate_agent_access(agent_type: str, requested_tables: List[str], include_cross_domain: bool = False) -> Dict:
    """
    Validate which tables an agent can access from a list of requested tables.
    
    Args:
        agent_type: The agent type as a string
        requested_tables: List of table names the agent wants to access
        include_cross_domain: If True, include cross-domain permissions
        
    Returns:
        Dict with 'allowed' and 'denied' lists of table names
    """
    allowed_tables = get_allowed_tables(agent_type, include_cross_domain=include_cross_domain)
    
    allowed = []
    denied = []
    
    for table in requested_tables:
        if table.lower() in allowed_tables:
            allowed.append(table)
        else:
            denied.append(table)
    
    return {
        'allowed': allowed,
        'denied': denied,
        'all_allowed': len(denied) == 0
    }


# Data loader method to table mapping
# This maps DataLoader methods to the tables they access
DATA_LOADER_METHOD_TABLES: Dict[str, Set[str]] = {
    'load_sales_data': {'daily_metrics', 'orders'},
    'load_top_products_data': {'orders', 'order_items'},
    'load_inventory_data': {'daily_metrics', 'inventory_snapshots'},
    'load_inventory_baseline': {'daily_metrics', 'inventory_snapshots'},
    'load_marketing_data': {'daily_metrics', 'marketing_campaigns_daily'},
    'load_channel_data': {'marketing_campaigns_daily'},
    'load_support_data': {'daily_metrics', 'support_tickets'},
    'get_yesterday_date': {'daily_metrics'},  # Accessible by all
    'load_all_products_inventory': {'inventory_snapshots'},  # List all products
    'load_product_inventory': {'inventory_snapshots'},  # Get single product
    'search_products': {'inventory_snapshots'},  # Search products
    'update_product_stock': {'inventory_snapshots'},  # Update stock (HITL protected)
}


def can_use_data_method(agent_type: str, method_name: str, include_cross_domain: bool = False) -> bool:
    """
    Check if an agent can use a specific DataLoader method.
    
    Args:
        agent_type: The agent type as a string
        method_name: The DataLoader method name
        include_cross_domain: If True, include cross-domain permissions
        
    Returns:
        True if agent can use the method, False otherwise
    """
    # Check if method is in cross-domain access list
    if include_cross_domain:
        cross_domain_methods = CROSS_DOMAIN_METHOD_ACCESS.get(agent_type.lower(), set())
        if method_name in cross_domain_methods:
            return True
    
    required_tables = DATA_LOADER_METHOD_TABLES.get(method_name, set())
    allowed_tables = get_allowed_tables(agent_type, include_cross_domain=include_cross_domain)
    
    # Agent can use the method if they have access to ALL required tables
    return required_tables.issubset(allowed_tables)


def get_allowed_data_methods(agent_type: str, include_cross_domain: bool = False) -> List[str]:
    """
    Get list of DataLoader methods an agent is allowed to use.
    
    Args:
        agent_type: The agent type as a string
        include_cross_domain: If True, include cross-domain methods
        
    Returns:
        List of method names the agent can use
    """
    allowed_methods = []
    for method, tables in DATA_LOADER_METHOD_TABLES.items():
        if can_use_data_method(agent_type, method, include_cross_domain=include_cross_domain):
            allowed_methods.append(method)
    return allowed_methods


def get_cross_domain_methods(agent_type: str) -> Set[str]:
    """
    Get the set of cross-domain methods available to an agent.
    
    Args:
        agent_type: The agent type as a string
        
    Returns:
        Set of method names granted through cross-domain access
    """
    return CROSS_DOMAIN_METHOD_ACCESS.get(agent_type.lower(), set())
