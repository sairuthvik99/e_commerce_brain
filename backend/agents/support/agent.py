"""
Support Agent Implementation (LLM-Driven)

Uses LangChain tools for LLM-driven customer support analysis.
The LLM decides what's happening based on data and question.
Supports cross-domain access for queries involving sales correlation.
"""

from typing import Dict, Any, Optional, List
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from langfuse import observe
from pydantic import BaseModel, Field

from backend.settings import Settings
from backend.utils.agent_data_loader import AgentDataLoader
from backend.schemas.agent_output import AgentOutput
from .tools import get_support_tools, SupportLLMAnalyzer
from .logic import (
    calculate_ticket_spike,
    analyze_sentiment,
    analyze_top_categories,
    calculate_confidence,
    build_evidence
)

import logging
import json

logger = logging.getLogger(__name__)


class SupportAgentContext(BaseModel):
    """Context for support agent execution."""
    question: str = Field(description="User's question")
    intent: str = Field(default="support", description="Detected intent")
    other_agent_outputs: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Outputs from other agents"
    )


class SupportAgent:
    """
    LLM-Driven Support Agent.
    
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
        Initialize support agent.
        
        Args:
            use_tools: Whether to use LangChain tools (vs direct LLM)
            use_direct_loader: Force direct DB access (auto-detect if None)
            allow_cross_domain: Enable cross-domain data access for queries
                              that require sales data correlation
        """
        self.agent_name = "support"
        self.use_tools = use_tools
        self.allow_cross_domain = allow_cross_domain
        
        # Initialize LLM
        self.llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS.get("support", "gpt-4"),
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
        self.analyzer = SupportLLMAnalyzer()
        
        # Initialize tools and agent
        if use_tools:
            self._init_tool_agent()
        
        logger.info(
            f"[SupportAgent] Initialized (tools={use_tools}, "
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
        tools = get_support_tools()
        
        # Create system prompt with cross-domain awareness
        system_prompt = """You are a Customer Support Analysis Agent for an e-commerce business.
Your job is to analyze support ticket data and answer user questions about complaints, sentiment, categories, and customer service quality.

You have access to:
- Support data (tickets, complaints, sentiment, categories, refunds)
- Sales data (for cross-domain queries about review impact on conversions)

Use the available tools to get the right analysis for the user's question.
Select the most appropriate tool based on what the user is asking:
- For general support questions: use analyze_support_status
- For ticket volume: use analyze_ticket_volume
- For sentiment analysis: use analyze_customer_sentiment
- For issue categories: use analyze_issue_categories
- For trend analysis: use analyze_support_trend
- For refunds/returns: use analyze_refunds_returns
- For diagnosing spikes: use identify_support_spike_cause
- For correlation with sales: use analyze_support_sales_correlation
- For summaries: use get_support_summary

For questions about reviews affecting conversions or sales impact:
- Correlate negative reviews with sales/conversion data
- Consider timing of negative sentiment vs sales drops

After getting the tool result, provide a clear, concise answer to the user.
Always include specific numbers, percentages, and categories in your response."""
        
        # Create LangGraph agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=system_prompt,
        )
        
        logger.info("[SupportAgent] LangGraph agent initialized with tools")
    
    @observe(name="support_agent_execute")
    def execute(self, context: SupportAgentContext) -> AgentOutput:
        """
        Execute support analysis.
        
        This is the main entry point that:
        1. Takes the user's question
        2. Uses LLM (with or without tools) to analyze
        3. Returns structured output
        
        Args:
            context: SupportAgentContext with question and other info
            
        Returns:
            AgentOutput with finding, evidence, confidence
        """
        question = context.question
        logger.info(f"[SupportAgent] Executing for question: {question}")
        
        try:
            if self.use_tools:
                return self._execute_with_tools(question, context)
            else:
                return self._execute_direct(question, context)
                
        except Exception as e:
            logger.error(f"[SupportAgent] Execution failed: {e}")
            return self._create_error_output(str(e))
    
    def _execute_with_tools(
        self, 
        question: str, 
        context: SupportAgentContext
    ) -> AgentOutput:
        """Execute using LangGraph agent with tools."""
        logger.info("[SupportAgent] Executing with tools...")
        
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
        context: SupportAgentContext
    ) -> AgentOutput:
        """Execute using direct LLM call without tools."""
        logger.info("[SupportAgent] Executing direct (no tools)...")
        
        # Load data
        support_data = self.data_loader.load_support_data(days=7)
        
        # Use analyzer for LLM-driven analysis
        result = self.analyzer.analyze(
            question=question,
            data=support_data,
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
            finding=f"Support analysis failed: {error}",
            evidence=["error"],
            confidence=0.0
        )
    
    # ==================== Legacy Methods for Backward Compatibility ====================
    
    def load_data(self, context: Optional[SupportAgentContext] = None) -> Dict[str, Any]:
        """
        Load support data (legacy method for backward compatibility).
        
        Returns:
            Dict with ticket volume, sentiment, categories
        """
        logger.info("[SupportAgent] Loading data (legacy method)...")
        
        try:
            support_data = self.data_loader.load_support_data(days=7)
            
            logger.info(
                f"[SupportAgent] Loaded: "
                f"{support_data.get('yesterday_tickets', 0)} tickets vs "
                f"{support_data.get('avg_tickets', 0):.1f} avg"
            )
            
            return support_data
        
        except Exception as e:
            logger.error(f"[SupportAgent] Data loading failed: {e}")
            raise
    
    def analyze_legacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze support data using legacy logic (for backward compatibility).
        
        Uses rule-based analysis instead of LLM.
        """
        logger.info("[SupportAgent] Analyzing data (legacy)...")
        
        # Calculate metrics using legacy logic
        ticket_spike = calculate_ticket_spike(data)
        sentiment_metrics = analyze_sentiment(data)
        top_category, top_count, top_pct = analyze_top_categories(data)
        
        confidence = calculate_confidence(
            spike_pct=ticket_spike,
            negative_pct=sentiment_metrics['negative_pct'],
            top_category_pct=top_pct
        )
        
        metrics = {
            'ticket_spike_pct': ticket_spike,
            'yesterday_tickets': data.get('yesterday_tickets', 0),
            'avg_tickets': data.get('avg_tickets', 0),
            'negative_pct': sentiment_metrics['negative_pct'],
            'negative_count': sentiment_metrics['negative_count'],
            'top_category': top_category,
            'top_category_count': top_count,
            'top_category_pct': top_pct
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
            "Support tickets increased {ticket_spike_pct:.0f}% yesterday "
            "({yesterday_tickets} vs {avg_tickets:.1f} avg)"
        )
    
    def get_tool_description(self) -> str:
        """LangChain tool description."""
        return (
            "Analyzes support ticket volume, sentiment distribution, and "
            "complaint categories. Identifies spikes and issues."
        )
    
    @observe(name="support_agent_call")
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph-compatible call method.
        
        Args:
            state: Graph state with question and other data
            
        Returns:
            Updated state with agent output
        """
        context = SupportAgentContext(
            question=state.get("question", ""),
            intent=state.get("intent", "support"),
            other_agent_outputs=state.get("agent_outputs", {})
        )
        
        output = self.execute(context)
        
        # Update state
        if "agent_outputs" not in state:
            state["agent_outputs"] = {}
        state["agent_outputs"][self.agent_name] = output.model_dump()
        
        return state