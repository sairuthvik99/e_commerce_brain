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