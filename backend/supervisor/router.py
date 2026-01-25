"""
Supervisor Routing Logic

Maps detected intents to domain agents.
For MVP: Simple hardcoded rules.
Day 3+: Can be enhanced with configuration or rule engine.
"""

from typing import List
import logging

logger = logging.getLogger(__name__)

# Valid agent names in the system
VALID_AGENTS = ["sales", "inventory", "marketing", "support"]

# Routing map: intent -> list of agents
ROUTING_MAP = {
    "sales_drop": ["sales", "inventory", "marketing", "support"],
    "inventory_issue": ["inventory", "sales"],
    "marketing_issue": ["marketing", "sales"],
    "support_issue": ["support", "sales"],
}


def route_agents(intent: str) -> List[str]:
    """
    Route an intent to appropriate domain agents.
    
    Args:
        intent: Classified intent string (e.g., 'sales_drop')
    
    Returns:
        List of agent names to call
    
    Examples:
        >>> route_agents("sales_drop")
        ["sales", "inventory", "marketing", "support"]
        
        >>> route_agents("unknown")
        []
    """
    if not intent:
        logger.warning("[Router] Empty intent provided, returning no agents")
        return []
    
    agents = ROUTING_MAP.get(intent, [])
    
    logger.info(f"[Router] Intent '{intent}' → Agents: {agents}")
    
    return agents


def add_routing_rule(intent: str, agents: List[str]) -> None:
    """
    Add or update a routing rule (for testing or future dynamic routing).
    
    Args:
        intent: Intent label
        agents: List of agent names
    """
    # Validate agents
    invalid_agents = [a for a in agents if a not in VALID_AGENTS]
    if invalid_agents:
        raise ValueError(f"Invalid agents: {invalid_agents}. Valid agents: {VALID_AGENTS}")
    
    ROUTING_MAP[intent] = agents
    logger.info(f"[Router] Added/updated rule: {intent} → {agents}")


def get_all_routes() -> dict:
    """
    Get all current routing rules (useful for debugging/introspection).
    
    Returns:
        Dict mapping intents to agent lists
    """
    return ROUTING_MAP.copy()