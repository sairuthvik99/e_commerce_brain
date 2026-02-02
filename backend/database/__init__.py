"""
Database package for PostgreSQL integration.
"""

from .connection import get_engine, get_session
from .models import (
    Orders,
    InventorySnapshots,
    MarketingCampaignsDaily,
    SupportTickets,
    DailyMetrics
)
from .permissions import (
    AgentType,
    Tables,
    AGENT_TABLE_ACCESS,
    get_allowed_tables,
    has_table_access,
    validate_agent_access,
    can_use_data_method,
    get_allowed_data_methods
)

__all__ = [
    "get_engine",
    "get_session",
    "Orders",
    "InventorySnapshots",
    "MarketingCampaignsDaily",
    "SupportTickets",
    "DailyMetrics",
    # Permissions
    "AgentType",
    "Tables",
    "AGENT_TABLE_ACCESS",
    "get_allowed_tables",
    "has_table_access",
    "validate_agent_access",
    "can_use_data_method",
    "get_allowed_data_methods"
]