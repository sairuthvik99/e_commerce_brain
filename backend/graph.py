"""
LangGraph Flow Definition

Wires together the complete agentic system using new BaseAgent architecture.
All graph operations are traced via Langfuse for observability.

Flow:
    User Input → Supervisor → Domain Agents (sequential with data sharing) → 
    Synthesis → Reflection → HITL → END

Data Sharing Strategy:
    Agents execute sequentially in priority order (inventory → sales → marketing → support)
    so each agent can access previous agents' findings in their context.
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict, List, Optional
from datetime import datetime
from langfuse import observe
from .settings import Settings

from .agents.sales.agent import SalesAgent
from .agents.inventory.agent import InventoryAgent
from .agents.marketing.agent import MarketingAgent
from .agents.support.agent import SupportAgent
from .agents.general.agent import GeneralAgent
from .agents.supervisor.agent import SupervisorAgent

# Synthesis and Reflection implementations
from .synthesis.synthesis import SynthesisAgent
from .reflection.agent import SelfReflectionAgent
from .vector_db.history_store import HistoryStore
from .schemas.root_cause import RootCause
from .schemas.reflection_result import ReflectionResult

# Memory modules
from .memory.checkpointer import get_config, ShortTermMemory
from .memory.long_term_memory import LongTermMemory

import logging
import threading

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
        conversation_history: Recent conversation context (last 10 messages)
        root_cause: Synthesized root cause (RootCause model)
        causal_chain: Ordered list of agents in causal chain
        reflection_result: Result of reflection audit (ReflectionResult model)
        quality_score: Overall quality score from reflection
        conflicts: List of detected conflicts between agents
        action_proposal: Proposed action
        hitl_decision: Human decision
        timestamp: Timestamp of analysis
        error: Error message if something fails
    """
    question: str
    intent: str
    agents_to_call: List[str]
    agent_outputs: Dict[str, Dict[str, Any]]
    agents_completed: List[str]
    conversation_history: List[Dict[str, Any]]  # Short-term memory
    long_term_context: str  # Long-term memory context
    root_cause: Dict[str, Any]  # RootCause model
    causal_chain: List[str]
    reflection_result: Dict[str, Any]  # ReflectionResult model
    quality_score: float
    conflicts: List[str]
    action_proposal: Dict[str, Any]
    hitl_decision: Dict[str, Any]
    timestamp: str
    error: str


# ==================== PERSIST ANALYSIS NODE ====================

class PersistAnalysisNode:
    """
    Persists completed analysis to Vector DB for historical reference.
    Traced via Langfuse @observe decorator.
    
    Stores:
        - Question and intent
        - Root cause analysis
        - Reflection results
        - Agent outputs
        - Timestamp
    """
    def __init__(self):
        self._history_store = None
    
    @property
    def history_store(self):
        """Lazy initialization of history store."""
        if self._history_store is None:
            try:
                self._history_store = HistoryStore()
            except Exception as e:
                logger.warning(f"[PersistAnalysis] Failed to initialize HistoryStore: {e}")
                self._history_store = None
        return self._history_store
    
    @observe(name="persist_analysis_node")
    def __call__(self, state: MVPState) -> MVPState:
        logger.info("[PersistAnalysis] Saving analysis to Vector DB...")
        
        # Build analysis document
        analysis = {
            "question": state.get("question", ""),
            "intent": state.get("intent", ""),
            "root_cause": state.get("root_cause", {}),
            "reflection_result": state.get("reflection_result", {}),
            "agent_outputs": state.get("agent_outputs", {}),
            "quality_score": state.get("quality_score", 0.0),
            "conflicts": state.get("conflicts", []),
            "causal_chain": state.get("causal_chain", []),
            "timestamp": state.get("timestamp", datetime.utcnow().isoformat())
        }
        
        # Persist to Vector DB
        if self.history_store:
            try:
                self.history_store.save_analysis(analysis)
                logger.info("[PersistAnalysis] Analysis saved successfully")
            except Exception as e:
                logger.error(f"[PersistAnalysis] Failed to save analysis: {e}")
        else:
            logger.warning("[PersistAnalysis] HistoryStore not available, skipping persistence")
        
        return state


# ==================== HITL GATE ====================

class HITLGate:
    """
    Human-in-the-loop approval gate.
    Traced via Langfuse @observe decorator.
    """
    @observe(name="hitl_gate")
    def __call__(self, state: MVPState) -> MVPState:
        logger.info("[HITLGate] Human approval gate")
        
        # Will implement actual approval logic
        state["hitl_decision"] = {
            "approved": True,
            "timestamp": None,
            "note": "Approved by HITL gate"
        }
        
        return state


# ==================== ROUTING LOGIC ====================

# Agent execution priority (for sequential data sharing)
# General agent is last as it may need context from other agents
AGENT_PRIORITY = ["inventory", "sales", "marketing", "support", "general"]


# ==================== MEMORY LOADER NODE ====================

class MemoryLoaderNode:
    """
    Loads conversation history from short-term memory.
    Injects recent context into the state for agents to use.
    """
    def __init__(self):
        self._memory = None
    
    @property
    def memory(self):
        """Lazy initialization of memory store."""
        if self._memory is None:
            try:
                self._memory = ShortTermMemory()
            except Exception as e:
                logger.warning(f"[MemoryLoader] Failed to initialize ShortTermMemory: {e}")
        return self._memory
    
    @observe(name="memory_loader_node")
    def __call__(self, state: MVPState) -> MVPState:
        """Load conversation history into state."""
        logger.info("[MemoryLoader] Loading conversation history...")
        
        if self.memory:
            try:
                history = self.memory.get_conversation_history(limit=10)
                state["conversation_history"] = history
                logger.info(f"[MemoryLoader] Loaded {len(history)} conversation entries")
            except Exception as e:
                logger.warning(f"[MemoryLoader] Failed to load history: {e}")
                state["conversation_history"] = []
        else:
            state["conversation_history"] = []
        
        return state


# ==================== LONG-TERM MEMORY LOADER NODE ====================

class LongTermMemoryLoaderNode:
    """
    Loads long-term memory context (preferences, facts, knowledge).
    Injects persistent context into the state for agents to use.
    """
    def __init__(self):
        self._memory = None
    
    @property
    def memory(self):
        """Lazy initialization of long-term memory store."""
        if self._memory is None:
            try:
                self._memory = LongTermMemory()
            except Exception as e:
                logger.warning(f"[LongTermMemoryLoader] Failed to initialize LongTermMemory: {e}")
        return self._memory
    
    @observe(name="long_term_memory_loader_node")
    def __call__(self, state: MVPState) -> MVPState:
        """Load long-term memory context into state."""
        logger.info("[LongTermMemoryLoader] Loading long-term memory...")
        
        if self.memory:
            try:
                context = self.memory.get_memory_context()
                state["long_term_context"] = context
                logger.info(f"[LongTermMemoryLoader] Loaded long-term context ({len(context)} chars)")
            except Exception as e:
                logger.warning(f"[LongTermMemoryLoader] Failed to load context: {e}")
                state["long_term_context"] = ""
        else:
            state["long_term_context"] = ""
        
        return state


# ==================== MEMORY SAVER NODE ====================

class MemorySaverNode:
    """
    Saves the current conversation to short-term memory.
    Called after synthesis to store the Q&A pair.
    """
    def __init__(self):
        self._memory = None
    
    @property
    def memory(self):
        """Lazy initialization of memory store."""
        if self._memory is None:
            try:
                self._memory = ShortTermMemory()
            except Exception as e:
                logger.warning(f"[MemorySaver] Failed to initialize ShortTermMemory: {e}")
        return self._memory
    
    @observe(name="memory_saver_node")
    def __call__(self, state: MVPState) -> MVPState:
        """Save current conversation to memory."""
        logger.info("[MemorySaver] Saving conversation to memory...")
        
        if self.memory:
            try:
                # Extract response from root_cause or synthesis
                root_cause = state.get("root_cause", {})
                response = root_cause.get("summary", "") or root_cause.get("description", "")
                
                # If no summary, try to build from agent outputs
                if not response:
                    agent_outputs = state.get("agent_outputs", {})
                    findings = [
                        output.get("finding", "")
                        for output in agent_outputs.values()
                        if output.get("finding")
                    ]
                    response = " | ".join(findings[:3]) if findings else "No response generated"
                
                self.memory.save_conversation(
                    question=state.get("question", ""),
                    response=response,
                    intent=state.get("intent", ""),
                    agent_outputs=state.get("agent_outputs"),
                    root_cause=root_cause
                )
                logger.info("[MemorySaver] Conversation saved successfully")
                
            except Exception as e:
                logger.error(f"[MemorySaver] Failed to save conversation: {e}")
        
        return state


# ==================== LONG-TERM MEMORY SAVER NODE ====================

class LongTermMemorySaverNode:
    """
    Saves insights from analysis to long-term memory.
    Extracts knowledge from root cause analysis and agent findings.
    """
    def __init__(self):
        self._memory = None
    
    @property
    def memory(self):
        """Lazy initialization of long-term memory store."""
        if self._memory is None:
            try:
                self._memory = LongTermMemory()
            except Exception as e:
                logger.warning(f"[LongTermMemorySaver] Failed to initialize LongTermMemory: {e}")
        return self._memory
    
    @observe(name="long_term_memory_saver_node")
    def __call__(self, state: MVPState) -> MVPState:
        """Extract and save insights to long-term memory."""
        logger.info("[LongTermMemorySaver] Analyzing for long-term insights...")
        
        if not self.memory:
            return state
        
        try:
            root_cause = state.get("root_cause", {})
            agent_outputs = state.get("agent_outputs", {})
            intent = state.get("intent", "")
            question = state.get("question", "")
            
            # Extract and save knowledge from root cause analysis
            if root_cause:
                # Save the primary cause as knowledge if it's significant
                primary_cause = root_cause.get("primary_cause", "")
                summary = root_cause.get("summary", "")
                confidence = root_cause.get("confidence", 0)
                
                # Only save high-confidence insights (> 0.7)
                if primary_cause and confidence and confidence > 0.7:
                    self.memory.save_knowledge(
                        topic=f"Analysis: {intent}",
                        content=f"Root Cause: {primary_cause}. {summary}",
                        source="analysis"
                    )
                    logger.info(f"[LongTermMemorySaver] Saved knowledge from analysis")
                
                # Save contributing factors as facts
                contributing_factors = root_cause.get("contributing_factors", [])
                for i, factor in enumerate(contributing_factors[:3]):  # Limit to top 3
                    if isinstance(factor, str) and len(factor) > 10:
                        self.memory.save_fact(
                            fact=factor,
                            category="contributing_factor"
                        )
                        logger.info(f"[LongTermMemorySaver] Saved contributing factor as fact")
            
            # Extract insights from agent outputs
            for agent_name, output in agent_outputs.items():
                if isinstance(output, dict):
                    # Save significant findings as knowledge
                    finding = output.get("finding", "")
                    confidence = output.get("confidence", 0)
                    
                    if finding and confidence and confidence > 0.8 and len(finding) > 50:
                        self.memory.save_knowledge(
                            topic=f"{agent_name.title()} Insight",
                            content=finding[:500],  # Limit content length
                            source=f"agent_{agent_name}"
                        )
                        logger.info(f"[LongTermMemorySaver] Saved knowledge from {agent_name}")
            
            logger.info("[LongTermMemorySaver] Long-term memory analysis complete")
            
        except Exception as e:
            logger.error(f"[LongTermMemorySaver] Failed to save to long-term memory: {e}")
        
        return state


# ==================== GRAPH MANAGER (Singleton) ====================

class GraphManager:
    """
    Singleton manager for the LangGraph instance.
    
    Ensures the graph and all agents are initialized only once
    and reused across all requests. Thread-safe implementation.
    """
    _instance: Optional['GraphManager'] = None
    _lock: threading.Lock = threading.Lock()
    _graph = None
    _initialized: bool = False
    
    def __new__(cls) -> 'GraphManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if not GraphManager._initialized:
            with GraphManager._lock:
                if not GraphManager._initialized:
                    logger.info("[GraphManager] Initializing singleton instance...")
                    self._build_graph()
                    GraphManager._initialized = True
                    logger.info("[GraphManager] Singleton initialization complete")
    
    def _build_graph(self) -> None:
        """Build and cache the compiled graph."""
        graph = StateGraph(MVPState)
        
        logger.info("[GraphManager] Building graph...")
        
        # ==================== ADD NODES ====================
        
        # Memory loaders (load both short-term and long-term memory at the start)
        graph.add_node("load_memory", MemoryLoaderNode())
        graph.add_node("load_long_term_memory", LongTermMemoryLoaderNode())
        
        # Supervisor
        graph.add_node("supervisor", SupervisorAgent())
        
        # Domain agents
        graph.add_node("inventory", AgentWrapper(InventoryAgent(), "inventory"))
        graph.add_node("sales", AgentWrapper(SalesAgent(), "sales"))
        graph.add_node("marketing", AgentWrapper(MarketingAgent(), "marketing"))
        graph.add_node("support", AgentWrapper(SupportAgent(), "support"))
        
        # General agent (handles general/unknown intents)
        graph.add_node("general", AgentWrapper(GeneralAgent(), "general"))
        
        # Synthesis and reflection
        graph.add_node("synthesis", SynthesisAgent())
        graph.add_node("reflection", SelfReflectionAgent())
        
        # Memory saver (saves conversation after synthesis)
        graph.add_node("save_memory", MemorySaverNode())
        
        # Long-term memory saver (extracts and saves insights)
        graph.add_node("save_long_term_memory", LongTermMemorySaverNode())
        
        # Persist analysis to Vector DB
        graph.add_node("persist_analysis", PersistAnalysisNode())
        
        # HITL gate 
        graph.add_node("hitl", HITLGate())
        
        logger.info("[GraphManager] All nodes added")
        
        # ==================== SET ENTRY POINT ====================
        
        # Start with loading short-term memory
        graph.set_entry_point("load_memory")
        
        # ==================== ADD EDGES ====================
        
        # Load memory → Load long-term memory → Supervisor
        graph.add_edge("load_memory", "load_long_term_memory")
        graph.add_edge("load_long_term_memory", "supervisor")
        
        # Supervisor → First Agent (or synthesis if no agents)
        graph.add_conditional_edges(
            "supervisor",
            get_next_agent,
            {
                "inventory": "inventory",
                "sales": "sales",
                "marketing": "marketing",
                "support": "support",
                "general": "general",
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
                    "general": "general",
                    "synthesis": "synthesis"
                }
            )
        
        # Linear flow after synthesis
        graph.add_edge("synthesis", "save_memory")  # Save to memory after synthesis
        graph.add_edge("save_memory", "save_long_term_memory")  # Save long-term insights
        graph.add_edge("save_long_term_memory", "reflection")
        graph.add_edge("reflection", "persist_analysis")
        graph.add_edge("persist_analysis", "hitl")
        graph.add_edge("hitl", END)
        
        logger.info("[GraphManager] All edges added")
        
        GraphManager._graph = graph.compile()
        logger.info("[GraphManager] Graph compilation complete")
    
    @property
    def graph(self):
        """Get the compiled graph instance."""
        return GraphManager._graph
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the graph manager has been initialized."""
        return cls._initialized
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton (mainly for testing purposes).
        
        Warning: This will cause re-initialization on next access.
        """
        with cls._lock:
            cls._instance = None
            cls._graph = None
            cls._initialized = False
            logger.info("[GraphManager] Singleton reset")


def get_graph_manager() -> GraphManager:
    """
    Get the singleton GraphManager instance.
    
    Returns:
        GraphManager: The singleton instance
    """
    return GraphManager()


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
    Traced via Langfuse @observe decorator.
    
    Tracks which agents have completed for routing logic.
    """
    def __init__(self, agent, agent_name: str):
        self.agent = agent
        self.agent_name = agent_name
    
    @observe(name="agent_wrapper")
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
    
    Uses singleton GraphManager to ensure agents and graph are 
    initialized only once and reused across all requests.
    
    Flow:
        User Input → Supervisor → 
        [Inventory → Sales → Marketing → Support → General] (sequential with data sharing) →
        Synthesis → Reflection → HITL → END
    
    Returns:
        Compiled StateGraph
    """
    manager = get_graph_manager()
    return manager.graph


# ==================== CONVENIENCE FUNCTION ====================

@observe(name="run_graph")
def run_graph(question: str) -> MVPState:
    """
    Run the complete graph with a question.
    Traced via Langfuse @observe decorator.
    
    Uses singleton GraphManager to reuse the compiled graph
    instead of rebuilding it for every request.
    
    Flow includes short-term memory:
        Load Memory → Supervisor → Agents → Synthesis → Save Memory → Reflection → HITL → END
    
    Args:
        question: User's input question
    
    Returns:
        Final state after execution
    
    Example:
        >>> final_state = run_graph("Why did sales drop yesterday?")
        >>> print(final_state["agent_outputs"]["sales"]["finding"])
    """
    logger.info(f"[Graph] Starting execution with question: '{question}'")
    
    # Get the cached graph from singleton manager
    graph = build_graph()
    
    initial_state: MVPState = {
        "question": question,
        "intent": "",
        "agents_to_call": [],
        "agent_outputs": {},
        "agents_completed": [],
        "conversation_history": [],  # Will be loaded by MemoryLoaderNode
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        final_state = graph.invoke(initial_state)
        logger.info("[Graph] Execution complete")
        
        # Log summary
        logger.info(f"[Graph] Intent: {final_state.get('intent', 'N/A')}")
        logger.info(f"[Graph] Agents called: {final_state.get('agents_to_call', [])}")
        logger.info(f"[Graph] Agents completed: {final_state.get('agents_completed', [])}")
        logger.info(f"[Graph] Conversation history size: {len(final_state.get('conversation_history', []))}")
        
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


# Alias for backward compatibility
create_graph = build_graph