"""
Sales Agent LangChain Tools

LLM-driven tools for sales analysis.
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

class SalesAnalysisInput(BaseModel):
    """Input schema for sales analysis tool."""
    question: str = Field(description="The user's question about sales")
    days: int = Field(default=7, description="Number of days for baseline comparison")


class RevenueComparisonInput(BaseModel):
    """Input schema for revenue comparison tool."""
    question: str = Field(description="The user's question about revenue comparison")
    period1: str = Field(default="yesterday", description="First period (yesterday, today, etc.)")
    period2: str = Field(default="last_week", description="Second period for comparison")


class SalesTrendInput(BaseModel):
    """Input schema for sales trend analysis."""
    question: str = Field(description="The user's question about sales trends")
    days: int = Field(default=7, description="Number of days to analyze for trends")


class ProductContributionInput(BaseModel):
    """Input schema for product contribution analysis."""
    question: str = Field(description="The user's question about product contributions")
    top_n: int = Field(default=5, description="Number of top products to analyze")


class AnomalyDetectionInput(BaseModel):
    """Input schema for anomaly detection."""
    question: str = Field(description="The user's question about anomalies")
    threshold: float = Field(default=0.15, description="Threshold for anomaly detection (15% default)")


# ==================== LLM Analysis Helper ====================

class SalesLLMAnalyzer:
    """
    Helper class to analyze sales data using LLM.
    Sends data and question to LLM and returns structured response.
    
    Table Access: daily_metrics, orders
    """
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS.get("sales", "gpt-4"),
            temperature=0.2,
        )
        # Use agent-specific data loader with restricted table access
        # Sales agent can only access: daily_metrics, orders
        self.data_loader = create_agent_loader("sales")
        logger.info(f"[SalesLLMAnalyzer] Initialized with table access: {self.data_loader.allowed_tables}")
    
    @observe(name="sales_llm_analyze")
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
            data: Sales data from database
            analysis_type: Type of analysis (general, comparison, trend, etc.)
            additional_context: Extra context for the LLM
            
        Returns:
            Dict with finding, evidence, confidence, and raw LLM response
        """
        try:
            # Load the analysis prompt
            system_prompt = load_prompt(
                agent="sales",
                task="analysis",
                prompt_type="system"
            )
            
            user_prompt = load_prompt(
                agent="sales",
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
            
            logger.info(f"[SalesLLMAnalyzer] Calling LLM for {analysis_type} analysis...")
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
            
            logger.info(f"[SalesLLMAnalyzer] Analysis complete: {result.get('finding', '')[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"[SalesLLMAnalyzer] Analysis failed: {e}")
            return {
                "finding": f"Analysis failed: {str(e)}",
                "evidence": ["error"],
                "confidence": 0.0,
                "error": str(e)
            }


# Global analyzer instance (lazy initialization)
_analyzer: Optional[SalesLLMAnalyzer] = None

def get_analyzer() -> SalesLLMAnalyzer:
    """Get or create the global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SalesLLMAnalyzer()
    return _analyzer


# ==================== LangChain Tools ====================

@tool("analyze_sales_performance", args_schema=SalesAnalysisInput)
def analyze_sales_performance(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze overall sales performance and identify issues.
    
    Use this tool when the user asks:
    - "Why did sales drop yesterday?"
    - "What happened with sales?"
    - "Sales performance analysis"
    - "Was the drop due to fewer orders or lower order value?"
    
    Returns a comprehensive analysis of revenue, orders, and AOV.
    """
    logger.info(f"[Tool:analyze_sales_performance] Question: {question}")
    
    analyzer = get_analyzer()
    
    # Load sales data
    sales_data = analyzer.data_loader.load_sales_data(days=days)
    
    # Let LLM analyze the data
    result = analyzer.analyze(
        question=question,
        data=sales_data,
        analysis_type="general_sales_performance",
        additional_context=f"Analyzing {days}-day sales data to answer the user's question."
    )
    
    # Add raw data to result
    result["raw_data"] = sales_data
    result["tool"] = "analyze_sales_performance"
    
    return result


@tool("compare_sales_periods", args_schema=RevenueComparisonInput)
def compare_sales_periods(
    question: str, 
    period1: str = "yesterday", 
    period2: str = "last_week"
) -> Dict[str, Any]:
    """
    Compare sales between two time periods.
    
    Use this tool when the user asks:
    - "Compare yesterday's sales with last week"
    - "How did sales compare to previous period?"
    - "Sales comparison analysis"
    - "Is today's performance better or worse?"
    
    Returns comparative analysis between periods.
    """
    logger.info(f"[Tool:compare_sales_periods] Question: {question}, {period1} vs {period2}")
    
    analyzer = get_analyzer()
    
    # Load more days for comparison
    sales_data = analyzer.data_loader.load_sales_data(days=14)
    
    result = analyzer.analyze(
        question=question,
        data=sales_data,
        analysis_type="period_comparison",
        additional_context=f"Compare {period1} with {period2}. Provide specific metrics and percentage changes."
    )
    
    result["raw_data"] = sales_data
    result["tool"] = "compare_sales_periods"
    result["comparison"] = {"period1": period1, "period2": period2}
    
    return result


@tool("analyze_sales_trend", args_schema=SalesTrendInput)
def analyze_sales_trend(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze sales trends over time.
    
    Use this tool when the user asks:
    - "Did sales recover today or is the trend continuing?"
    - "What's the sales trend over the past week?"
    - "Is sales declining or improving?"
    - "Show sales patterns"
    
    Returns trend analysis with direction and momentum.
    """
    logger.info(f"[Tool:analyze_sales_trend] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    sales_data = analyzer.data_loader.load_sales_data(days=days)
    
    result = analyzer.analyze(
        question=question,
        data=sales_data,
        analysis_type="trend_analysis",
        additional_context="Identify trend direction (improving, declining, stable), pattern (consistent, volatile), and forecast."
    )
    
    result["raw_data"] = sales_data
    result["tool"] = "analyze_sales_trend"
    
    return result


@tool("identify_sales_anomaly", args_schema=AnomalyDetectionInput)
def identify_sales_anomaly(question: str, threshold: float = 0.15) -> Dict[str, Any]:
    """
    Detect if current sales are normal or an anomaly.
    
    Use this tool when the user asks:
    - "Is this drop normal or an anomaly?"
    - "Is this unusual behavior?"
    - "Should I be concerned about this?"
    - "Is this within normal variance?"
    
    Returns anomaly assessment with statistical context.
    """
    logger.info(f"[Tool:identify_sales_anomaly] Question: {question}, threshold: {threshold}")
    
    analyzer = get_analyzer()
    
    # Get more historical data for anomaly detection
    sales_data = analyzer.data_loader.load_sales_data(days=14)
    
    result = analyzer.analyze(
        question=question,
        data=sales_data,
        analysis_type="anomaly_detection",
        additional_context=f"Determine if current values are anomalies using {threshold*100}% threshold. Consider historical variance and patterns."
    )
    
    result["raw_data"] = sales_data
    result["tool"] = "identify_sales_anomaly"
    result["threshold"] = threshold
    
    return result


@tool("identify_drop_cause", args_schema=SalesAnalysisInput)
def identify_drop_cause(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Identify the primary cause of a sales drop.
    
    Use this tool when the user asks:
    - "Was the drop due to fewer orders or lower order value?"
    - "What caused the sales drop?"
    - "Why are orders/revenue down?"
    - "Root cause of sales decline"
    
    Returns analysis of whether drop is due to order count, AOV, or both.
    """
    logger.info(f"[Tool:identify_drop_cause] Question: {question}")
    
    analyzer = get_analyzer()
    
    sales_data = analyzer.data_loader.load_sales_data(days=days)
    
    result = analyzer.analyze(
        question=question,
        data=sales_data,
        analysis_type="drop_cause_analysis",
        additional_context="Determine if revenue drop is primarily due to: 1) Fewer orders, 2) Lower AOV, 3) Both. Quantify each factor's contribution."
    )
    
    result["raw_data"] = sales_data
    result["tool"] = "identify_drop_cause"
    
    return result


@tool("analyze_regional_performance", args_schema=SalesAnalysisInput)
def analyze_regional_performance(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze sales performance by region.
    
    Use this tool when the user asks:
    - "Did any region perform worse than usual?"
    - "Which regions are underperforming?"
    - "Regional sales breakdown"
    - "Geographic sales analysis"
    
    Returns regional performance comparison.
    """
    logger.info(f"[Tool:analyze_regional_performance] Question: {question}")
    
    analyzer = get_analyzer()
    
    # Load sales data (which may include regional breakdown)
    sales_data = analyzer.data_loader.load_sales_data(days=days)
    
    result = analyzer.analyze(
        question=question,
        data=sales_data,
        analysis_type="regional_analysis",
        additional_context="Analyze performance by region. Identify underperforming regions and quantify the gap."
    )
    
    result["raw_data"] = sales_data
    result["tool"] = "analyze_regional_performance"
    
    return result


@tool("get_sales_summary", args_schema=SalesAnalysisInput)
def get_sales_summary(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Get a comprehensive sales summary for reporting.
    
    Use this tool when the user asks:
    - "Summarize yesterday's sales"
    - "Give me a sales overview"
    - "Executive summary of sales"
    - "What's the sales status?"
    
    Returns a formatted summary suitable for reports.
    """
    logger.info(f"[Tool:get_sales_summary] Question: {question}")
    
    analyzer = get_analyzer()
    
    sales_data = analyzer.data_loader.load_sales_data(days=days)
    
    result = analyzer.analyze(
        question=question,
        data=sales_data,
        analysis_type="summary",
        additional_context="Create a clear, executive-level summary. Include key metrics, trends, and notable observations."
    )
    
    result["raw_data"] = sales_data
    result["tool"] = "get_sales_summary"
    
    return result


# ==================== Tool Registry ====================

def get_sales_tools() -> List:
    """
    Get all sales analysis tools.
    
    Returns:
        List of LangChain tools for sales analysis
    """
    return [
        analyze_sales_performance,
        compare_sales_periods,
        analyze_sales_trend,
        identify_sales_anomaly,
        identify_drop_cause,
        analyze_regional_performance,
        get_sales_summary,
    ]


def get_tool_descriptions() -> Dict[str, str]:
    """
    Get descriptions for all sales tools.
    
    Useful for supervisor/router to understand tool capabilities.
    """
    tools = get_sales_tools()
    return {tool.name: tool.description for tool in tools}
