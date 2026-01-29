"""
Supervisor Agent - LLM-Driven Intent Detection and Routing

Uses LangChain tools to classify user intent and route to appropriate domain agents.
All methods are traced via Langfuse for observability.
"""

from backend.schemas.agent_output import AgentOutput
from .router import route_agents
from .tools import (
    get_supervisor_tools,
    classify_user_intent,
    determine_agents_to_call,
    analyze_cross_domain_impact,
    query_past_incidents,
    generate_action_recommendations,
    prepare_hitl_action,
    generate_executive_summary,
)
from backend.settings import Settings
from backend.utils.prompt_loader import load_prompt
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from langfuse import observe
from typing import Dict, Any, List, Optional
import logging
import json

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    LLM-Driven Supervisor Agent.
    
    The SupervisorAgent is responsible for:
    - Detecting intent from user questions using LLM with tools
    - Deciding which domain agents to call
    - Handling cross-domain queries
    - Managing memory/history queries
    - Preparing action proposals for HITL
    
    All methods are traced via Langfuse.
    """
    
    VALID_INTENTS = {
        "sales", 
        "inventory", 
        "marketing", 
        "support", 
        "general",
        "memory",
        "action",
        "unknown"
    }
    
    def __init__(self, use_tools: bool = True):
        """
        Initialize the supervisor agent with LLM and tools.
        
        Args:
            use_tools: Whether to use LangChain tools (vs simple LLM)
        """
        self.use_tools = use_tools
        
        try:
            self.llm = AzureChatOpenAI(
                api_key=Settings.DIAL_API_KEY,
                azure_endpoint=Settings.AZURE_ENDPOINT,
                api_version=Settings.API_VERSION,
                model=Settings.AGENT_MODELS["supervisor"],
                temperature=0.1,
            )
            
            if use_tools:
                self._init_tool_agent()
            
            logger.info(
                f"[SupervisorAgent] Initialized with model: "
                f"{Settings.AGENT_MODELS['supervisor']} (tools={use_tools})"
            )
        except Exception as e:
            logger.error(f"[SupervisorAgent] Failed to initialize LLM: {e}")
            raise
    
    def _init_tool_agent(self):
        """Initialize LangGraph agent with supervisor tools."""
        tools = get_supervisor_tools()
        
        system_prompt = """You are a Supervisor Agent for an E-commerce Operations Brain.

Your responsibilities:
1. Classify user questions into appropriate intents
2. Decide which domain agents to call
3. Handle cross-domain queries that span multiple areas
4. Query historical memory for past incidents
5. Prepare action proposals that require human approval

Available domain agents: sales, inventory, marketing, support

Question categories you handle:
- Sales & Revenue: Why sales dropped, revenue comparisons, AOV analysis
- Inventory: Stock issues, stockouts, reordering decisions
- Marketing: Campaign performance, channel analysis, promotions
- Support: Customer complaints, refunds, reviews
- Cross-Domain: Root cause analysis spanning multiple domains
- Memory: Questions about past incidents and what worked before
- Actions: Commands to fix, restock, discount, etc. (require HITL approval)

Use the appropriate tools to analyze the question and provide routing decisions."""
        
        # Create LangGraph agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=system_prompt,
        )
        
        logger.info("[SupervisorAgent] LangGraph agent initialized")

    @observe(name="supervisor_detect_intent")
    def detect_intent(self, question: str) -> str:
        """
        Use LLM to classify user intent.
        Traced via Langfuse @observe decorator.
        
        Args:
            question: User's question string
        
        Returns:
            Intent label (e.g., "sales", "inventory", etc.)
        """
        if not question or not question.strip():
            logger.warning("[SupervisorAgent] Empty question provided")
            return "unknown"
        
        try:
            if self.use_tools:
                # Use the classify_user_intent tool directly
                result = classify_user_intent.invoke({"question": question})
                intent = result.get("intent", "unknown")
            else:
                # Fallback to simple LLM call
                intent = self._detect_intent_simple(question)
            
            # Validate intent
            if intent not in self.VALID_INTENTS:
                logger.warning(
                    f"[SupervisorAgent] Unrecognized intent: '{intent}'. "
                    f"Defaulting to 'unknown'."
                )
                intent = "unknown"
            
            logger.info(f"[SupervisorAgent] Detected intent: {intent}")
            return intent
        
        except Exception as e:
            logger.error(f"[SupervisorAgent] Intent detection failed: {e}")
            return "unknown"
    
    def _detect_intent_simple(self, question: str) -> str:
        """Simple LLM-based intent detection without tools."""
        try:
            system_prompt = load_prompt(
                agent="supervisor",
                task="intent_classification",
                prompt_type="system"
            )
            
            user_prompt = load_prompt(
                agent="supervisor",
                task="intent_classification",
                prompt_type="user",
                variables={"question": question}
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.llm.invoke(messages)
            return response.content.strip().lower()
            
        except Exception as e:
            logger.error(f"[SupervisorAgent] Simple intent detection failed: {e}")
            return "unknown"
    
    @observe(name="supervisor_route_question")
    def route_question(self, question: str, intent: str) -> Dict[str, Any]:
        """
        Determine routing based on question and intent.
        
        Args:
            question: User's question
            intent: Classified intent
            
        Returns:
            Dict with agents_to_call, priority, etc.
        """
        try:
            if self.use_tools:
                result = determine_agents_to_call.invoke({
                    "question": question,
                    "intent": intent
                })
                return result
            else:
                # Use simple routing
                agents = route_agents(intent)
                return {
                    "intent": intent,
                    "agents_to_call": agents,
                    "priority": "normal"
                }
        except Exception as e:
            logger.error(f"[SupervisorAgent] Routing failed: {e}")
            return {
                "intent": intent,
                "agents_to_call": route_agents(intent),
                "priority": "normal",
                "error": str(e)
            }
    
    @observe(name="supervisor_handle_special_intent")
    def handle_special_intent(
        self, 
        question: str, 
        intent: str,
        agent_findings: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle special intents that don't require domain agents.
        
        Args:
            question: User's question
            intent: Classified intent
            agent_findings: Findings from domain agents (if any)
            
        Returns:
            Response dict for special intents, None for normal intents
        """
        if agent_findings is None:
            agent_findings = {}
        
        try:
            if intent == "memory":
                # Query historical data
                result = query_past_incidents.invoke({
                    "question": question,
                    "query_type": "similar_incidents"
                })
                return result
            
            elif intent == "action":
                # Prepare HITL action proposal
                result = prepare_hitl_action.invoke({
                    "question": question,
                    "findings": agent_findings
                })
                return result
            
            else:
                return None
                
        except Exception as e:
            logger.error(f"[SupervisorAgent] Special intent handling failed: {e}")
            return None
    
    @observe(name="supervisor_synthesize_cross_domain")
    def synthesize_cross_domain(
        self,
        question: str,
        agent_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesize findings from multiple domain agents.
        
        Args:
            question: Original user question
            agent_outputs: Outputs from all domain agents
            
        Returns:
            Synthesized cross-domain analysis
        """
        try:
            result = analyze_cross_domain_impact.invoke({
                "question": question,
                "domains": list(agent_outputs.keys())
            })
            
            # Add agent findings context
            result["agent_findings"] = agent_outputs
            
            return result
            
        except Exception as e:
            logger.error(f"[SupervisorAgent] Cross-domain synthesis failed: {e}")
            return {
                "error": str(e),
                "agent_findings": agent_outputs
            }
    
    @observe(name="supervisor_generate_summary")
    def generate_summary(
        self,
        question: str,
        agent_outputs: Dict[str, Any],
        report_type: str = "executive_summary"
    ) -> Dict[str, Any]:
        """
        Generate a summary report from all agent findings.
        
        Args:
            question: Original question
            agent_outputs: All agent outputs
            report_type: Type of summary to generate
            
        Returns:
            Summary report
        """
        try:
            result = generate_executive_summary.invoke({
                "question": question,
                "report_type": report_type,
                "findings": agent_outputs
            })
            return result
            
        except Exception as e:
            logger.error(f"[SupervisorAgent] Summary generation failed: {e}")
            return {"error": str(e)}

    @observe(name="supervisor_call")
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method called by LangGraph.
        Traced via Langfuse @observe decorator.
        
        Args:
            state: Current graph state containing at least 'question'
        
        Returns:
            Updated state with intent, agents_to_call, and routing info
        """
        try:
            question = state.get("question", "")
            
            if not question:
                logger.error("[SupervisorAgent] No question found in state")
                state["intent"] = "unknown"
                state["agents_to_call"] = []
                state["agent_outputs"] = {}
                return state
            
            logger.info(f"[SupervisorAgent] Processing question: {question}")
            
            # Step 1: Detect intent
            intent = self.detect_intent(question)
            
            # Step 2: Get routing decision
            routing = self.route_question(question, intent)
            agents_to_call = routing.get("agents_to_call", [])
            
            # Step 3: Handle special intents (memory, action)
            special_response = self.handle_special_intent(question, intent)
            
            # Update state
            state["intent"] = intent
            state["agents_to_call"] = agents_to_call
            state["routing"] = routing
            state["agent_outputs"] = {}
            
            if special_response:
                state["special_response"] = special_response
            
            logger.info(
                f"[SupervisorAgent] Intent: {intent} | "
                f"Routing to agents: {agents_to_call}"
            )
            
            return state
        
        except Exception as e:
            logger.error(f"[SupervisorAgent] Execution failed: {e}")
            state["intent"] = "unknown"
            state["agents_to_call"] = []
            state["agent_outputs"] = {}
            state["error"] = str(e)
            return state
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        tools = get_supervisor_tools()
        return [tool.name for tool in tools]