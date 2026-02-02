"""
Database Table Access Permissions

Defines which tables each agent is allowed to access.
This ensures agents can only query data relevant to their domain.
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
    DAILY_METRICS = "daily_metrics"
    INVENTORY_SNAPSHOTS = "inventory_snapshots"
    MARKETING_CAMPAIGNS_DAILY = "marketing_campaigns_daily"
    SUPPORT_TICKETS = "support_tickets"


# Agent-to-table access mapping
AGENT_TABLE_ACCESS: Dict[AgentType, Set[Tables]] = {
    # Sales agent: access to daily_metrics and orders
    AgentType.SALES: {
        Tables.DAILY_METRICS,
        Tables.ORDERS,
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
        Tables.DAILY_METRICS,
        Tables.INVENTORY_SNAPSHOTS,
        Tables.MARKETING_CAMPAIGNS_DAILY,
        Tables.SUPPORT_TICKETS,
    },
    
    # Supervisor: access to ALL tables (for routing decisions)
    AgentType.SUPERVISOR: {
        Tables.ORDERS,
        Tables.DAILY_METRICS,
        Tables.INVENTORY_SNAPSHOTS,
        Tables.MARKETING_CAMPAIGNS_DAILY,
        Tables.SUPPORT_TICKETS,
    },
}


def get_allowed_tables(agent_type: str) -> Set[str]:
    """
    Get the set of table names an agent is allowed to access.
    
    Args:
        agent_type: The agent type as a string (e.g., "sales", "marketing")
        
    Returns:
        Set of table names the agent can access
    """
    try:
        agent = AgentType(agent_type.lower())
        tables = AGENT_TABLE_ACCESS.get(agent, set())
        return {t.value for t in tables}
    except ValueError:
        # Unknown agent type - return empty set (no access)
        return set()


def has_table_access(agent_type: str, table_name: str) -> bool:
    """
    Check if an agent has access to a specific table.
    
    Args:
        agent_type: The agent type as a string
        table_name: The table name to check access for
        
    Returns:
        True if agent has access, False otherwise
    """
    allowed_tables = get_allowed_tables(agent_type)
    return table_name.lower() in allowed_tables


def validate_agent_access(agent_type: str, requested_tables: List[str]) -> Dict:
    """
    Validate which tables an agent can access from a list of requested tables.
    
    Args:
        agent_type: The agent type as a string
        requested_tables: List of table names the agent wants to access
        
    Returns:
        Dict with 'allowed' and 'denied' lists of table names
    """
    allowed_tables = get_allowed_tables(agent_type)
    
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
    'load_inventory_data': {'daily_metrics', 'inventory_snapshots'},
    'load_inventory_baseline': {'daily_metrics', 'inventory_snapshots'},
    'load_marketing_data': {'daily_metrics', 'marketing_campaigns_daily'},
    'load_support_data': {'daily_metrics', 'support_tickets'},
    'get_yesterday_date': {'daily_metrics'},  # Accessible by all
}


def can_use_data_method(agent_type: str, method_name: str) -> bool:
    """
    Check if an agent can use a specific DataLoader method.
    
    Args:
        agent_type: The agent type as a string
        method_name: The DataLoader method name
        
    Returns:
        True if agent can use the method, False otherwise
    """
    required_tables = DATA_LOADER_METHOD_TABLES.get(method_name, set())
    allowed_tables = get_allowed_tables(agent_type)
    
    # Agent can use the method if they have access to ALL required tables
    return required_tables.issubset(allowed_tables)


def get_allowed_data_methods(agent_type: str) -> List[str]:
    """
    Get list of DataLoader methods an agent is allowed to use.
    
    Args:
        agent_type: The agent type as a string
        
    Returns:
        List of method names the agent can use
    """
    allowed_methods = []
    for method, tables in DATA_LOADER_METHOD_TABLES.items():
        if can_use_data_method(agent_type, method):
            allowed_methods.append(method)
    return allowed_methods
