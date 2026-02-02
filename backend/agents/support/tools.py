"""
Support Agent LangChain Tools

LLM-driven tools for customer support ticket analysis.
Each tool is designed for specific question types and lets the LLM
decide what's happening based on the data.
"""

from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from backend.settings import Settings
from backend.utils.agent_data_loader import create_agent_loader, AgentDataLoader
from backend.utils.prompt_loader import load_prompt
from langfuse import observe
import json
import logging

logger = logging.getLogger(__name__)


# ==================== Pydantic Input Schemas ====================

class SupportAnalysisInput(BaseModel):
    """Input schema for support analysis tool."""
    question: str = Field(description="The user's question about support")
    days: int = Field(default=7, description="Number of days for baseline comparison")


class TicketVolumeInput(BaseModel):
    """Input schema for ticket volume analysis."""
    question: str = Field(description="The user's question about ticket volume")
    days: int = Field(default=7, description="Number of days to analyze")


class SentimentAnalysisInput(BaseModel):
    """Input schema for sentiment analysis."""
    question: str = Field(description="The user's question about customer sentiment")
    days: int = Field(default=7, description="Number of days to analyze")


class CategoryAnalysisInput(BaseModel):
    """Input schema for category analysis."""
    question: str = Field(description="The user's question about issue categories")
    top_n: int = Field(default=5, description="Number of top categories to analyze")


class SupportTrendInput(BaseModel):
    """Input schema for support trend analysis."""
    question: str = Field(description="The user's question about support trends")
    days: int = Field(default=7, description="Number of days to analyze for trends")


class RefundReturnsInput(BaseModel):
    """Input schema for refund and returns analysis."""
    question: str = Field(description="The user's question about refunds or returns")
    days: int = Field(default=7, description="Number of days to analyze")


class SupportImpactInput(BaseModel):
    """Input schema for support impact analysis."""
    question: str = Field(description="The user's question about support impact on business")
    days: int = Field(default=7, description="Number of days to analyze")


# ==================== LLM Analysis Helper ====================

class SupportLLMAnalyzer:
    """
    Helper class to analyze support data using LLM.
    Sends data and question to LLM and returns structured response.
    
    Table Access: daily_metrics, support_tickets
    """
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS.get("support", "gpt-4"),
            temperature=0.2,
        )
        # Use agent-specific data loader with restricted table access
        # Support agent can only access: daily_metrics, support_tickets
        self.data_loader = create_agent_loader("support")
        logger.info(f"[SupportLLMAnalyzer] Initialized with table access: {self.data_loader.allowed_tables}")
    
    @observe(name="support_llm_analyze")
    def analyze(
        self, 
        question: str, 
        data: Dict[str, Any], 
        analysis_type: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send data and question to LLM for analysis.
        
        Args:
            question: User's question
            data: Support data from database
            analysis_type: Type of analysis (tickets, sentiment, categories, etc.)
            additional_context: Extra context for the LLM
            
        Returns:
            Dict with finding, evidence, confidence, and raw LLM response
        """
        try:
            # Load the analysis prompt
            system_prompt = load_prompt(
                agent="support",
                task="analysis",
                prompt_type="system"
            )
            
            user_prompt = load_prompt(
                agent="support",
                task="analysis",
                prompt_type="user",
                variables={
                    "question": question,
                    "data": json.dumps(data, indent=2, default=str),
                    "analysis_type": analysis_type,
                    "additional_context": additional_context or "None"
                }
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            logger.info(f"[SupportLLMAnalyzer] Calling LLM for {analysis_type} analysis...")
            response = self.llm.invoke(messages)
            
            # Parse the response - LLM should return JSON
            content = response.content.strip()
            
            # Try to parse as JSON, otherwise wrap the text response
            try:
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()
                
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, wrap the response
                result = {
                    "finding": content,
                    "evidence": ["llm_analysis"],
                    "confidence": 0.75,
                    "analysis_details": content
                }
            
            logger.info(f"[SupportLLMAnalyzer] Analysis complete: {result.get('finding', '')[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"[SupportLLMAnalyzer] Analysis failed: {e}")
            return {
                "finding": f"Analysis failed: {str(e)}",
                "evidence": ["error"],
                "confidence": 0.0,
                "error": str(e)
            }


# Global analyzer instance (lazy initialization)
_analyzer: Optional[SupportLLMAnalyzer] = None


def get_analyzer() -> SupportLLMAnalyzer:
    """Get or create the global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SupportLLMAnalyzer()
    return _analyzer


# ==================== LangChain Tools ====================

@tool("analyze_support_status", args_schema=SupportAnalysisInput)
def analyze_support_status(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze overall customer support status and health.
    
    Use this tool when the user asks:
    - "How is customer support doing?"
    - "What's the support situation?"
    - "Support status overview"
    - "Are there any support issues?"
    
    Returns comprehensive support analysis including ticket volume, sentiment, and categories.
    """
    logger.info(f"[Tool:analyze_support_status] Question: {question}")
    
    analyzer = get_analyzer()
    
    # Load support data
    support_data = analyzer.data_loader.load_support_data(days=days)
    
    combined_data = {
        **support_data,
        "analysis_period_days": days
    }
    
    # Let LLM analyze the data
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="general_support_status",
        additional_context=f"Analyzing {days}-day support data to answer the user's question."
    )
    
    # Add raw data to result
    result["raw_data"] = combined_data
    result["tool"] = "analyze_support_status"
    
    return result


@tool("analyze_ticket_volume", args_schema=TicketVolumeInput)
def analyze_ticket_volume(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze support ticket volume and spikes.
    
    Use this tool when the user asks:
    - "Did customer complaints increase?"
    - "How many tickets did we get?"
    - "Is ticket volume higher than usual?"
    - "Support ticket trends"
    
    Returns ticket volume analysis with spike detection.
    """
    logger.info(f"[Tool:analyze_ticket_volume] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    support_data = analyzer.data_loader.load_support_data(days=days)
    
    combined_data = {
        **support_data,
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="ticket_volume_analysis",
        additional_context="Focus on ticket volume changes, spikes, and comparison to baseline."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_ticket_volume"
    
    return result


@tool("analyze_customer_sentiment", args_schema=SentimentAnalysisInput)
def analyze_customer_sentiment(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze customer sentiment from support tickets.
    
    Use this tool when the user asks:
    - "What's the customer sentiment?"
    - "Are customers unhappy?"
    - "Sentiment analysis of tickets"
    - "How negative are the complaints?"
    
    Returns sentiment analysis with positive/negative distribution.
    """
    logger.info(f"[Tool:analyze_customer_sentiment] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    support_data = analyzer.data_loader.load_support_data(days=days)
    
    combined_data = {
        **support_data,
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="sentiment_analysis",
        additional_context="Analyze customer sentiment distribution. Focus on negative sentiment percentage and trends."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_customer_sentiment"
    
    return result


@tool("analyze_issue_categories", args_schema=CategoryAnalysisInput)
def analyze_issue_categories(question: str, top_n: int = 5) -> Dict[str, Any]:
    """
    Analyze top issue categories from support tickets.
    
    Use this tool when the user asks:
    - "What are customers complaining about?"
    - "Top complaint categories"
    - "What issues are most common?"
    - "What's driving support tickets?"
    
    Returns category breakdown with top issues identified.
    """
    logger.info(f"[Tool:analyze_issue_categories] Question: {question}, top_n: {top_n}")
    
    analyzer = get_analyzer()
    
    support_data = analyzer.data_loader.load_support_data(days=7)
    
    combined_data = {
        **support_data,
        "top_n_categories": top_n
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="category_analysis",
        additional_context=f"Identify top {top_n} issue categories. Focus on what customers are complaining about most."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_issue_categories"
    
    return result


@tool("analyze_support_trend", args_schema=SupportTrendInput)
def analyze_support_trend(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze support ticket trends over time.
    
    Use this tool when the user asks:
    - "Is the support situation improving or worsening?"
    - "What's the trend in customer complaints?"
    - "Are we getting more or fewer tickets?"
    - "Support ticket pattern analysis"
    
    Returns trend analysis with direction and pattern insights.
    """
    logger.info(f"[Tool:analyze_support_trend] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    support_data = analyzer.data_loader.load_support_data(days=days)
    
    combined_data = {
        **support_data,
        "trend_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="support_trend",
        additional_context=f"Analyze {days}-day support trend. Identify pattern direction and predict near-term outlook."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_support_trend"
    
    return result


@tool("analyze_refunds_returns", args_schema=RefundReturnsInput)
def analyze_refunds_returns(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze refund and return patterns.
    
    Use this tool when the user asks:
    - "Are refunds higher than usual?"
    - "Return rate analysis"
    - "Refund trends"
    - "Why are customers returning products?"
    
    Returns refund and return analysis.
    """
    logger.info(f"[Tool:analyze_refunds_returns] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    support_data = analyzer.data_loader.load_support_data(days=days)
    
    combined_data = {
        **support_data,
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="refunds_returns_analysis",
        additional_context="Analyze refund and return patterns. Look for trends and common reasons."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_refunds_returns"
    
    return result


@tool("identify_support_spike_cause", args_schema=SupportAnalysisInput)
def identify_support_spike_cause(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Identify the root cause of support ticket spikes.
    
    Use this tool when the user asks:
    - "Why did complaints increase?"
    - "What caused the support spike?"
    - "Root cause of ticket surge"
    - "Diagnose support issues"
    
    Returns root cause analysis for support spikes.
    """
    logger.info(f"[Tool:identify_support_spike_cause] Question: {question}")
    
    analyzer = get_analyzer()
    
    # Load support data
    support_data = analyzer.data_loader.load_support_data(days=days)
    
    # Also load inventory data to check for stockout correlation
    inventory_data = analyzer.data_loader.load_inventory_data()
    inventory_baseline = analyzer.data_loader.load_inventory_baseline(days=days)
    
    combined_data = {
        "support": support_data,
        "inventory": {
            **inventory_data,
            "baseline": inventory_baseline
        },
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="spike_cause_analysis",
        additional_context="Identify why support tickets spiked. Consider category distribution, sentiment, and correlation with inventory issues."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "identify_support_spike_cause"
    
    return result


@tool("get_support_summary", args_schema=SupportAnalysisInput)
def get_support_summary(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Get a comprehensive support summary for reporting.
    
    Use this tool when the user asks:
    - "Summarize support performance"
    - "Give me a support overview"
    - "Executive summary of customer service"
    - "What's the support status?"
    
    Returns a formatted summary suitable for reports.
    """
    logger.info(f"[Tool:get_support_summary] Question: {question}")
    
    analyzer = get_analyzer()
    
    support_data = analyzer.data_loader.load_support_data(days=days)
    
    combined_data = {
        **support_data,
        "summary_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="summary",
        additional_context="Create clear, executive-level support summary. Include key metrics, trends, and notable issues."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "get_support_summary"
    
    return result


@tool("analyze_support_sales_correlation", args_schema=SupportImpactInput)
def analyze_support_sales_correlation(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze correlation between support issues and sales impact.
    
    Use this tool when the user asks:
    - "Are support issues affecting sales?"
    - "Correlation between complaints and revenue"
    - "Support impact on business"
    - "Are customer issues causing sales drops?"
    
    Returns correlation analysis between support and business metrics.
    """
    logger.info(f"[Tool:analyze_support_sales_correlation] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    # Load both support and sales data
    support_data = analyzer.data_loader.load_support_data(days=days)
    sales_data = analyzer.data_loader.load_sales_data(days=days)
    
    combined_data = {
        "support": support_data,
        "sales": sales_data,
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="support_sales_correlation",
        additional_context="Analyze correlation between support metrics and sales performance. Identify if support issues are impacting revenue."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_support_sales_correlation"
    
    return result


# ==================== Tool Registry ====================

def get_support_tools() -> List:
    """
    Get all support analysis tools.
    
    Returns:
        List of LangChain tools for support analysis
    """
    return [
        analyze_support_status,
        analyze_ticket_volume,
        analyze_customer_sentiment,
        analyze_issue_categories,
        analyze_support_trend,
        analyze_refunds_returns,
        identify_support_spike_cause,
        get_support_summary,
        analyze_support_sales_correlation,
    ]


def get_tool_descriptions() -> Dict[str, str]:
    """
    Get descriptions for all support tools.
    
    Useful for supervisor/router to understand tool capabilities.
    """
    tools = get_support_tools()
    return {tool.name: tool.description for tool in tools}
