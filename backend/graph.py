"""
LangGraph Flow Definition

Wires together the complete agentic system using new BaseAgent architecture.

Flow:
    User Input → Supervisor → Domain Agents (sequential with data sharing) → 
    Synthesis → Reflection → HITL → END

Data Sharing Strategy:
    Agents execute sequentially in priority order (inventory → sales → marketing → support)
    so each agent can access previous agents' findings in their context.
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict, List
from .settings import Settings

from .agents.sales.agent import SalesAgent
from .agents.inventory.agent import InventoryAgent
from .agents.marketing.agent import MarketingAgent
from .agents.support.agent import SupportAgent

from .agents.supervisor.agent import SupervisorAgent

import logging

logger = logging.getLogger(__name__)


# ==================== STATE DEFINITION ====================

class MVPState(TypedDict, total=False):
    """
    Canonical state that flows through the graph.
    
    Fields:
        question: User's input question
        intent: Detected intent (e.g., 'sales_drop')
        agents_to_call: List of agent names to execute
        agent_outputs: Dict mapping agent name to AgentOutput
        agents_completed: List of agents that have finished execution
        root_cause: Synthesized root cause (Day 4)
        action_proposal: Proposed action (Day 5)
        hitl_decision: Human decision (Day 5)
        error: Error message if something fails
    """
    question: str
    intent: str
    agents_to_call: List[str]
    agent_outputs: Dict[str, Dict[str, Any]]
    agents_completed: List[str]
    root_cause: Dict[str, Any]
    action_proposal: Dict[str, Any]
    hitl_decision: Dict[str, Any]
    error: str


# ==================== PLACEHOLDER NODES (Day 4-6) ====================

class SynthesisNode:
    """
    Synthesizes agent outputs into root cause.
    
    Day 3: Pass-through with logging
    Day 4: Actual synthesis logic
    """
    def __call__(self, state: MVPState) -> MVPState:
        logger.info("[SynthesisNode] Aggregating agent outputs...")
        
        agent_outputs = state.get("agent_outputs", {})
        
        # Log what we received
        for agent_name, output in agent_outputs.items():
            logger.info(
                f"  → {agent_name}: {output.get('finding', 'N/A')[:80]}... "
                f"(confidence: {output.get('confidence', 0):.2%})"
            )
        
        logger.info("[SynthesisNode] Synthesis complete (Day 3 stub)")
        
        # Day 4: Will implement actual synthesis
        state["root_cause"] = {
            "summary": "Multiple issues detected across domains",
            "agent_count": len(agent_outputs)
        }
        
        return state


class SelfReflectionAgent:
    """
    Audits reasoning quality and detects conflicts.
    
    Day 3: Pass-through with logging
    Day 4: Actual reflection logic
    """
    def __call__(self, state: MVPState) -> MVPState:
        logger.info("[SelfReflectionAgent] Auditing agent outputs...")
        
        agent_outputs = state.get("agent_outputs", {})
        
        # Simple quality check
        for agent_name, output in agent_outputs.items():
            confidence = output.get("confidence", 0)
            if confidence < 0.5:
                logger.warning(
                    f"  ⚠️  {agent_name} has low confidence: {confidence:.2%}"
                )
        
        logger.info("[SelfReflectionAgent] Reflection complete (Day 3 stub)")
        
        # Day 4: Will implement conflict detection
        return state


class HITLGate:
    """
    Human-in-the-loop approval gate.
    
    Day 3: Pass-through with logging
    Day 5: Actual HITL logic
    """
    def __call__(self, state: MVPState) -> MVPState:
        logger.info("[HITLGate] Human approval gate (Day 3 stub)")
        
        # Day 5: Will implement actual approval logic
        state["hitl_decision"] = {
            "approved": True,
            "timestamp": None,
            "note": "Auto-approved (Day 3)"
        }
        
        return state


# ==================== ROUTING LOGIC ====================

# Agent execution priority (for sequential data sharing)
AGENT_PRIORITY = ["inventory", "sales", "marketing", "support"]


def get_next_agent(state: MVPState) -> str:
    """
    Determine the next agent to execute.
    
    Executes agents sequentially in priority order to enable data sharing.
    Each agent can see outputs from previously executed agents.
    
    Returns:
        Next agent name or "synthesis" if all done
    """
    agents_to_call = state.get("agents_to_call", [])
    agents_completed = state.get("agents_completed", [])
    
    if not agents_to_call:
        logger.info("[Router] No agents to call, moving to synthesis")
        return "synthesis"
    
    # Find next agent in priority order that hasn't been completed
    for agent in AGENT_PRIORITY:
        if agent in agents_to_call and agent not in agents_completed:
            logger.info(f"[Router] Next agent: {agent}")
            return agent
    
    # All agents completed
    logger.info("[Router] All agents completed, moving to synthesis")
    return "synthesis"


def mark_agent_complete(agent_name: str):
    """
    Create a function that marks an agent as completed.
    
    Used to update state after each agent execution.
    """
    def marker(state: MVPState) -> MVPState:
        if "agents_completed" not in state:
            state["agents_completed"] = []
        
        if agent_name not in state["agents_completed"]:
            state["agents_completed"].append(agent_name)
            logger.info(f"[Router] Marked {agent_name} as complete")
        
        return state
    
    return marker


# ==================== AGENT WRAPPERS (for state tracking) ====================

class AgentWrapper:
    """
    Wraps an agent to add state tracking.
    
    Tracks which agents have completed for routing logic.
    """
    def __init__(self, agent, agent_name: str):
        self.agent = agent
        self.agent_name = agent_name
    
    def __call__(self, state: MVPState) -> MVPState:
        # Execute agent
        state = self.agent(state)
        
        # Mark as completed
        if "agents_completed" not in state:
            state["agents_completed"] = []
        
        if self.agent_name not in state["agents_completed"]:
            state["agents_completed"].append(self.agent_name)
        
        return state


# ==================== GRAPH CONSTRUCTION ====================

def build_graph() -> StateGraph:
    """
    Builds the complete LangGraph flow.
    
    Flow:
        User Input → Supervisor → 
        [Inventory → Sales → Marketing → Support] (sequential with data sharing) →
        Synthesis → Reflection → HITL → END
    
    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(MVPState)
    
    logger.info("[Graph] Building graph...")
    
    # ==================== ADD NODES ====================
    
    # Supervisor (Day 2 - production)
    graph.add_node("supervisor", SupervisorAgent())
    
    # Domain agents (Day 3 - production with data sharing)
    graph.add_node("inventory", AgentWrapper(InventoryAgent(), "inventory"))
    graph.add_node("sales", AgentWrapper(SalesAgent(), "sales"))
    graph.add_node("marketing", AgentWrapper(MarketingAgent(), "marketing"))
    graph.add_node("support", AgentWrapper(SupportAgent(), "support"))
    
    # Synthesis, reflection, HITL (Day 3 - stubs)
    graph.add_node("synthesis", SynthesisNode())
    graph.add_node("reflection", SelfReflectionAgent())
    graph.add_node("hitl", HITLGate())
    
    logger.info("[Graph] All nodes added")
    
    # ==================== SET ENTRY POINT ====================
    
    graph.set_entry_point("supervisor")
    
    # ==================== ADD EDGES ====================
    
    # Supervisor → First Agent (or synthesis if no agents)
    graph.add_conditional_edges(
        "supervisor",
        get_next_agent,
        {
            "inventory": "inventory",
            "sales": "sales",
            "marketing": "marketing",
            "support": "support",
            "synthesis": "synthesis"
        }
    )
    
    # Each agent → Next Agent (or synthesis if done)
    # This enables sequential execution with data sharing
    for agent_name in AGENT_PRIORITY:
        graph.add_conditional_edges(
            agent_name,
            get_next_agent,
            {
                "inventory": "inventory",
                "sales": "sales",
                "marketing": "marketing",
                "support": "support",
                "synthesis": "synthesis"
            }
        )
    
    # Linear flow after synthesis
    graph.add_edge("synthesis", "reflection")
    graph.add_edge("reflection", "hitl")
    graph.add_edge("hitl", END)
    
    logger.info("[Graph] All edges added")
    logger.info("[Graph] Graph construction complete")
    
    return graph.compile()


# ==================== CONVENIENCE FUNCTION ====================

def run_graph(question: str) -> MVPState:
    """
    Run the complete graph with a question.
    
    Args:
        question: User's input question
    
    Returns:
        Final state after execution
    
    Example:
        >>> final_state = run_graph("Why did sales drop yesterday?")
        >>> print(final_state["agent_outputs"]["sales"]["finding"])
    """
    logger.info(f"[Graph] Starting execution with question: '{question}'")
    
    graph = build_graph()
    
    initial_state: MVPState = {
        "question": question,
        "intent": "",
        "agents_to_call": [],
        "agent_outputs": {},
        "agents_completed": []
    }
    
    try:
        final_state = graph.invoke(initial_state)
        logger.info("[Graph] Execution complete")
        
        # Log summary
        logger.info(f"[Graph] Intent: {final_state.get('intent', 'N/A')}")
        logger.info(f"[Graph] Agents called: {final_state.get('agents_to_call', [])}")
        logger.info(f"[Graph] Agents completed: {final_state.get('agents_completed', [])}")
        
        return final_state
    
    except Exception as e:
        logger.error(f"[Graph] Execution failed: {e}", exc_info=True)
        initial_state["error"] = str(e)
        return initial_state


def get_agent_findings(state: MVPState) -> Dict[str, str]:
    """
    Extract just the findings from agent outputs.
    
    Utility function for easier result access.
    
    Args:
        state: Final state from graph execution
    
    Returns:
        Dict mapping agent name to finding string
    """
    agent_outputs = state.get("agent_outputs", {})
    return {
        agent: output.get("finding", "No finding")
        for agent, output in agent_outputs.items()
    }


def get_highest_confidence_agent(state: MVPState) -> tuple:
    """
    Get the agent with highest confidence.
    
    Utility function to identify most confident finding.
    
    Args:
        state: Final state from graph execution
    
    Returns:
        Tuple of (agent_name, confidence_score)
    """
    agent_outputs = state.get("agent_outputs", {})
    
    if not agent_outputs:
        return (None, 0.0)
    
    highest = max(
        agent_outputs.items(),
        key=lambda x: x[1].get("confidence", 0)
    )
    
    return (highest[0], highest[1].get("confidence", 0))