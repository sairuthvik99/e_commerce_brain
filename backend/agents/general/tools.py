"""
General Agent LangChain Tools

LLM-driven tools for cross-domain business analysis.
Each tool is designed for comprehensive business analysis with access to all data sources.
"""

from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from backend.settings import Settings
from backend.utils.data_loader import DataLoader
from backend.utils.prompt_loader import load_prompt
from langfuse import observe
import json
import logging

logger = logging.getLogger(__name__)


# ==================== Pydantic Input Schemas ====================

class BusinessHealthInput(BaseModel):
    """Input schema for business health analysis."""
    question: str = Field(description="The user's question about business health")
    days: int = Field(default=7, description="Number of days for analysis")


class CrossDomainInput(BaseModel):
    """Input schema for cross-domain analysis."""
    question: str = Field(description="The user's question requiring cross-domain analysis")
    domains: List[str] = Field(
        default=["sales", "inventory", "marketing", "support"],
        description="Domains to include in analysis"
    )
    days: int = Field(default=7, description="Number of days for analysis")


class DailySummaryInput(BaseModel):
    """Input schema for daily summary."""
    question: str = Field(description="The user's question about daily summary")
    include_recommendations: bool = Field(
        default=True,
        description="Whether to include recommendations"
    )


class KPIComparisonInput(BaseModel):
    """Input schema for KPI comparison."""
    question: str = Field(description="The user's question about KPI comparison")
    kpis: List[str] = Field(
        default=["revenue", "orders", "conversions", "stockouts", "tickets"],
        description="KPIs to compare"
    )
    days: int = Field(default=7, description="Number of days for comparison")


class TrendAnalysisInput(BaseModel):
    """Input schema for multi-domain trend analysis."""
    question: str = Field(description="The user's question about trends")
    domains: List[str] = Field(
        default=["sales", "inventory", "marketing", "support"],
        description="Domains to analyze trends for"
    )
    days: int = Field(default=14, description="Number of days for trend analysis")


class DomainQueryInput(BaseModel):
    """Input schema for querying specific domain data."""
    question: str = Field(description="The user's question about domain data")
    domain: str = Field(
        description="Domain to query: sales, inventory, marketing, or support"
    )
    days: int = Field(default=7, description="Number of days for query")


class CorrelationInput(BaseModel):
    """Input schema for finding correlations."""
    question: str = Field(description="The user's question about correlations")
    metrics: List[str] = Field(
        default=["revenue", "stockouts", "marketing_spend", "tickets"],
        description="Metrics to check for correlations"
    )
    days: int = Field(default=14, description="Number of days for correlation analysis")


# ==================== LLM Analysis Helper ====================

class GeneralLLMAnalyzer:
    """
    Helper class to analyze cross-domain data using LLM.
    Sends comprehensive data and question to LLM and returns structured response.
    """
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS.get("general", "gpt-4"),
            temperature=0.3,
        )
        self.data_loader = DataLoader(use_direct=True)
        logger.info("[GeneralLLMAnalyzer] Initialized")
    
    @observe(name="general_llm_analyze")
    def analyze(
        self,
        question: str,
        data: Dict[str, Any],
        analysis_type: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send data and question to LLM for cross-domain analysis.
        
        Args:
            question: User's question
            data: Combined data from all domains
            analysis_type: Type of analysis (health, comparison, trend, etc.)
            additional_context: Extra context for the LLM
            
        Returns:
            Dict with finding, evidence, confidence, and raw LLM response
        """
        try:
            # Load the analysis prompt
            system_prompt = load_prompt(
                agent="general",
                task="analysis",
                prompt_type="system"
            )
            
            user_prompt = load_prompt(
                agent="general",
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
            
            logger.info(f"[GeneralLLMAnalyzer] Calling LLM for {analysis_type} analysis...")
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
                    "evidence": ["llm_analysis", "cross_domain"],
                    "confidence": 0.75,
                    "analysis_details": content
                }
            
            logger.info(f"[GeneralLLMAnalyzer] Analysis complete: {result.get('finding', '')[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"[GeneralLLMAnalyzer] Analysis failed: {e}")
            return {
                "finding": f"Analysis failed: {str(e)}",
                "evidence": ["error"],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def load_all_data(self, days: int = 7) -> Dict[str, Any]:
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
            logger.warning(f"[GeneralLLMAnalyzer] Failed to load sales data: {e}")
            all_data["sales"] = {"error": str(e)}
        
        try:
            all_data["inventory"] = self.data_loader.load_inventory_data()
        except Exception as e:
            logger.warning(f"[GeneralLLMAnalyzer] Failed to load inventory data: {e}")
            all_data["inventory"] = {"error": str(e)}
        
        try:
            all_data["inventory_baseline"] = self.data_loader.load_inventory_baseline(days=days)
        except Exception as e:
            logger.warning(f"[GeneralLLMAnalyzer] Failed to load inventory baseline: {e}")
            all_data["inventory_baseline"] = {"error": str(e)}
        
        try:
            all_data["marketing"] = self.data_loader.load_marketing_data(days=days)
        except Exception as e:
            logger.warning(f"[GeneralLLMAnalyzer] Failed to load marketing data: {e}")
            all_data["marketing"] = {"error": str(e)}
        
        try:
            all_data["support"] = self.data_loader.load_support_data(days=days)
        except Exception as e:
            logger.warning(f"[GeneralLLMAnalyzer] Failed to load support data: {e}")
            all_data["support"] = {"error": str(e)}
        
        return all_data


# Global analyzer instance (lazy initialization)
_analyzer: Optional[GeneralLLMAnalyzer] = None


def get_analyzer() -> GeneralLLMAnalyzer:
    """Get or create the global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = GeneralLLMAnalyzer()
    return _analyzer


# ==================== LangChain Tools ====================

@tool("analyze_business_health", args_schema=BusinessHealthInput)
def analyze_business_health(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze overall business health across all domains.
    
    Use this tool when the user asks:
    - "How is the business doing?"
    - "Give me a business health overview"
    - "What's the overall status of operations?"
    - "Summarize yesterday's business health"
    - "Is everything running smoothly?"
    
    Returns comprehensive analysis of all business metrics.
    """
    logger.info(f"[Tool:analyze_business_health] Question: {question}")
    
    analyzer = get_analyzer()
    
    # Load all domain data
    all_data = analyzer.load_all_data(days=days)
    
    # Let LLM analyze the data
    result = analyzer.analyze(
        question=question,
        data=all_data,
        analysis_type="business_health_overview",
        additional_context="Provide a holistic view of business health across all domains. Identify key issues and highlight any concerning trends."
    )
    
    result["raw_data"] = all_data
    result["tool"] = "analyze_business_health"
    
    return result


@tool("analyze_cross_domain", args_schema=CrossDomainInput)
def analyze_cross_domain(
    question: str,
    domains: List[str] = ["sales", "inventory", "marketing", "support"],
    days: int = 7
) -> Dict[str, Any]:
    """
    Perform cross-domain analysis to find relationships and impacts.
    
    Use this tool when the user asks:
    - "Was the sales drop caused by inventory, marketing, or customer issues?"
    - "How are different domains affecting each other?"
    - "Find connections between problems in different areas"
    - "What's causing the overall performance decline?"
    
    Returns analysis of how different domains interact.
    """
    logger.info(f"[Tool:analyze_cross_domain] Question: {question}, domains: {domains}")
    
    analyzer = get_analyzer()
    
    # Load data for specified domains
    all_data = {}
    
    if "sales" in domains:
        try:
            all_data["sales"] = analyzer.data_loader.load_sales_data(days=days)
        except Exception as e:
            all_data["sales"] = {"error": str(e)}
    
    if "inventory" in domains:
        try:
            all_data["inventory"] = analyzer.data_loader.load_inventory_data()
            all_data["inventory_baseline"] = analyzer.data_loader.load_inventory_baseline(days=days)
        except Exception as e:
            all_data["inventory"] = {"error": str(e)}
    
    if "marketing" in domains:
        try:
            all_data["marketing"] = analyzer.data_loader.load_marketing_data(days=days)
        except Exception as e:
            all_data["marketing"] = {"error": str(e)}
    
    if "support" in domains:
        try:
            all_data["support"] = analyzer.data_loader.load_support_data(days=days)
        except Exception as e:
            all_data["support"] = {"error": str(e)}
    
    result = analyzer.analyze(
        question=question,
        data=all_data,
        analysis_type="cross_domain_analysis",
        additional_context=f"Analyze interactions between: {', '.join(domains)}. Identify causal relationships and impact chains."
    )
    
    result["raw_data"] = all_data
    result["tool"] = "analyze_cross_domain"
    result["domains_analyzed"] = domains
    
    return result


@tool("get_daily_summary", args_schema=DailySummaryInput)
def get_daily_summary(
    question: str,
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """
    Get a comprehensive daily summary of all operations.
    
    Use this tool when the user asks:
    - "Summarize yesterday's operations"
    - "Give me a daily report"
    - "What happened yesterday across all areas?"
    - "Executive summary of business performance"
    
    Returns a formatted daily summary suitable for reports.
    """
    logger.info(f"[Tool:get_daily_summary] Question: {question}")
    
    analyzer = get_analyzer()
    
    # Load yesterday's data
    all_data = analyzer.load_all_data(days=7)
    
    result = analyzer.analyze(
        question=question,
        data=all_data,
        analysis_type="daily_summary",
        additional_context=f"Create an executive-level daily summary. {'Include actionable recommendations.' if include_recommendations else 'Focus on metrics only.'}"
    )
    
    result["raw_data"] = all_data
    result["tool"] = "get_daily_summary"
    result["includes_recommendations"] = include_recommendations
    
    return result


@tool("compare_kpis", args_schema=KPIComparisonInput)
def compare_kpis(
    question: str,
    kpis: List[str] = ["revenue", "orders", "conversions", "stockouts", "tickets"],
    days: int = 7
) -> Dict[str, Any]:
    """
    Compare key performance indicators across domains.
    
    Use this tool when the user asks:
    - "Compare all KPIs with last week"
    - "Which metrics improved or declined?"
    - "Show me a KPI dashboard view"
    - "How do all metrics compare to baseline?"
    
    Returns KPI comparison with percentages and trends.
    """
    logger.info(f"[Tool:compare_kpis] Question: {question}, kpis: {kpis}")
    
    analyzer = get_analyzer()
    
    # Load all data for KPI extraction
    all_data = analyzer.load_all_data(days=days)
    
    result = analyzer.analyze(
        question=question,
        data=all_data,
        analysis_type="kpi_comparison",
        additional_context=f"Compare these KPIs: {', '.join(kpis)}. Show percentage changes vs baseline. Highlight significant deviations."
    )
    
    result["raw_data"] = all_data
    result["tool"] = "compare_kpis"
    result["kpis_compared"] = kpis
    
    return result


@tool("analyze_trends", args_schema=TrendAnalysisInput)
def analyze_trends(
    question: str,
    domains: List[str] = ["sales", "inventory", "marketing", "support"],
    days: int = 14
) -> Dict[str, Any]:
    """
    Analyze trends across multiple domains over time.
    
    Use this tool when the user asks:
    - "What are the trends across all areas?"
    - "Is the business improving or declining overall?"
    - "Show me trend patterns"
    - "How have things changed over the past two weeks?"
    
    Returns trend analysis with direction and momentum.
    """
    logger.info(f"[Tool:analyze_trends] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    # Load extended data for trend analysis
    all_data = analyzer.load_all_data(days=days)
    
    result = analyzer.analyze(
        question=question,
        data=all_data,
        analysis_type="trend_analysis",
        additional_context=f"Analyze trends for: {', '.join(domains)} over {days} days. Identify direction (improving/declining/stable) and momentum."
    )
    
    result["raw_data"] = all_data
    result["tool"] = "analyze_trends"
    result["domains_analyzed"] = domains
    result["days_analyzed"] = days
    
    return result


@tool("query_domain_data", args_schema=DomainQueryInput)
def query_domain_data(
    question: str,
    domain: str,
    days: int = 7
) -> Dict[str, Any]:
    """
    Query specific domain data for detailed analysis.
    
    Use this tool when the user asks about a specific domain:
    - "Show me sales data"
    - "What are the inventory levels?"
    - "Get marketing campaign data"
    - "Show support ticket details"
    
    Returns detailed data for the specified domain.
    """
    logger.info(f"[Tool:query_domain_data] Question: {question}, domain: {domain}")
    
    analyzer = get_analyzer()
    
    # Load data for specified domain
    domain_data = {}
    
    if domain.lower() == "sales":
        domain_data = analyzer.data_loader.load_sales_data(days=days)
    elif domain.lower() == "inventory":
        domain_data = analyzer.data_loader.load_inventory_data()
        domain_data["baseline"] = analyzer.data_loader.load_inventory_baseline(days=days)
    elif domain.lower() == "marketing":
        domain_data = analyzer.data_loader.load_marketing_data(days=days)
    elif domain.lower() == "support":
        domain_data = analyzer.data_loader.load_support_data(days=days)
    else:
        domain_data = {"error": f"Unknown domain: {domain}. Valid: sales, inventory, marketing, support"}
    
    result = analyzer.analyze(
        question=question,
        data=domain_data,
        analysis_type=f"{domain}_data_query",
        additional_context=f"Provide detailed analysis for {domain} domain based on the user's question."
    )
    
    result["raw_data"] = domain_data
    result["tool"] = "query_domain_data"
    result["domain"] = domain
    
    return result


@tool("find_correlations", args_schema=CorrelationInput)
def find_correlations(
    question: str,
    metrics: List[str] = ["revenue", "stockouts", "marketing_spend", "tickets"],
    days: int = 14
) -> Dict[str, Any]:
    """
    Find correlations between different business metrics.
    
    Use this tool when the user asks:
    - "Are stockouts related to sales drops?"
    - "Does marketing spend correlate with conversions?"
    - "Find relationships between metrics"
    - "What factors are correlated?"
    
    Returns correlation analysis between specified metrics.
    """
    logger.info(f"[Tool:find_correlations] Question: {question}, metrics: {metrics}")
    
    analyzer = get_analyzer()
    
    # Load extended data for correlation analysis
    all_data = analyzer.load_all_data(days=days)
    
    result = analyzer.analyze(
        question=question,
        data=all_data,
        analysis_type="correlation_analysis",
        additional_context=f"Find correlations between: {', '.join(metrics)}. Look for positive/negative correlations and potential causal relationships."
    )
    
    result["raw_data"] = all_data
    result["tool"] = "find_correlations"
    result["metrics_analyzed"] = metrics
    result["days_analyzed"] = days
    
    return result


# ==================== Tool Registry ====================

def get_general_tools() -> List:
    """
    Get all general analysis tools.
    
    Returns:
        List of LangChain tools for general analysis
    """
    return [
        analyze_business_health,
        analyze_cross_domain,
        get_daily_summary,
        compare_kpis,
        analyze_trends,
        query_domain_data,
        find_correlations,
    ]


def get_tool_descriptions() -> Dict[str, str]:
    """
    Get descriptions for all general tools.
    
    Useful for supervisor/router to understand tool capabilities.
    """
    tools = get_general_tools()
    return {tool.name: tool.description for tool in tools}
