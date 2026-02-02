"""
Marketing Agent Implementation (LLM-Driven)

Uses LangChain tools for LLM-driven marketing and campaign analysis.
The LLM decides what's happening based on data and question.
"""

from typing import Dict, Any, Optional, List
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from langfuse import observe
from pydantic import BaseModel, Field

from backend.settings import Settings
from backend.utils.data_loader import DataLoader
from backend.schemas.agent_output import AgentOutput
from .tools import get_marketing_tools, MarketingLLMAnalyzer
from .logic import (
    calculate_conversion_drop,
    calculate_spend_change,
    calculate_efficiency,
    analyze_campaign_status,
    calculate_confidence,
    build_evidence
)

import logging
import json

logger = logging.getLogger(__name__)


class MarketingAgentContext(BaseModel):
    """Context for marketing agent execution."""
    question: str = Field(description="User's question")
    intent: str = Field(default="marketing", description="Detected intent")
    other_agent_outputs: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Outputs from other agents"
    )


class MarketingAgent:
    """
    LLM-Driven Marketing Agent.
    
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
        use_direct_loader: Optional[bool] = None
    ):
        """
        Initialize marketing agent.
        
        Args:
            use_tools: Whether to use LangChain tools (vs direct LLM)
            use_direct_loader: Force direct DB access (auto-detect if None)
        """
        self.agent_name = "marketing"
        self.use_tools = use_tools
        
        # Initialize LLM
        self.llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS.get("marketing", "gpt-4"),
            temperature=0.2,
        )
        
        # Initialize data loader
        if use_direct_loader is None:
            use_direct_loader = self._is_jupyter()
        self.data_loader = DataLoader(use_direct=use_direct_loader)
        
        # Initialize LLM analyzer for direct mode
        self.analyzer = MarketingLLMAnalyzer()
        
        # Initialize tools and agent
        if use_tools:
            self._init_tool_agent()
        
        logger.info(f"[MarketingAgent] Initialized (tools={use_tools})")
    
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
        tools = get_marketing_tools()
        
        # Create system prompt
        system_prompt = """You are a Marketing Analysis Agent for an e-commerce business.
Your job is to analyze marketing campaign data and answer user questions about conversions, ad spend, ROI, and campaign performance.

Use the available tools to get the right analysis for the user's question.
Select the most appropriate tool based on what the user is asking:
- For general marketing questions: use analyze_marketing_performance
- For conversion analysis: use analyze_campaign_conversions
- For spend analysis: use analyze_ad_spend
- For ROI/efficiency: use analyze_marketing_roi
- For campaign status: use analyze_campaign_status
- For period comparisons: use compare_campaign_periods
- For diagnosing drops: use identify_conversion_drop_cause
- For correlation with sales: use analyze_marketing_sales_correlation
- For summaries: use get_marketing_summary

After getting the tool result, provide a clear, concise answer to the user.
Always include specific numbers, percentages, and currency values in your response."""
        
        # Create LangGraph agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=system_prompt,
        )
        
        logger.info("[MarketingAgent] LangGraph agent initialized with tools")
    
    @observe(name="marketing_agent_execute")
    def execute(self, context: MarketingAgentContext) -> AgentOutput:
        """
        Execute marketing analysis.
        
        This is the main entry point that:
        1. Takes the user's question
        2. Uses LLM (with or without tools) to analyze
        3. Returns structured output
        
        Args:
            context: MarketingAgentContext with question and other info
            
        Returns:
            AgentOutput with finding, evidence, confidence
        """
        question = context.question
        logger.info(f"[MarketingAgent] Executing for question: {question}")
        
        try:
            if self.use_tools:
                return self._execute_with_tools(question, context)
            else:
                return self._execute_direct(question, context)
                
        except Exception as e:
            logger.error(f"[MarketingAgent] Execution failed: {e}")
            return self._create_error_output(str(e))
    
    def _execute_with_tools(
        self, 
        question: str, 
        context: MarketingAgentContext
    ) -> AgentOutput:
        """Execute using LangGraph agent with tools."""
        logger.info("[MarketingAgent] Executing with tools...")
        
        # Prepare input message
        messages = [{"role": "user", "content": question}]
        
        # Run the agent
        result = self.agent.invoke({"messages": messages})
        
        # Extract final response
        final_message = result["messages"][-1]
        response_text = final_message.content
        
        # Try to extract structured data from tool results
        finding = response_text
        evidence = ["tool_based_analysis"]
        confidence = 0.85
        
        # Look for tool results in message history
        for msg in result["messages"]:
            if hasattr(msg, 'additional_kwargs') and 'tool_calls' in msg.additional_kwargs:
                evidence.append("llm_tool_used")
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                try:
                    if '"finding"' in msg.content:
                        parsed = json.loads(msg.content)
                        if 'confidence' in parsed:
                            confidence = parsed['confidence']
                        if 'evidence' in parsed:
                            evidence.extend(parsed['evidence'])
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return AgentOutput(
            agent=self.agent_name,
            finding=finding,
            evidence=list(set(evidence)),
            confidence=confidence
        )
    
    def _execute_direct(
        self, 
        question: str, 
        context: MarketingAgentContext
    ) -> AgentOutput:
        """Execute using direct LLM call without tools."""
        logger.info("[MarketingAgent] Executing direct (no tools)...")
        
        # Load data
        marketing_data = self.data_loader.load_marketing_data(days=7)
        
        # Use analyzer for LLM-driven analysis
        result = self.analyzer.analyze(
            question=question,
            data=marketing_data,
            analysis_type="direct_query",
            additional_context="Answer the user's question directly based on the data."
        )
        
        return AgentOutput(
            agent=self.agent_name,
            finding=result.get("finding", "Analysis completed"),
            evidence=result.get("evidence", ["direct_analysis"]),
            confidence=result.get("confidence", 0.75)
        )
    
    def _create_error_output(self, error: str) -> AgentOutput:
        """Create error output for failed execution."""
        return AgentOutput(
            agent=self.agent_name,
            finding=f"Marketing analysis failed: {error}",
            evidence=["error"],
            confidence=0.0
        )
    
    # ==================== Legacy Methods for Backward Compatibility ====================
    
    def load_data(self, context: Optional[MarketingAgentContext] = None) -> Dict[str, Any]:
        """
        Load marketing data (legacy method for backward compatibility).
        
        Returns:
            Dict with campaign performance metrics
        """
        logger.info("[MarketingAgent] Loading data (legacy method)...")
        
        try:
            marketing_data = self.data_loader.load_marketing_data(days=7)
            
            logger.info(
                f"[MarketingAgent] Loaded: "
                f"{marketing_data.get('yesterday_conversions', 0)} conversions vs "
                f"{marketing_data.get('avg_conversions', 0):.1f} avg"
            )
            
            return marketing_data
        
        except Exception as e:
            logger.error(f"[MarketingAgent] Data loading failed: {e}")
            raise
    
    def analyze_legacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze marketing data using legacy logic (for backward compatibility).
        
        Uses rule-based analysis instead of LLM.
        """
        logger.info("[MarketingAgent] Analyzing data (legacy)...")
        
        # Calculate metrics using legacy logic
        conversion_drop = calculate_conversion_drop(data)
        spend_change = calculate_spend_change(data)
        efficiency_metrics = calculate_efficiency(data)
        campaign_status = analyze_campaign_status(data)
        
        confidence = calculate_confidence(
            conversion_drop=conversion_drop,
            spend_change=spend_change,
            efficiency_drop=efficiency_metrics['efficiency_drop_pct']
        )
        
        metrics = {
            'conversion_drop_pct': conversion_drop,
            'spend_change_pct': spend_change,
            'efficiency_drop_pct': efficiency_metrics['efficiency_drop_pct'],
            'yesterday_conversions': data.get('yesterday_conversions', 0),
            'avg_conversions': data.get('avg_conversions', 0),
            'yesterday_spend': data.get('yesterday_spend', 0),
            'avg_spend': data.get('avg_spend', 0),
            'active_campaigns': campaign_status['active_campaigns'],
            'has_paused_campaigns': campaign_status['has_paused_campaigns']
        }
        
        evidence = build_evidence(data, metrics)
        
        return {
            "metrics": metrics,
            "evidence": evidence,
            "confidence": confidence,
            "raw_data": data
        }
    
    def get_fallback_template(self) -> str:
        """Fallback template if LLM formatting fails."""
        return (
            "Campaign conversions dropped {conversion_drop_pct:.1f}% yesterday "
            "with {active_campaigns} active campaigns"
        )
    
    def get_tool_description(self) -> str:
        """LangChain tool description."""
        return (
            "Analyzes marketing campaign performance including conversions, "
            "spend, and efficiency. Identifies underperforming campaigns."
        )
    
    @observe(name="marketing_agent_call")
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph-compatible call method.
        
        Args:
            state: Graph state with question and other data
            
        Returns:
            Updated state with agent output
        """
        context = MarketingAgentContext(
            question=state.get("question", ""),
            intent=state.get("intent", "marketing"),
            other_agent_outputs=state.get("agent_outputs", {})
        )
        
        output = self.execute(context)
        
        # Update state
        if "agent_outputs" not in state:
            state["agent_outputs"] = {}
        state["agent_outputs"][self.agent_name] = output.model_dump()
        
        return state