"""
Marketing Agent LangChain Tools

LLM-driven tools for marketing and campaign performance analysis.
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

class MarketingAnalysisInput(BaseModel):
    """Input schema for marketing analysis tool."""
    question: str = Field(description="The user's question about marketing")
    days: int = Field(default=7, description="Number of days for baseline comparison")


class CampaignPerformanceInput(BaseModel):
    """Input schema for campaign performance analysis."""
    question: str = Field(description="The user's question about campaign performance")
    days: int = Field(default=7, description="Number of days to analyze")


class ConversionAnalysisInput(BaseModel):
    """Input schema for conversion analysis."""
    question: str = Field(description="The user's question about conversions")
    days: int = Field(default=7, description="Number of days to analyze for trends")


class SpendAnalysisInput(BaseModel):
    """Input schema for spend analysis."""
    question: str = Field(description="The user's question about ad spend")
    days: int = Field(default=7, description="Number of days to analyze")


class ROIAnalysisInput(BaseModel):
    """Input schema for ROI/efficiency analysis."""
    question: str = Field(description="The user's question about marketing ROI or efficiency")
    days: int = Field(default=7, description="Number of days to analyze")


class CampaignComparisonInput(BaseModel):
    """Input schema for campaign comparison."""
    question: str = Field(description="The user's question about comparing campaigns")
    period1: str = Field(default="yesterday", description="First period for comparison")
    period2: str = Field(default="average", description="Second period for comparison")


# ==================== LLM Analysis Helper ====================

class MarketingLLMAnalyzer:
    """
    Helper class to analyze marketing data using LLM.
    Sends data and question to LLM and returns structured response.
    
    Table Access: daily_metrics, marketing_campaigns_daily
    """
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS.get("marketing", "gpt-4"),
            temperature=0.2,
        )
        # Use agent-specific data loader with restricted table access
        # Marketing agent can only access: daily_metrics, marketing_campaigns_daily
        self.data_loader = create_agent_loader("marketing")
        logger.info(f"[MarketingLLMAnalyzer] Initialized with table access: {self.data_loader.allowed_tables}")
    
    @observe(name="marketing_llm_analyze")
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
            data: Marketing data from database
            analysis_type: Type of analysis (campaign, conversion, roi, etc.)
            additional_context: Extra context for the LLM
            
        Returns:
            Dict with finding, evidence, confidence, and raw LLM response
        """
        try:
            # Load the analysis prompt
            system_prompt = load_prompt(
                agent="marketing",
                task="analysis",
                prompt_type="system"
            )
            
            user_prompt = load_prompt(
                agent="marketing",
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
            
            logger.info(f"[MarketingLLMAnalyzer] Calling LLM for {analysis_type} analysis...")
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
            
            logger.info(f"[MarketingLLMAnalyzer] Analysis complete: {result.get('finding', '')[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"[MarketingLLMAnalyzer] Analysis failed: {e}")
            return {
                "finding": f"Analysis failed: {str(e)}",
                "evidence": ["error"],
                "confidence": 0.0,
                "error": str(e)
            }


# Global analyzer instance (lazy initialization)
_analyzer: Optional[MarketingLLMAnalyzer] = None


def get_analyzer() -> MarketingLLMAnalyzer:
    """Get or create the global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = MarketingLLMAnalyzer()
    return _analyzer


# ==================== LangChain Tools ====================

@tool("analyze_marketing_performance", args_schema=MarketingAnalysisInput)
def analyze_marketing_performance(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze overall marketing performance and campaign health.
    
    Use this tool when the user asks:
    - "How is marketing performing?"
    - "What's the current state of our campaigns?"
    - "Marketing performance overview"
    - "Are our campaigns doing well?"
    
    Returns comprehensive marketing analysis including conversions, spend, and efficiency.
    """
    logger.info(f"[Tool:analyze_marketing_performance] Question: {question}")
    
    analyzer = get_analyzer()
    
    # Load marketing data
    marketing_data = analyzer.data_loader.load_marketing_data(days=days)
    
    combined_data = {
        **marketing_data,
        "analysis_period_days": days
    }
    
    # Let LLM analyze the data
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="general_marketing_performance",
        additional_context=f"Analyzing {days}-day marketing data to answer the user's question."
    )
    
    # Add raw data to result
    result["raw_data"] = combined_data
    result["tool"] = "analyze_marketing_performance"
    
    return result


@tool("analyze_campaign_conversions", args_schema=ConversionAnalysisInput)
def analyze_campaign_conversions(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze campaign conversion rates and trends.
    
    Use this tool when the user asks:
    - "Why did conversions drop?"
    - "What's happening with our conversion rates?"
    - "Conversion analysis"
    - "Are we getting fewer conversions?"
    
    Returns conversion analysis with trends and insights.
    """
    logger.info(f"[Tool:analyze_campaign_conversions] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    marketing_data = analyzer.data_loader.load_marketing_data(days=days)
    
    combined_data = {
        **marketing_data,
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="conversion_analysis",
        additional_context="Focus on conversion rates, changes, and potential causes for any drops or increases."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_campaign_conversions"
    
    return result


@tool("analyze_ad_spend", args_schema=SpendAnalysisInput)
def analyze_ad_spend(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze advertising spend patterns and efficiency.
    
    Use this tool when the user asks:
    - "How much are we spending on ads?"
    - "Is our ad spend efficient?"
    - "Spending analysis"
    - "Are we overspending or underspending?"
    
    Returns spend analysis with comparison to baseline.
    """
    logger.info(f"[Tool:analyze_ad_spend] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    marketing_data = analyzer.data_loader.load_marketing_data(days=days)
    
    combined_data = {
        **marketing_data,
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="spend_analysis",
        additional_context="Analyze ad spend patterns, changes from baseline, and spending efficiency."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_ad_spend"
    
    return result


@tool("analyze_marketing_roi", args_schema=ROIAnalysisInput)
def analyze_marketing_roi(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze marketing ROI and cost efficiency.
    
    Use this tool when the user asks:
    - "What's our marketing ROI?"
    - "Cost per conversion analysis"
    - "Are we getting good value from our spend?"
    - "Marketing efficiency metrics"
    
    Returns ROI analysis with cost per conversion and efficiency metrics.
    """
    logger.info(f"[Tool:analyze_marketing_roi] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    marketing_data = analyzer.data_loader.load_marketing_data(days=days)
    
    combined_data = {
        **marketing_data,
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="roi_efficiency_analysis",
        additional_context="Calculate and analyze marketing ROI, cost per conversion, and overall efficiency."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_marketing_roi"
    
    return result


@tool("analyze_campaign_status", args_schema=CampaignPerformanceInput)
def analyze_campaign_status(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze active and paused campaign status.
    
    Use this tool when the user asks:
    - "Which campaigns are active?"
    - "Are any campaigns paused?"
    - "Campaign status overview"
    - "How many campaigns are running?"
    
    Returns campaign status analysis including active, paused, and underperforming campaigns.
    """
    logger.info(f"[Tool:analyze_campaign_status] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    marketing_data = analyzer.data_loader.load_marketing_data(days=days)
    
    combined_data = {
        **marketing_data,
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="campaign_status",
        additional_context="Analyze campaign status - active, paused, performance by campaign if available."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_campaign_status"
    
    return result


@tool("compare_campaign_periods", args_schema=CampaignComparisonInput)
def compare_campaign_periods(
    question: str, 
    period1: str = "yesterday", 
    period2: str = "average"
) -> Dict[str, Any]:
    """
    Compare campaign performance between time periods.
    
    Use this tool when the user asks:
    - "Compare yesterday's performance with last week"
    - "How did campaigns perform compared to average?"
    - "Period-over-period comparison"
    - "Is performance better or worse than before?"
    
    Returns comparative analysis between periods.
    """
    logger.info(f"[Tool:compare_campaign_periods] Question: {question}, {period1} vs {period2}")
    
    analyzer = get_analyzer()
    
    # Load more days for comparison
    marketing_data = analyzer.data_loader.load_marketing_data(days=14)
    
    combined_data = {
        **marketing_data,
        "comparison": {"period1": period1, "period2": period2}
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="period_comparison",
        additional_context=f"Compare {period1} with {period2}. Provide specific metrics and percentage changes."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "compare_campaign_periods"
    result["comparison"] = {"period1": period1, "period2": period2}
    
    return result


@tool("identify_conversion_drop_cause", args_schema=MarketingAnalysisInput)
def identify_conversion_drop_cause(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Identify the root cause of conversion drops.
    
    Use this tool when the user asks:
    - "Why did conversions drop?"
    - "What caused the conversion decline?"
    - "Root cause of marketing issues"
    - "Diagnose conversion problems"
    
    Returns root cause analysis for conversion drops.
    """
    logger.info(f"[Tool:identify_conversion_drop_cause] Question: {question}")
    
    analyzer = get_analyzer()
    
    marketing_data = analyzer.data_loader.load_marketing_data(days=days)
    
    # Also load sales data to check for correlation
    sales_data = analyzer.data_loader.load_sales_data(days=days)
    
    combined_data = {
        "marketing": marketing_data,
        "sales": sales_data,
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="drop_cause_analysis",
        additional_context="Identify why conversions dropped. Consider spend changes, campaign status, and correlation with sales."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "identify_conversion_drop_cause"
    
    return result


@tool("get_marketing_summary", args_schema=MarketingAnalysisInput)
def get_marketing_summary(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Get a comprehensive marketing summary for reporting.
    
    Use this tool when the user asks:
    - "Summarize marketing performance"
    - "Give me a marketing overview"
    - "Executive summary of campaigns"
    - "What's the marketing status?"
    
    Returns a formatted summary suitable for reports.
    """
    logger.info(f"[Tool:get_marketing_summary] Question: {question}")
    
    analyzer = get_analyzer()
    
    marketing_data = analyzer.data_loader.load_marketing_data(days=days)
    
    combined_data = {
        **marketing_data,
        "summary_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="summary",
        additional_context="Create clear, executive-level marketing summary. Include key metrics, trends, and notable observations."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "get_marketing_summary"
    
    return result


@tool("analyze_marketing_sales_correlation", args_schema=MarketingAnalysisInput)
def analyze_marketing_sales_correlation(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze correlation between marketing activities and sales.
    
    Use this tool when the user asks:
    - "Is marketing affecting sales?"
    - "Correlation between campaigns and revenue"
    - "Marketing impact on sales"
    - "Are campaign issues causing sales drops?"
    
    Returns correlation analysis between marketing and sales performance.
    """
    logger.info(f"[Tool:analyze_marketing_sales_correlation] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    # Load both marketing and sales data
    marketing_data = analyzer.data_loader.load_marketing_data(days=days)
    sales_data = analyzer.data_loader.load_sales_data(days=days)
    
    combined_data = {
        "marketing": marketing_data,
        "sales": sales_data,
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="marketing_sales_correlation",
        additional_context="Analyze correlation between marketing metrics and sales performance. Identify if marketing issues are impacting revenue."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_marketing_sales_correlation"
    
    return result


# ==================== Tool Registry ====================

def get_marketing_tools() -> List:
    """
    Get all marketing analysis tools.
    
    Returns:
        List of LangChain tools for marketing analysis
    """
    return [
        analyze_marketing_performance,
        analyze_campaign_conversions,
        analyze_ad_spend,
        analyze_marketing_roi,
        analyze_campaign_status,
        compare_campaign_periods,
        identify_conversion_drop_cause,
        get_marketing_summary,
        analyze_marketing_sales_correlation,
    ]


def get_tool_descriptions() -> Dict[str, str]:
    """
    Get descriptions for all marketing tools.
    
    Useful for supervisor/router to understand tool capabilities.
    """
    tools = get_marketing_tools()
    return {tool.name: tool.description for tool in tools}
