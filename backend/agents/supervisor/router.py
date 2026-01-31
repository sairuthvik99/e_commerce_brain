"""
Supervisor Routing Logic

Maps detected intents to domain agents.
Enhanced for LLM-driven architecture with memory and action intents.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Valid agent names in the system
VALID_AGENTS = ["sales", "inventory", "marketing", "support", "general"]

# Valid intent categories
VALID_INTENTS = [
    "sales", "inventory", "marketing", "support",
    "general", "memory", "action", "unknown"
]

# Routing map: intent -> list of agents
# Using broader intent categories that map to agent names
ROUTING_MAP = {
    # Single domain intents
    "sales": ["sales"],
    "inventory": ["inventory"],
    "marketing": ["marketing"],
    "support": ["support"],
    
    # Multi-domain intents - route to general agent
    "general": ["general"],
    
    # Special intents (may or may not need domain agents)
    "memory": [],  # Memory queries handled by supervisor
    "action": ["sales", "inventory", "marketing", "support"],  # Need context for actions
    
    # Unknown intents - route to general agent for best-effort handling
    "unknown": ["general"],
}


def route_agents(intent: str) -> List[str]:
    """
    Route an intent to appropriate domain agents.
    
    Args:
        intent: Classified intent string (e.g., 'sales_drop')
    
    Returns:
        List of agent names to call
    
    Examples:
        >>> route_agents("sales")
        ["sales"]
        
        >>> route_agents("general")
        ["general"]
        
        >>> route_agents("unknown")
        ["general"]
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