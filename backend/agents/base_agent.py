"""
Base Agent Abstract Class

Provides common functionality for all domain agents.
All agent methods are traced via Langfuse for observability.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langfuse import observe
from ..settings import Settings
from ..utils.data_loader import DataLoader
from ..utils.llm_formatter import LLMFormatter
from ..schemas.agent_output import AgentOutput
import logging

logger = logging.getLogger(__name__)


class AgentContext(BaseModel):
    """
    Context passed to agents from shared state.
    
    Allows agents to see what other agents have found.
    """
    question: str = Field(description="Original user question")
    intent: str = Field(description="Detected intent")
    other_agent_outputs: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Outputs from other agents (for data sharing)"
    )
    long_term_context: str = Field(
        default="",
        description="Long-term memory context (preferences, facts, knowledge)"
    )
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent conversation history"
    )


class AnalysisResult(BaseModel):
    """
    Structured result from agent analysis.
    
    All analysis logic should return this format.
    """
    metrics: Dict[str, Any] = Field(description="Calculated metrics")
    evidence: List[str] = Field(description="Evidence list")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    raw_data: Dict[str, Any] = Field(description="Raw data from source")


class BaseAgent(ABC):
    """
    Abstract base class for all domain agents.
    
    Enforces consistent interface and provides shared functionality.
    
    Child classes must implement:
    - load_data()
    - analyze()
    - get_fallback_template()
    """
    
    @staticmethod
    def _is_jupyter() -> bool:
        """Check if running in a Jupyter notebook."""
        try:
            from IPython import get_ipython
            if get_ipython() is not None:
                return True
        except ImportError:
            pass
        return False
    
    def __init__(
        self,
        agent_name: str,
        data_loader: Optional[DataLoader] = None,
        llm_formatter: Optional[LLMFormatter] = None,
        use_direct_loader: Optional[bool] = None
    ):
        """
        Initialize base agent.
        
        Args:
            agent_name: Name of the agent (sales, inventory, etc.)
            data_loader: Data loader instance (injected for testing)
            llm_formatter: LLM formatter instance (injected for testing)
            use_direct_loader: Force direct database access (auto-detected if None)
        """
        self.agent_name = agent_name
        
        # Auto-detect if we should use direct loader (Jupyter environment)
        if use_direct_loader is None:
            use_direct_loader = self._is_jupyter()
        
        # Initialize data loader with appropriate mode
        if data_loader:
            self.data_loader = data_loader
        else:
            self.data_loader = DataLoader(use_direct=use_direct_loader)
        
        self.llm_formatter = llm_formatter or LLMFormatter(agent_name)
        
        loader_type = "direct" if use_direct_loader else "MCP"
        logger.info(f"[{self.agent_name}Agent] Initialized (loader: {loader_type})")
    
    @abstractmethod
    def load_data(self, context: AgentContext) -> Dict[str, Any]:
        """
        Load data from MCP server.
        
        Args:
            context: Agent context with question and other agent outputs
        
        Returns:
            Raw data dictionary
        """
        pass
    
    @abstractmethod
    def analyze(self, data: Dict[str, Any], context: AgentContext) -> AnalysisResult:
        """
        Analyze loaded data and produce structured result.
        
        Args:
            data: Raw data from load_data()
            context: Agent context
        
        Returns:
            AnalysisResult with metrics, evidence, confidence
        """
        pass
    
    @abstractmethod
    def get_fallback_template(self) -> str:
        """
        Get fallback template for finding formatting.
        
        Used if LLM formatting fails.
        
        Returns:
            Template string with {variable} placeholders
        """
        pass
    
    def format_finding(
        self,
        analysis: AnalysisResult,
        context: AgentContext
    ) -> str:
        """
        Format analysis result into natural language finding.
        
        Args:
            analysis: Analysis result
            context: Agent context
        
        Returns:
            Natural language finding string
        """
        try:
            # Prepare context from other agents
            other_findings = {
                agent: output.get("finding", "")
                for agent, output in context.other_agent_outputs.items()
            }
            
            return self.llm_formatter.format_with_fallback(
                raw_metrics=analysis.raw_data,
                analysis_results=analysis.metrics,
                fallback_template=self.get_fallback_template(),
                context={"other_agents": other_findings}
            )
        except Exception as e:
            logger.error(f"[{self.agent_name}Agent] Formatting failed: {e}")
            # Use fallback template
            return self.get_fallback_template().format(**analysis.metrics)
    
    @observe(name="agent_execute")
    def execute(self, context: AgentContext) -> AgentOutput:
        """
        Execute the complete agent workflow.
        
        Orchestrates: load → analyze → format → output
        Traced via Langfuse @observe decorator.
        
        Args:
            context: Agent context
        
        Returns:
            AgentOutput with finding, evidence, confidence
        """
        try:
            logger.info(f"[{self.agent_name}Agent] Starting execution...")
            
            # Step 1: Load data
            data = self.load_data(context)
            
            # Step 2: Analyze
            analysis = self.analyze(data, context)
            
            # Step 3: Format finding
            finding = self.format_finding(analysis, context)
            
            # Step 4: Create output
            output = AgentOutput(
                finding=finding,
                evidence=analysis.evidence,
                confidence=analysis.confidence,
                agent=self.agent_name
            )
            
            logger.info(
                f"[{self.agent_name}Agent] Complete. "
                f"Confidence: {output.confidence:.2%}"
            )
            
            return output
        
        except Exception as e:
            logger.error(f"[{self.agent_name}Agent] Execution failed: {e}")
            # Return error output
            return AgentOutput(
                finding=f"{self.agent_name.capitalize()} analysis failed: {str(e)}",
                evidence=["error"],
                confidence=0.0,
                agent=self.agent_name
            )
    
    @observe(name="agent_call")
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make agent callable for LangGraph integration.
        Traced via Langfuse @observe decorator.
        
        Args:
            state: LangGraph state dictionary
        
        Returns:
            Updated state with agent output
        """
        # Extract context from state
        context = AgentContext(
            question=state.get("question", ""),
            intent=state.get("intent", ""),
            other_agent_outputs=state.get("agent_outputs", {}),
            long_term_context=state.get("long_term_context", ""),
            conversation_history=state.get("conversation_history", [])
        )
        
        # Execute agent
        output = self.execute(context)
        
        # Update state
        if "agent_outputs" not in state:
            state["agent_outputs"] = {}
        
        state["agent_outputs"][self.agent_name] = output.dict()
        
        return state
    
    @observe(name="agent_as_tool")
    def as_tool(self) -> StructuredTool:
        """
        Convert agent to LangChain StructuredTool.
        
        Allows agents to be used in LangChain tool calling.
        
        Returns:
            StructuredTool instance
        """
        def tool_func(question: str, context: Optional[Dict] = None) -> Dict:
            """Execute agent analysis."""
            agent_context = AgentContext(
                question=question,
                intent=context.get("intent", "") if context else "",
                other_agent_outputs=context.get("other_outputs", {}) if context else {}
            )
            output = self.execute(agent_context)
            return output.dict()
        
        return StructuredTool.from_function(
            func=tool_func,
            name=f"{self.agent_name}_agent",
            description=self.get_tool_description(),
        )
    
    @abstractmethod
    def get_tool_description(self) -> str:
        """
        Get description for LangChain tool.
        
        Returns:
            Tool description string
        """
        pass