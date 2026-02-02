"""
General Agent Implementation (LLM-Driven)

Handles general business inquiries and unknown intents.
Uses LangChain tools to access all database tables for comprehensive analysis.
The LLM decides what data is needed and synthesizes insights across domains.
"""

from typing import Dict, Any, Optional, List
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from langfuse import observe
from pydantic import BaseModel, Field

from backend.settings import Settings
from backend.utils.data_loader import DataLoader
from backend.schemas.agent_output import AgentOutput
from .tools import get_general_tools, GeneralLLMAnalyzer

import logging
import json

logger = logging.getLogger(__name__)


class GeneralAgentContext(BaseModel):
    """Context for general agent execution."""
    question: str = Field(description="User's question")
    intent: str = Field(default="general", description="Detected intent")
    other_agent_outputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Outputs from other agents"
    )


class GeneralAgent:
    """
    LLM-Driven General Agent.
    
    This agent handles:
    1. General business inquiries that span multiple domains
    2. Unknown intents that couldn't be classified
    3. Cross-domain analysis requiring data from all tables
    
    Supports two modes:
    - Tool mode: Uses LangGraph agent with tools (for complex queries)
    - Direct mode: Uses single LLM call (for simple queries)
    """
    
    def __init__(
        self,
        use_tools: bool = True,
        use_direct_loader: Optional[bool] = None
    ):
        """
        Initialize general agent.
        
        Args:
            use_tools: Whether to use LangChain tools (vs direct LLM)
            use_direct_loader: Force direct DB access (auto-detect if None)
        """
        self.agent_name = "general"
        self.use_tools = use_tools
        
        # Initialize LLM
        self.llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS["general"],
            temperature=0.3,
        )
        
        # Initialize data loader
        if use_direct_loader is None:
            use_direct_loader = self._is_jupyter()
        self.data_loader = DataLoader(use_direct=use_direct_loader)
        
        # Initialize LLM analyzer for direct mode
        self.analyzer = GeneralLLMAnalyzer()
        
        # Initialize tools and agent
        if use_tools:
            self._init_tool_agent()
        
        logger.info(f"[GeneralAgent] Initialized (tools={use_tools})")
    
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
        tools = get_general_tools()
        
        # Create system prompt for general agent
        system_prompt = """You are a General Business Intelligence Agent for an e-commerce business.
Your job is to analyze data across ALL business domains and answer comprehensive business questions.

You have access to ALL data sources:
- Sales data (revenue, orders, AOV)
- Inventory data (stock levels, stockouts)
- Marketing data (campaigns, conversions, spend)
- Support data (tickets, complaints, sentiment)
- Daily metrics (aggregated KPIs)

Use the available tools to get comprehensive analysis for the user's question.
Select the most appropriate tool(s) based on what the user is asking:
- For business health overviews: use analyze_business_health
- For cross-domain analysis: use analyze_cross_domain
- For daily summaries: use get_daily_summary
- For KPI comparisons: use compare_kpis
- For trend analysis across domains: use analyze_trends
- For specific domain data: use query_domain_data
- For correlation analysis: use find_correlations

After getting the tool result, provide a clear, concise answer to the user.
Always include specific numbers and percentages in your response.
When multiple domains are involved, synthesize insights rather than listing separately."""
        
        # Create LangGraph agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=system_prompt,
        )
        
        logger.info("[GeneralAgent] LangGraph agent initialized with tools")
    
    @observe(name="general_agent_execute")
    def execute(self, context: GeneralAgentContext) -> AgentOutput:
        """
        Execute general analysis.
        
        This is the main entry point that:
        1. Takes the user's question
        2. Uses LLM (with or without tools) to analyze
        3. Returns structured output
        
        Args:
            context: GeneralAgentContext with question and other info
            
        Returns:
            AgentOutput with finding, evidence, confidence
        """
        question = context.question
        logger.info(f"[GeneralAgent] Executing for question: {question}")
        
        try:
            if self.use_tools:
                return self._execute_with_tools(question, context)
            else:
                return self._execute_direct(question, context)
                
        except Exception as e:
            logger.error(f"[GeneralAgent] Execution failed: {e}")
            return AgentOutput(
                finding=f"General analysis failed: {str(e)}",
                evidence=["error"],
                confidence=0.0,
                agent=self.agent_name
            )
    
    def _execute_with_tools(
        self,
        question: str,
        context: GeneralAgentContext
    ) -> AgentOutput:
        """Execute using LangGraph agent with tools."""
        logger.info("[GeneralAgent] Executing with tools...")
        
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
        evidence = ["llm_analysis", "cross_domain_tools"]
        confidence = 0.80
        
        if "messages" in result:
            # Get the last AI message
            for msg in reversed(result["messages"]):
                if hasattr(msg, "content") and msg.content:
                    output_text = msg.content
                    break
        
        logger.info(f"[GeneralAgent] Tool execution complete: {output_text[:100]}...")
        
        return AgentOutput(
            finding=output_text,
            evidence=evidence,
            confidence=confidence,
            agent=self.agent_name
        )
    
    def _execute_direct(
        self,
        question: str,
        context: GeneralAgentContext
    ) -> AgentOutput:
        """Execute using direct LLM call (no tools)."""
        logger.info("[GeneralAgent] Executing direct LLM call...")
        
        # Load all available data
        all_data = self._load_all_data(days=7)
        
        # Analyze using LLM
        result = self.analyzer.analyze(
            question=question,
            data=all_data,
            analysis_type="general_business_health",
            additional_context=str(context.other_agent_outputs) if context.other_agent_outputs else None
        )
        
        # Extract structured response
        finding = result.get("finding", "Unable to complete general analysis.")
        evidence = result.get("evidence", ["llm_analysis"])
        confidence = result.get("confidence", 0.70)
        
        return AgentOutput(
            finding=finding,
            evidence=evidence,
            confidence=float(confidence),
            agent=self.agent_name
        )
    
    def _load_all_data(self, days: int = 7) -> Dict[str, Any]:
        """
        Load data from all available sources.
        
        Args:
            days: Number of days to load
            
        Returns:
            Dict containing all domain data
        """
        all_data = {}
        
        try:
            all_data["sales"] = self.data_loader.load_sales_data(days=days)
        except Exception as e:
            logger.warning(f"[GeneralAgent] Failed to load sales data: {e}")
            all_data["sales"] = {"error": str(e)}
        
        try:
            all_data["inventory"] = self.data_loader.load_inventory_data()
        except Exception as e:
            logger.warning(f"[GeneralAgent] Failed to load inventory data: {e}")
            all_data["inventory"] = {"error": str(e)}
        
        try:
            all_data["marketing"] = self.data_loader.load_marketing_data(days=days)
        except Exception as e:
            logger.warning(f"[GeneralAgent] Failed to load marketing data: {e}")
            all_data["marketing"] = {"error": str(e)}
        
        try:
            all_data["support"] = self.data_loader.load_support_data(days=days)
        except Exception as e:
            logger.warning(f"[GeneralAgent] Failed to load support data: {e}")
            all_data["support"] = {"error": str(e)}
        
        return all_data
    
    @observe(name="general_agent_call")
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph-compatible call method.
        
        Args:
            state: Graph state with question and other data
            
        Returns:
            Updated state with agent output
        """
        context = GeneralAgentContext(
            question=state.get("question", ""),
            intent=state.get("intent", "general"),
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
            "Analyzes overall business health across all domains including "
            "sales, inventory, marketing, and support. Uses LLM to synthesize "
            "insights and identify cross-domain patterns and correlations."
        )
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        tools = get_general_tools()
        return [tool.name for tool in tools]
