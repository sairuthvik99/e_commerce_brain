"""
Supervisor Agent - Intent Detection and Routing

Uses LLM to classify user intent and route to appropriate domain agents.
"""

from backend.schemas.agent_output import AgentOutput
from backend.supervisor.router import route_agents
from backend.settings import Settings
from backend.utils.prompt_loader import load_prompt
from langchain_openai import AzureChatOpenAI
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    The SupervisorAgent is responsible for:
    - Detecting intent from the user question using an LLM
    - Deciding which domain agents to call
    - Passing shared context to agents
    - Collecting agent outputs
    """
    
    VALID_INTENTS = {
        "sales_drop", 
        "inventory_issue", 
        "marketing_issue", 
        "support_issue", 
        "unknown"
    }
    
    def __init__(self):
        """Initialize the supervisor agent with LLM configuration."""
        try:
            self.llm = AzureChatOpenAI(
                api_key=Settings.DIAL_API_KEY,
                azure_endpoint=Settings.AZURE_ENDPOINT,
                api_version=Settings.API_VERSION,
                model=Settings.AGENT_MODELS["supervisor"],
            )
            logger.info(
                f"[SupervisorAgent] Initialized with model: "
                f"{Settings.AGENT_MODELS['supervisor']}"
            )
        except Exception as e:
            logger.error(f"[SupervisorAgent] Failed to initialize LLM: {e}")
            raise

    def detect_intent(self, question: str) -> str:
        """
        Use LLM to classify user intent.
        
        Args:
            question: User's question string
        
        Returns:
            Intent label (e.g., "sales_drop", "inventory_issue", etc.)
        
        Raises:
            ValueError: If question is empty
            RuntimeError: If LLM call fails
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
            
            # Construct messages using dict format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Call LLM
            logger.info(f"[SupervisorAgent] Calling LLM for intent detection...")
            response = self.llm.invoke(messages)
            
            # Extract and clean intent
            intent = response.content.strip().lower()
            
            # Fallback if intent is not recognized
            if intent not in self.VALID_INTENTS:
                logger.warning(
                    f"[SupervisorAgent] LLM returned unrecognized intent: '{intent}'. "
                    f"Defaulting to 'unknown'."
                )
                intent = "unknown"
            
            logger.info(f"[SupervisorAgent] Detected intent: {intent}")
            return intent
        
        except FileNotFoundError as e:
            logger.error(f"[SupervisorAgent] Prompt file not found: {e}")
            raise RuntimeError(f"Failed to load prompts: {e}")
        
        except Exception as e:
            logger.error(f"[SupervisorAgent] Intent detection failed: {e}")
            raise RuntimeError(f"Intent detection failed: {e}")

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method called by LangGraph.
        
        Args:
            state: Current graph state containing at least 'question'
        
        Returns:
            Updated state with intent, agents_to_call, and agent_outputs
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
            
            # Detect intent
            intent = self.detect_intent(question)
            
            # Route to appropriate agents
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
            # Graceful degradation
            state["intent"] = "unknown"
            state["agents_to_call"] = []
            state["agent_outputs"] = {}
            state["error"] = str(e)
            return state