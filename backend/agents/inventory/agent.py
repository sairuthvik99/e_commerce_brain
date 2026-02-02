"""
Inventory Agent Implementation (LLM-Driven)

Uses LangChain tools for LLM-driven inventory analysis.
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
from .tools import get_inventory_tools, InventoryLLMAnalyzer
from .logic import (
    calculate_stockout_severity,
    identify_critical_products,
    calculate_confidence,
    build_evidence
)

import logging
import json

logger = logging.getLogger(__name__)


class InventoryAgentContext(BaseModel):
    """Context for inventory agent execution."""
    question: str = Field(description="User's question")
    intent: str = Field(default="inventory", description="Detected intent")
    other_agent_outputs: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Outputs from other agents"
    )


class InventoryAgent:
    """
    LLM-Driven Inventory Agent.
    
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
        Initialize inventory agent.
        
        Args:
            use_tools: Whether to use LangChain tools (vs direct LLM)
            use_direct_loader: Force direct DB access (auto-detect if None)
            allow_cross_domain: Enable cross-domain data access for queries
                              that require sales data correlation
        """
        self.agent_name = "inventory"
        self.use_tools = use_tools
        self.allow_cross_domain = allow_cross_domain
        
        # Initialize LLM
        self.llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS.get("inventory", "gpt-4"),
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
        self.analyzer = InventoryLLMAnalyzer()
        
        # Initialize tools and agent
        if use_tools:
            self._init_tool_agent()
        
        logger.info(
            f"[InventoryAgent] Initialized (tools={use_tools}, "
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
        tools = get_inventory_tools()
        
        # Create system prompt with cross-domain awareness
        system_prompt = """You are an Inventory Analysis Agent for an e-commerce business.
Your job is to analyze inventory data and answer user questions about stockouts, inventory levels, and product availability.

You have access to:
- Inventory data (stock levels, stockouts, snapshots)
- Sales data (for cross-domain queries about viewed/purchased items, conversions)

Use the available tools to get the right analysis for the user's question.
Select the most appropriate tool based on what the user is asking:
- For general inventory questions: use analyze_inventory_status
- For stockout details: use analyze_stockout_events
- For trend analysis: use analyze_stockout_trend
- For critical products: use identify_critical_stockouts
- For sales impact: use analyze_inventory_impact
- For restock recommendations: use prioritize_restock
- For severity comparison: use compare_stockout_severity
- For summaries: use get_inventory_summary

For questions about "viewed but not purchased" or conversion impact:
- Correlate inventory stockouts with sales/order data
- Consider products that were viewed but unavailable

After getting the tool result, provide a clear, concise answer to the user.
Always include specific numbers and severity multipliers in your response."""
        
        # Create LangGraph agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=system_prompt,
        )
        
        logger.info("[InventoryAgent] LangGraph agent initialized with tools")
    
    @observe(name="inventory_agent_execute")
    def execute(self, context: InventoryAgentContext) -> AgentOutput:
        """
        Execute inventory analysis.
        
        This is the main entry point that:
        1. Takes the user's question
        2. Uses LLM (with or without tools) to analyze
        3. Returns structured output
        
        Args:
            context: InventoryAgentContext with question and other info
            
        Returns:
            AgentOutput with finding, evidence, confidence
        """
        question = context.question
        logger.info(f"[InventoryAgent] Executing for question: {question}")
        
        try:
            if self.use_tools:
                return self._execute_with_tools(question, context)
            else:
                return self._execute_direct(question, context)
                
        except Exception as e:
            logger.error(f"[InventoryAgent] Execution failed: {e}")
            return self._create_error_output(str(e))
    
    def _execute_with_tools(
        self, 
        question: str, 
        context: InventoryAgentContext
    ) -> AgentOutput:
        """Execute using LangGraph agent with tools."""
        logger.info("[InventoryAgent] Executing with tools...")
        
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
        context: InventoryAgentContext
    ) -> AgentOutput:
        """Execute using direct LLM call without tools."""
        logger.info("[InventoryAgent] Executing direct (no tools)...")
        
        # Load data
        inventory_data = self.data_loader.load_inventory_data()
        baseline = self.data_loader.load_inventory_baseline(days=7)
        
        combined_data = {
            **inventory_data,
            "baseline": baseline
        }
        
        # Use analyzer for LLM-driven analysis
        result = self.analyzer.analyze(
            question=question,
            data=combined_data,
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
            finding=f"Inventory analysis failed: {error}",
            evidence=["error"],
            confidence=0.0
        )
    
    # ==================== Legacy Methods for Backward Compatibility ====================
    
    def load_data(self, context: Optional[InventoryAgentContext] = None) -> Dict[str, Any]:
        """
        Load inventory data (legacy method for backward compatibility).
        
        Returns:
            Dict with stockout events and baseline
        """
        logger.info("[InventoryAgent] Loading data (legacy method)...")
        
        try:
            stockouts = self.data_loader.load_inventory_data()
            baseline = self.data_loader.load_inventory_baseline(days=7)
            
            data = {
                **stockouts,
                'baseline': baseline
            }
            
            logger.info(
                f"[InventoryAgent] Loaded: "
                f"{stockouts.get('total_stockouts', 0)} stockouts vs "
                f"{baseline.get('avg_daily_stockouts', 0):.1f} avg"
            )
            
            return data
        
        except Exception as e:
            logger.error(f"[InventoryAgent] Data loading failed: {e}")
            raise
    
    def analyze_legacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze inventory data using legacy logic (for backward compatibility).
        
        Uses rule-based analysis instead of LLM.
        """
        logger.info("[InventoryAgent] Analyzing data (legacy)...")
        
        baseline = data.get('baseline', {})
        
        severity = calculate_stockout_severity(data, baseline)
        critical_products = identify_critical_products(data)
        total_stockouts = data.get('total_stockouts', 0)
        
        confidence = calculate_confidence(
            severity=severity,
            critical_count=len(critical_products),
            total_stockouts=total_stockouts
        )
        
        metrics = {
            'total_stockouts': total_stockouts,
            'avg_stockouts': baseline.get('avg_daily_stockouts', 0),
            'severity': severity,
            'critical_products': critical_products,
            'critical_count': len(critical_products)
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
            "{total_stockouts} products out of stock "
            "({severity:.1f}x higher than baseline)"
        )
    
    def get_tool_description(self) -> str:
        """LangChain tool description."""
        return (
            "Analyzes inventory stockout events and identifies critical "
            "products affected. Compares to baseline to assess severity."
        )
    
    @observe(name="inventory_agent_call")
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph-compatible call method.
        
        Args:
            state: Graph state with question and other data
            
        Returns:
            Updated state with agent output
        """
        context = InventoryAgentContext(
            question=state.get("question", ""),
            intent=state.get("intent", "inventory"),
            other_agent_outputs=state.get("agent_outputs", {})
        )
        
        output = self.execute(context)
        
        # Update state
        if "agent_outputs" not in state:
            state["agent_outputs"] = {}
        state["agent_outputs"][self.agent_name] = output.model_dump()
        
        return state