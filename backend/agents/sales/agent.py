"""
Sales Agent Implementation (LLM-Driven)

Uses LangChain tools for LLM-driven sales analysis.
The LLM decides what's happening based on data and question.
Supports cross-domain access for queries involving inventory/marketing correlation.
"""

from typing import Dict, Any, Optional, List
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from langfuse import observe
from pydantic import BaseModel, Field

from backend.settings import Settings
from backend.utils.agent_data_loader import AgentDataLoader
from backend.utils.prompt_loader import load_prompt
from backend.schemas.agent_output import AgentOutput
from .tools import get_sales_tools, SalesLLMAnalyzer

import logging
import json

logger = logging.getLogger(__name__)


class SalesAgentContext(BaseModel):
    """Context for sales agent execution."""
    question: str = Field(description="User's question")
    intent: str = Field(default="sales", description="Detected intent")
    other_agent_outputs: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Outputs from other agents"
    )


class SalesAgent:
    """
    LLM-Driven Sales Agent.
    
    Instead of hardcoded analysis logic, this agent:
    1. Receives the user's question
    2. Loads relevant data
    3. Uses LLM with tools to analyze and answer
    4. Returns only the LLM's response
    
    Supports two modes:
    - Tool mode: Uses LangGraph agent with tools (for complex queries)
    - Direct mode: Uses single LLM call (for simple queries)
    """
    
    def __init__(
        self,
        use_tools: bool = True,
        use_direct_loader: Optional[bool] = None,
        allow_cross_domain: bool = True
    ):
        """
        Initialize sales agent.
        
        Args:
            use_tools: Whether to use LangChain tools (vs direct LLM)
            use_direct_loader: Force direct DB access (auto-detect if None)
            allow_cross_domain: Enable cross-domain data access for queries
                              that require inventory/marketing correlation
        """
        self.agent_name = "sales"
        self.use_tools = use_tools
        self.allow_cross_domain = allow_cross_domain
        
        # Initialize LLM
        self.llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS.get("sales", "gpt-4"),
            temperature=0.2,
        )
        
        # Initialize data loader with cross-domain access
        if use_direct_loader is None:
            use_direct_loader = self._is_jupyter()
        self.data_loader = AgentDataLoader(
            agent_type=self.agent_name,
            use_direct=use_direct_loader,
            allow_cross_domain=allow_cross_domain
        )
        
        # Initialize LLM analyzer for direct mode
        self.analyzer = SalesLLMAnalyzer()
        
        # Initialize tools and agent
        if use_tools:
            self._init_tool_agent()
        
        logger.info(
            f"[SalesAgent] Initialized (tools={use_tools}, "
            f"cross_domain={allow_cross_domain})"
        )
    
    @staticmethod
    def _is_jupyter() -> bool:
        """Check if running in Jupyter notebook."""
        try:
            from IPython import get_ipython
            return get_ipython() is not None
        except ImportError:
            return False
    
    def _init_tool_agent(self):
        """Initialize LangGraph agent with tools."""
        tools = get_sales_tools()
        
        # Load system prompt from prompts/system_prompt.md
        system_prompt = load_prompt(
            agent="sales",
            task="system_prompt",
            prompt_type="system"
        )
        
        # Create LangGraph agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=system_prompt,
        )
        
        logger.info("[SalesAgent] LangGraph agent initialized with tools")
    
    @observe(name="sales_agent_execute")
    def execute(self, context: SalesAgentContext) -> AgentOutput:
        """
        Execute sales analysis.
        
        This is the main entry point that:
        1. Takes the user's question
        2. Uses LLM (with or without tools) to analyze
        3. Returns structured output
        
        Args:
            context: SalesAgentContext with question and other info
            
        Returns:
            AgentOutput with finding, evidence, confidence
        """
        question = context.question
        logger.info(f"[SalesAgent] Executing for question: {question}")
        
        try:
            if self.use_tools:
                return self._execute_with_tools(question, context)
            else:
                return self._execute_direct(question, context)
                
        except Exception as e:
            logger.error(f"[SalesAgent] Execution failed: {e}")
            return AgentOutput(
                finding=f"Sales analysis failed: {str(e)}",
                evidence=["error"],
                confidence=0.0,
                agent=self.agent_name
            )
    
    def _execute_with_tools(
        self, 
        question: str, 
        context: SalesAgentContext
    ) -> AgentOutput:
        """Execute using LangGraph agent with tools."""
        logger.info("[SalesAgent] Executing with tools...")
        
        # Add context from other agents if available
        input_text = question
        if context.other_agent_outputs:
            other_context = json.dumps(context.other_agent_outputs, indent=2, default=str)
            input_text = f"{question}\n\nContext from other agents:\n{other_context}"
        
        # Run agent
        messages = [{"role": "user", "content": input_text}]
        result = self.agent.invoke({"messages": messages})
        
        # Extract the last message (agent's response)
        output_text = ""
        evidence = ["llm_analysis", "tools_used"]
        confidence = 0.85
        
        if "messages" in result:
            # Get the last AI message
            for msg in reversed(result["messages"]):
                if hasattr(msg, "content") and msg.content:
                    output_text = msg.content
                    break
        
        logger.info(f"[SalesAgent] Tool execution complete: {output_text[:100]}...")
        
        return AgentOutput(
            finding=output_text,
            evidence=evidence,
            confidence=confidence,
            agent=self.agent_name
        )
    
    def _execute_direct(
        self, 
        question: str, 
        context: SalesAgentContext
    ) -> AgentOutput:
        """Execute using direct LLM call."""
        logger.info("[SalesAgent] Executing LLM call...")
        
        # Load sales data
        sales_data = self.data_loader.load_sales_data(days=7)
        
        # Analyze using LLM
        result = self.analyzer.analyze(
            question=question,
            data=sales_data,
            analysis_type="general_sales_performance",
            additional_context=str(context.other_agent_outputs) if context.other_agent_outputs else None
        )
        
        # Extract structured response
        finding = result.get("finding", "Unable to analyze sales data.")
        evidence = result.get("evidence", ["llm_analysis"])
        confidence = result.get("confidence", 0.75)
        
        return AgentOutput(
            finding=finding,
            evidence=evidence,
            confidence=float(confidence),
            agent=self.agent_name
        )
    
    @observe(name="sales_agent_call")
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph-compatible call method.
        
        Args:
            state: Graph state with question and other data
            
        Returns:
            Updated state with agent output
        """
        context = SalesAgentContext(
            question=state.get("question", ""),
            intent=state.get("intent", "sales"),
            other_agent_outputs=state.get("agent_outputs", {})
        )
        
        output = self.execute(context)
        
        # Update state
        if "agent_outputs" not in state:
            state["agent_outputs"] = {}
        state["agent_outputs"][self.agent_name] = output.model_dump()
        
        return state
    
    def get_tool_description(self) -> str:
        """Get description for this agent when used as a tool."""
        return (
            "Analyzes sales performance including revenue, order count, "
            "and average order value. Uses LLM to identify trends, anomalies, "
            "and root causes of sales changes."
        )
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        tools = get_sales_tools()
        return [tool.name for tool in tools]