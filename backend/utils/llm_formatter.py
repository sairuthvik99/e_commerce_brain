"""
LLM Finding Formatter

Uses LLM to format raw analysis results into natural language findings.
Integrates Langfuse for observability and tracing.
"""

from langchain_openai import AzureChatOpenAI
from langfuse import observe, Langfuse
from backend.settings import Settings
from backend.utils.prompt_loader import load_prompt
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

# ==================== LANGFUSE INITIALIZATION ====================
# Initialize Langfuse client with configuration from settings
# This bypasses OpenAI key requirement by using Azure OpenAI via company's LLM API

langfuse = Langfuse(
    secret_key=Settings.LANGFUSE_SECRET_KEY,
    public_key=Settings.LANGFUSE_PUBLIC_KEY,
    host=Settings.LANGFUSE_BASE_URL
)


class LLMFormatter:
    """
    Formats analysis results into natural language using LLM.
    All methods are traced via Langfuse for observability.
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize formatter for a specific agent.
        
        Args:
            agent_name: Name of the agent (sales, inventory, marketing, support)
        """
        self.agent_name = agent_name
        try:
            self.llm = AzureChatOpenAI(
                api_key=Settings.DIAL_API_KEY,
                azure_endpoint=Settings.AZURE_ENDPOINT,
                api_version=Settings.API_VERSION,
                model=Settings.AGENT_MODELS.get(agent_name, Settings.AGENT_MODELS["supervisor"]),
                temperature=0.3,  # Low temperature for consistent formatting
            )
            logger.info(f"[LLMFormatter:{agent_name}] Initialized with Langfuse tracing")
        except Exception as e:
            logger.error(f"[LLMFormatter:{agent_name}] Failed to initialize: {e}")
            raise
    
    @observe(name="format_finding")
    def format_finding(
        self, 
        raw_metrics: Dict[str, Any], 
        analysis_results: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> str:
        """
        Format analysis results into natural language finding.
        Traced via Langfuse @observe decorator.
        
        Args:
            raw_metrics: Raw data from database
            analysis_results: Calculated metrics (drops, trends, etc.)
            context: Optional context from other agents (for data sharing)
        
        Returns:
            Natural language finding string (1-2 sentences)
        """
        try:
            logger.info(f"[LLMFormatter:{self.agent_name}] Formatting finding...")
            
            # Load prompts
            system_prompt = load_prompt(
                agent=self.agent_name,
                task="finding_format",
                prompt_type="system"
            )
            
            # Prepare variables
            variables = {
                "raw_metrics": json.dumps(raw_metrics, indent=2, default=str),
                "analysis": json.dumps(analysis_results, indent=2, default=str)
            }
            
            # Add context if available
            if context:
                variables["context"] = json.dumps(context, indent=2, default=str)
            else:
                variables["context"] = "No context from other agents."
            
            user_prompt = load_prompt(
                agent=self.agent_name,
                task="finding_format",
                prompt_type="user",
                variables=variables
            )
            
            # Call LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.llm.invoke(messages)
            finding = response.content.strip()
            
            logger.info(f"[LLMFormatter:{self.agent_name}] Finding formatted: {finding[:100]}...")
            return finding
        
        except Exception as e:
            logger.error(f"[LLMFormatter:{self.agent_name}] Formatting failed: {e}")
            # Fallback to simple string format
            return f"{self.agent_name.capitalize()} agent detected issues based on analysis."
    
    @observe(name="format_with_fallback")
    def format_with_fallback(
        self,
        raw_metrics: Dict[str, Any],
        analysis_results: Dict[str, Any],
        fallback_template: str,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Format finding with fallback template if LLM fails.
        Traced via Langfuse @observe decorator.
        
        Args:
            raw_metrics: Raw data from database
            analysis_results: Calculated metrics
            fallback_template: Template string for fallback (uses .format())
            context: Optional context from other agents
        
        Returns:
            Formatted finding string
        """
        try:
            return self.format_finding(raw_metrics, analysis_results, context)
        except Exception as e:
            logger.warning(f"[LLMFormatter:{self.agent_name}] Using fallback template: {e}")
            return fallback_template.format(**analysis_results)
    
    @observe(name="format_synthesis")
    def format_synthesis(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Format synthesis output using LLM.
        Traced via Langfuse @observe decorator.
        
        Args:
            prompt: Synthesis prompt template
            context: Context with agent findings
        
        Returns:
            Synthesized output string
        """
        try:
            messages = [
                {"role": "system", "content": "You are a synthesis agent that combines findings from multiple domain agents."},
                {"role": "user", "content": f"{prompt}\n\nContext:\n{json.dumps(context, indent=2, default=str)}"}
            ]
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.error(f"[LLMFormatter:{self.agent_name}] Synthesis formatting failed: {e}")
            raise
    
    @observe(name="format_reflection")
    def format_reflection(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Format reflection output using LLM.
        Traced via Langfuse @observe decorator.
        
        Args:
            prompt: Reflection prompt template
            context: Context with agent outputs and synthesis
        
        Returns:
            Reflection output string
        """
        try:
            messages = [
                {"role": "system", "content": "You are a reflection agent that audits reasoning quality."},
                {"role": "user", "content": f"{prompt}\n\nContext:\n{json.dumps(context, indent=2, default=str)}"}
            ]
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.error(f"[LLMFormatter:{self.agent_name}] Reflection formatting failed: {e}")
            raise


# Convenience function
@observe(name="format_finding_convenience")
def format_finding(
    agent_name: str,
    raw_metrics: Dict[str, Any],
    analysis_results: Dict[str, Any],
    context: Dict[str, Any] = None
) -> str:
    """
    Format finding for an agent (convenience function).
    Traced via Langfuse @observe decorator.
    
    Usage:
        finding = format_finding(
            agent_name="sales",
            raw_metrics={"revenue": 10000, ...},
            analysis_results={"drop_pct": 25.5, ...}
        )
    """
    formatter = LLMFormatter(agent_name)
    return formatter.format_finding(raw_metrics, analysis_results, context)