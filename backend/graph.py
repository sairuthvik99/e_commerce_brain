"""
LangGraph Flow Definition

Wires together the complete agentic system:
- Supervisor (intent + routing)
- Domain agents (parallel execution based on routing)
- Synthesis
- Self-reflection
- HITL gate

ARCHITECTURE NOTE:
- SupervisorAgent: Imported from supervisor/agent.py (production code)
- BaseAgent: Defined here as DAY 2 STUB (will move to agents/ on Day 3)
- SynthesisNode, SelfReflectionAgent, HITLGate: Stubs for Day 4-5
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict, List
from .settings import Settings
from .schemas.agent_output import AgentOutput

# --- PRODUCTION IMPORTS (Day 2+) ---
from .supervisor.agent import SupervisorAgent  # ✅ Production agent

from langchain_openai import AzureChatOpenAI
import logging

logger = logging.getLogger(__name__)


# --- State Definition ---
class MVPState(TypedDict, total=False):
    """
    Canonical state that flows through the graph.
    
    Fields:
        question: User's input question
        intent: Detected intent (e.g., 'sales_drop')
        agents_to_call: List of agent names to execute
        agent_outputs: Dict mapping agent name to AgentOutput
        root_cause: Synthesized root cause (Day 4)
        action_proposal: Proposed action (Day 5)
        hitl_decision: Human decision (Day 5)
        error: Error message if something fails
    """
    question: str
    intent: str
    agents_to_call: List[str]
    agent_outputs: Dict[str, Dict[str, Any]]
    root_cause: Dict[str, Any]
    action_proposal: Dict[str, Any]
    hitl_decision: Dict[str, Any]
    error: str


# --- TEMPORARY STUB: BaseAgent (Day 2) ---
# TODO (Day 3): Move to individual agent files:
#   - backend/agents/sales/agent.py
#   - backend/agents/inventory/agent.py
#   - backend/agents/marketing/agent.py
#   - backend/agents/support/agent.py
class BaseAgent:
    """
    ⚠️ DAY 2 STUB: Temporary base class for domain agents.
    
    This will be replaced on Day 3 with individual agent implementations
    that include real reasoning logic and mock data integration.
    
    For Day 2: Returns stub outputs to validate graph flow.
    """
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        try:
            self.llm = AzureChatOpenAI(
                api_key=Settings.DIAL_API_KEY,
                azure_endpoint=Settings.AZURE_ENDPOINT,
                api_version=Settings.API_VERSION,
                model=Settings.AGENT_MODELS.get(agent_name, Settings.AGENT_MODELS["supervisor"]),
            )
            logger.info(f"[{self.agent_name}Agent] Initialized successfully")
        except Exception as e:
            logger.error(f"[{self.agent_name}Agent] Failed to initialize: {e}")
            raise

    def __call__(self, state: MVPState) -> MVPState:
        """
        Execute the agent's reasoning (Day 2: stub, Day 3: real logic).
        """
        try:
            logger.info(f"[{self.agent_name}Agent] Executing...")
            
            # Day 2 Stub: Return placeholder output
            output = AgentOutput(
                finding=f"[STUB] {self.agent_name.capitalize()} agent detected potential issues.",
                evidence=[f"{self.agent_name}_metric_1", f"{self.agent_name}_metric_2"],
                confidence=0.85,
                agent=self.agent_name
            )
            
            # Store output in state
            if "agent_outputs" not in state:
                state["agent_outputs"] = {}
            
            state["agent_outputs"][self.agent_name] = output.dict()
            
            logger.info(
                f"[{self.agent_name}Agent] Output: {output.finding} "
                f"(confidence: {output.confidence})"
            )
            
            return state
        
        except Exception as e:
            logger.error(f"[{self.agent_name}Agent] Execution failed: {e}")
            state["agent_outputs"][self.agent_name] = {
                "finding": f"Error in {self.agent_name} agent",
                "evidence": [],
                "confidence": 0.0,
                "agent": self.agent_name,
                "error": str(e)
            }
            return state


# --- TEMPORARY STUBS: Placeholder Nodes (Day 4-6) ---
# TODO (Day 4): Move SynthesisNode to backend/supervisor/synthesis.py
# TODO (Day 4): Move SelfReflectionAgent to backend/reflection/agent.py
# TODO (Day 5): Move HITLGate to backend/hitl/gate.py

class SynthesisNode:
    """
    ⚠️ DAY 2 STUB: Synthesizes agent outputs into root cause.
    
    Day 2: Pass-through
    Day 4: Will implement actual synthesis logic
    """
    def __call__(self, state: MVPState) -> MVPState:
        logger.info("[SynthesisNode] Passing state forward (Day 2 stub)")
        # Day 4: Will implement root cause synthesis
        return state


class SelfReflectionAgent:
    """
    ⚠️ DAY 2 STUB: Audits reasoning quality and detects conflicts.
    
    Day 2: Pass-through
    Day 4: Will implement actual reflection logic
    """
    def __call__(self, state: MVPState) -> MVPState:
        logger.info("[SelfReflectionAgent] Passing state forward (Day 2 stub)")
        # Day 4: Will implement conflict detection
        return state


class HITLGate:
    """
    ⚠️ DAY 2 STUB: Human-in-the-loop approval gate.
    
    Day 2: Pass-through
    Day 5: Will implement actual HITL logic
    """
    def __call__(self, state: MVPState) -> MVPState:
        logger.info("[HITLGate] Passing state forward (Day 2 stub)")
        # Day 5: Will implement approval logic
        return state


# --- Dynamic Routing Logic ---
def route_to_agents(state: MVPState) -> List[str]:
    """
    Determines which agents to call based on supervisor's routing decision.
    
    Returns:
        List of agent names to execute
    """
    agents = state.get("agents_to_call", [])
    logger.info(f"[Router] Routing to: {agents}")
    
    # If no agents specified, skip to synthesis
    if not agents:
        return ["synthesis"]
    
    return agents


# --- Graph Construction ---
def build_graph() -> StateGraph:
    """
    Builds the complete LangGraph flow.
    
    Flow:
        User Input → Supervisor → Domain Agents (parallel) → 
        Synthesis → Reflection → HITL → END
    """
    graph = StateGraph(MVPState)
    
    # Add nodes
    logger.info("[Graph] Adding nodes...")
    
    # Production agent (imported)
    graph.add_node("supervisor", SupervisorAgent())  # ✅ From supervisor/agent.py
    
    # Stub agents (defined in this file, Day 2 only)
    graph.add_node("sales", BaseAgent("sales"))
    graph.add_node("inventory", BaseAgent("inventory"))
    graph.add_node("marketing", BaseAgent("marketing"))
    graph.add_node("support", BaseAgent("support"))
    
    # Stub nodes (defined in this file, will move later)
    graph.add_node("synthesis", SynthesisNode())
    graph.add_node("reflection", SelfReflectionAgent())
    graph.add_node("hitl", HITLGate())
    
    # Entry point
    graph.set_entry_point("supervisor")
    
    # Dynamic routing: Supervisor → Domain Agents (based on agents_to_call)
    def supervisor_router(state: MVPState) -> str:
        """
        Routes from supervisor to first agent or directly to synthesis.
        
        For Day 2 MVP: Simple sequential routing.
        Day 3+: Can be enhanced for true parallelism.
        """
        agents = state.get("agents_to_call", [])
        if not agents:
            return "synthesis"
        # For now, route to first agent (will trigger chain)
        return agents[0] if agents else "synthesis"
    
    graph.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
            "sales": "sales",
            "inventory": "inventory",
            "marketing": "marketing",
            "support": "support",
            "synthesis": "synthesis"
        }
    )
    
    # All domain agents → synthesis
    for agent in ["sales", "inventory", "marketing", "support"]:
        graph.add_edge(agent, "synthesis")
    
    # Linear flow after synthesis
    graph.add_edge("synthesis", "reflection")
    graph.add_edge("reflection", "hitl")
    graph.add_edge("hitl", END)
    
    logger.info("[Graph] Graph construction complete")
    return graph.compile()


# --- Convenience function ---
def run_graph(question: str) -> MVPState:
    """
    Run the complete graph with a question.
    
    Args:
        question: User's input question
    
    Returns:
        Final state after execution
    """
    logger.info(f"[Graph] Starting execution with question: {question}")
    
    graph = build_graph()
    
    initial_state: MVPState = {
        "question": question,
        "intent": "",
        "agents_to_call": [],
        "agent_outputs": {}
    }
    
    try:
        final_state = graph.invoke(initial_state)
        logger.info("[Graph] Execution complete")
        return final_state
    except Exception as e:
        logger.error(f"[Graph] Execution failed: {e}")
        initial_state["error"] = str(e)
        return initial_state