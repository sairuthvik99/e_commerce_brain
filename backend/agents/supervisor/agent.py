"""
Supervisor Agent - Simple LLM-Based Intent Detection and Routing

Uses direct LLM calls to classify user intent and route to appropriate domain agents.
This is a lightweight supervisor that doesn't use complex tool orchestration.
All methods are traced via Langfuse for observability.
"""

from backend.schemas.agent_output import AgentOutput
from .router import route_agents
from backend.settings import Settings
from backend.utils.prompt_loader import load_prompt
from langchain_openai import AzureChatOpenAI
from langfuse import observe
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Simple LLM-Based Supervisor Agent.
    
    The SupervisorAgent is responsible for:
    - Detecting intent from user questions using direct LLM calls
    - Routing to appropriate domain agents based on intent
    - Keeping the orchestration simple and maintainable
    
    All methods are traced via Langfuse.
    """
    
    VALID_INTENTS = {
        "sales", 
        "inventory", 
        "marketing", 
        "support", 
        "general",
        "unknown"
    }
    
    def __init__(self):
        """
        Initialize the supervisor agent with LLM.
        Uses prompt-based intent classification without complex tools.
        """
        try:
            self.llm = AzureChatOpenAI(
                api_key=Settings.DIAL_API_KEY,
                azure_endpoint=Settings.AZURE_ENDPOINT,
                api_version=Settings.API_VERSION,
                model=Settings.AGENT_MODELS.get("supervisor", "gpt-4"),
                temperature=0.1,  # Low temperature for consistent classification
            )
            
            logger.info(
                f"[SupervisorAgent] Initialized with model: "
                f"{Settings.AGENT_MODELS.get('supervisor', 'gpt-4')}"
            )
        except Exception as e:
            logger.error(f"[SupervisorAgent] Failed to initialize LLM: {e}")
            raise

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
            # Load prompts from markdown files
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
            
            # Invoke LLM for intent classification
            response = self.llm.invoke(messages)
            intent = response.content.strip().lower()
            
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
            
            # Step 1: Detect intent using LLM
            intent = self.detect_intent(question)
            
            # Step 2: Route to appropriate agents based on intent
            agents_to_call = route_agents(intent)
            
            # Update state
            state["intent"] = intent
            state["agents_to_call"] = agents_to_call
            state["agent_outputs"] = {}
            
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