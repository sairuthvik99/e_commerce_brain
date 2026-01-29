"""
Supervisor agent module.

LLM-driven intent classification and agent routing.
"""

from backend.agents.supervisor.agent import SupervisorAgent
from backend.agents.supervisor.router import route_agents, ROUTING_MAP, VALID_INTENTS
from backend.agents.supervisor.tools import (
    get_supervisor_tools,
    get_tool_descriptions,
    classify_user_intent,
    determine_agents_to_call,
    analyze_cross_domain_impact,
    identify_root_cause,
    query_past_incidents,
    generate_action_recommendations,
    prepare_hitl_action,
    generate_executive_summary,
    calculate_confidence_score,
)

__all__ = [
    "SupervisorAgent",
    "route_agents",
    "ROUTING_MAP",
    "VALID_INTENTS",
    "get_supervisor_tools",
    "get_tool_descriptions",
    "classify_user_intent",
    "determine_agents_to_call",
    "analyze_cross_domain_impact",
    "identify_root_cause",
    "query_past_incidents",
    "generate_action_recommendations",
    "prepare_hitl_action",
    "generate_executive_summary",
    "calculate_confidence_score",
]
