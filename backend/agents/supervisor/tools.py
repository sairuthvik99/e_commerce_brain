"""
Supervisor Agent LangChain Tools

Tools for intent classification, agent routing, and cross-domain analysis.
The LLM decides which agents to call and how to synthesize results.
"""

from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from backend.settings import Settings
from backend.utils.prompt_loader import load_prompt
from langfuse import observe
import json
import logging

logger = logging.getLogger(__name__)


# ==================== Pydantic Input Schemas ====================

class IntentClassificationInput(BaseModel):
    """Input schema for intent classification."""
    question: str = Field(description="The user's question to classify")


class AgentRoutingInput(BaseModel):
    """Input schema for agent routing decisions."""
    question: str = Field(description="The user's question")
    intent: str = Field(description="Classified intent from intent detection")


class CrossDomainAnalysisInput(BaseModel):
    """Input schema for cross-domain analysis."""
    question: str = Field(description="The user's question requiring multi-domain analysis")
    domains: List[str] = Field(
        default=["sales", "inventory", "marketing", "support"],
        description="Domains to analyze"
    )


class MemoryQueryInput(BaseModel):
    """Input schema for memory/history queries."""
    question: str = Field(description="Question about past incidents or actions")
    query_type: str = Field(
        default="similar_incidents",
        description="Type: similar_incidents, past_actions, effectiveness"
    )


class ActionRecommendationInput(BaseModel):
    """Input schema for action recommendations."""
    question: str = Field(description="The action-oriented question/command")
    findings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Findings from domain agents"
    )


class SummaryReportInput(BaseModel):
    """Input schema for summary/report generation."""
    question: str = Field(description="The reporting question")
    report_type: str = Field(
        default="executive_summary",
        description="Type: executive_summary, detailed, recommendations"
    )
    findings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Findings from all agents"
    )


# ==================== LLM Helper ====================

class SupervisorLLMHelper:
    """Helper class for supervisor LLM operations."""
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS.get("supervisor", "gpt-4"),
            temperature=0.1,  # Low temperature for consistent routing
        )
        logger.info("[SupervisorLLMHelper] Initialized")
    
    @observe(name="supervisor_llm_analyze")
    def analyze(
        self,
        question: str,
        context: Dict[str, Any],
        analysis_type: str
    ) -> Dict[str, Any]:
        """
        General LLM analysis for supervisor tasks.
        
        Args:
            question: User's question
            context: Additional context
            analysis_type: Type of analysis
            
        Returns:
            Dict with analysis results
        """
        try:
            system_prompt = f"""You are an E-commerce Operations Supervisor AI.
You help route questions to appropriate domain agents and synthesize multi-domain insights.

Analysis type: {analysis_type}

Respond with a valid JSON object."""

            user_prompt = f"""Question: {question}

Context:
{json.dumps(context, indent=2, default=str)}

Provide your analysis as JSON."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            # Parse JSON response
            try:
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()
                return json.loads(content)
            except json.JSONDecodeError:
                return {"result": content}
                
        except Exception as e:
            logger.error(f"[SupervisorLLMHelper] Analysis failed: {e}")
            return {"error": str(e)}


# Global helper instance
_helper: Optional[SupervisorLLMHelper] = None

def get_helper() -> SupervisorLLMHelper:
    """Get or create the global helper instance."""
    global _helper
    if _helper is None:
        _helper = SupervisorLLMHelper()
    return _helper


# ==================== Intent & Routing Tools ====================

@tool("classify_user_intent", args_schema=IntentClassificationInput)
def classify_user_intent(question: str) -> Dict[str, Any]:
    """
    Classify the user's question into an intent category.
    
    Use this tool when you need to understand what domain(s) a question relates to.
    
    Intent categories:
    - sales: Revenue, orders, conversions, AOV
    - inventory: Stock levels, stockouts, supply chain
    - marketing: Campaigns, ads, promotions, traffic
    - support: Complaints, tickets, refunds, reviews
    - general: Multi-domain or overall business health
    - memory: Questions about past incidents or actions
    - action: Commands to take action (HITL required)
    
    Returns intent classification with confidence.
    """
    logger.info(f"[Tool:classify_user_intent] Question: {question}")
    
    helper = get_helper()
    
    context = {
        "available_intents": [
            "sales", "inventory", "marketing", "support",
            "general", "memory", "action"
        ],
        "intent_descriptions": {
            "sales": "Revenue, orders, conversions, AOV, pricing",
            "inventory": "Stock levels, stockouts, supply chain, reordering",
            "marketing": "Campaigns, ads, promotions, traffic, acquisition",
            "support": "Complaints, tickets, refunds, returns, reviews",
            "general": "Multi-domain questions, overall business health",
            "memory": "Past incidents, historical actions, what worked before",
            "action": "Commands to fix, restock, run discount, pause campaign"
        }
    }
    
    result = helper.analyze(
        question=question,
        context=context,
        analysis_type="intent_classification"
    )
    
    # Ensure we have required fields
    if "intent" not in result:
        # Fallback: use simple keyword matching
        question_lower = question.lower()
        if any(w in question_lower for w in ["sales", "revenue", "order", "aov"]):
            result["intent"] = "sales"
        elif any(w in question_lower for w in ["stock", "inventory", "restock"]):
            result["intent"] = "inventory"
        elif any(w in question_lower for w in ["campaign", "marketing", "promotion", "ad"]):
            result["intent"] = "marketing"
        elif any(w in question_lower for w in ["complaint", "refund", "return", "ticket"]):
            result["intent"] = "support"
        elif any(w in question_lower for w in ["before", "last time", "previously", "history"]):
            result["intent"] = "memory"
        elif any(w in question_lower for w in ["fix", "run", "pause", "create", "restock"]):
            result["intent"] = "action"
        else:
            result["intent"] = "general"
    
    result["tool"] = "classify_user_intent"
    return result


@tool("determine_agents_to_call", args_schema=AgentRoutingInput)
def determine_agents_to_call(question: str, intent: str) -> Dict[str, Any]:
    """
    Determine which domain agents should be called for a question.
    
    Use this tool after classifying intent to decide the routing.
    
    Returns list of agents to call and their priority.
    """
    logger.info(f"[Tool:determine_agents_to_call] Intent: {intent}")
    
    # Base routing map
    routing_map = {
        "sales": ["sales"],
        "inventory": ["inventory"],
        "marketing": ["marketing"],
        "support": ["support"],
        "general": ["sales", "inventory", "marketing", "support"],
        "memory": [],  # Memory queries don't need domain agents
        "action": ["sales", "inventory", "marketing", "support"],  # Need context
    }
    
    agents = routing_map.get(intent, ["sales"])  # Default to sales
    
    # Let LLM refine if question suggests cross-domain
    helper = get_helper()
    result = helper.analyze(
        question=question,
        context={
            "detected_intent": intent,
            "suggested_agents": agents,
            "available_agents": ["sales", "inventory", "marketing", "support"]
        },
        analysis_type="agent_routing"
    )
    
    # Use LLM's suggestion if provided
    if "agents" in result and isinstance(result["agents"], list):
        agents = result["agents"]
    
    return {
        "intent": intent,
        "agents_to_call": agents,
        "priority": result.get("priority", "normal"),
        "reasoning": result.get("reasoning", "Based on intent classification"),
        "tool": "determine_agents_to_call"
    }


# ==================== Cross-Domain Analysis Tools ====================

@tool("analyze_cross_domain_impact", args_schema=CrossDomainAnalysisInput)
def analyze_cross_domain_impact(
    question: str,
    domains: List[str] = None
) -> Dict[str, Any]:
    """
    Analyze how issues in one domain affect other domains.
    
    Use this tool when the user asks:
    - "Was the sales drop caused by inventory, marketing, or customer issues?"
    - "Correlate complaints with sales drop"
    - "Did out-of-stock items also have active campaigns?"
    - "Show me all contributing factors"
    
    Returns cross-domain correlation analysis.
    """
    if domains is None:
        domains = ["sales", "inventory", "marketing", "support"]
    
    logger.info(f"[Tool:analyze_cross_domain_impact] Domains: {domains}")
    
    helper = get_helper()
    
    result = helper.analyze(
        question=question,
        context={
            "domains_to_analyze": domains,
            "analysis_focus": "cross_domain_correlations",
            "output_format": {
                "primary_cause_domain": "string",
                "contributing_domains": ["list"],
                "correlations": [{"domain1": "string", "domain2": "string", "relationship": "string"}],
                "confidence": "float"
            }
        },
        analysis_type="cross_domain_impact"
    )
    
    result["tool"] = "analyze_cross_domain_impact"
    result["domains_analyzed"] = domains
    return result


@tool("identify_root_cause", args_schema=CrossDomainAnalysisInput)
def identify_root_cause(
    question: str,
    domains: List[str] = None
) -> Dict[str, Any]:
    """
    Identify the root cause of a business issue across domains.
    
    Use this tool when the user asks:
    - "What's the root cause of the sales drop?"
    - "Why is this happening?"
    - "What's causing the issue?"
    
    Returns root cause analysis with domain attribution.
    """
    if domains is None:
        domains = ["sales", "inventory", "marketing", "support"]
    
    logger.info(f"[Tool:identify_root_cause] Domains: {domains}")
    
    helper = get_helper()
    
    result = helper.analyze(
        question=question,
        context={
            "domains": domains,
            "analysis_type": "root_cause_analysis",
            "required_output": {
                "root_cause": "description",
                "domain": "primary domain",
                "evidence": ["list of evidence"],
                "confidence": "float 0-1"
            }
        },
        analysis_type="root_cause"
    )
    
    result["tool"] = "identify_root_cause"
    return result


# ==================== Memory & History Tools ====================

@tool("query_past_incidents", args_schema=MemoryQueryInput)
def query_past_incidents(
    question: str,
    query_type: str = "similar_incidents"
) -> Dict[str, Any]:
    """
    Query historical data about past incidents and actions.
    
    Use this tool when the user asks:
    - "Has this happened before?"
    - "What did we do last time sales dropped like this?"
    - "Did discounts help previously?"
    - "Which actions worked best in past incidents?"
    
    Returns relevant historical incidents and outcomes.
    """
    logger.info(f"[Tool:query_past_incidents] Type: {query_type}")
    
    helper = get_helper()
    
    result = helper.analyze(
        question=question,
        context={
            "query_type": query_type,
            "query_types_supported": [
                "similar_incidents",
                "past_actions",
                "action_effectiveness"
            ]
        },
        analysis_type="memory_query"
    )
    
    # Note: In a real implementation, this would query the vector database
    # For now, the LLM provides a structured response
    
    result["tool"] = "query_past_incidents"
    result["query_type"] = query_type
    result["source"] = "memory_store"
    return result


# ==================== Action & Recommendation Tools ====================

@tool("generate_action_recommendations", args_schema=ActionRecommendationInput)
def generate_action_recommendations(
    question: str,
    findings: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate recommended actions based on analysis findings.
    
    Use this tool when the user asks:
    - "What actions do you recommend and why?"
    - "What should we do about this?"
    - "How can we fix this?"
    
    Returns prioritized action recommendations.
    """
    if findings is None:
        findings = {}
    
    logger.info(f"[Tool:generate_action_recommendations] Question: {question}")
    
    helper = get_helper()
    
    result = helper.analyze(
        question=question,
        context={
            "findings": findings,
            "output_format": {
                "recommendations": [
                    {
                        "action": "description",
                        "domain": "sales|inventory|marketing|support",
                        "priority": "high|medium|low",
                        "expected_impact": "description",
                        "requires_approval": "boolean"
                    }
                ],
                "confidence": "float"
            }
        },
        analysis_type="action_recommendations"
    )
    
    result["tool"] = "generate_action_recommendations"
    result["hitl_required"] = True  # Actions require human approval
    return result


@tool("prepare_hitl_action", args_schema=ActionRecommendationInput)
def prepare_hitl_action(
    question: str,
    findings: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Prepare a Human-in-the-Loop action proposal.
    
    Use this tool when the user gives action commands:
    - "Fix the issue"
    - "Restock affected products"
    - "Run a 10% discount on top 3 products"
    - "Pause the worst-performing campaign"
    - "Create a support ticket for this issue"
    
    Returns action proposal that requires human approval.
    """
    if findings is None:
        findings = {}
    
    logger.info(f"[Tool:prepare_hitl_action] Command: {question}")
    
    helper = get_helper()
    
    result = helper.analyze(
        question=question,
        context={
            "findings": findings,
            "action_types": [
                "restock", "discount", "pause_campaign",
                "create_ticket", "send_alert", "update_price"
            ],
            "output_format": {
                "action_type": "string",
                "action_details": {},
                "affected_items": [],
                "estimated_impact": "string",
                "approval_required": True,
                "risk_level": "low|medium|high"
            }
        },
        analysis_type="hitl_preparation"
    )
    
    result["tool"] = "prepare_hitl_action"
    result["status"] = "pending_approval"
    result["requires_human_approval"] = True
    return result


# ==================== Reporting Tools ====================

@tool("generate_executive_summary", args_schema=SummaryReportInput)
def generate_executive_summary(
    question: str,
    report_type: str = "executive_summary",
    findings: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate an executive summary or business report.
    
    Use this tool when the user asks:
    - "Summarize yesterday's business health"
    - "Create an executive summary of the issue"
    - "Give me a confidence score for your analysis"
    
    Returns formatted summary report.
    """
    if findings is None:
        findings = {}
    
    logger.info(f"[Tool:generate_executive_summary] Type: {report_type}")
    
    helper = get_helper()
    
    result = helper.analyze(
        question=question,
        context={
            "report_type": report_type,
            "findings": findings,
            "report_types": {
                "executive_summary": "High-level overview for leadership",
                "detailed": "Comprehensive analysis with all metrics",
                "recommendations": "Focus on actionable next steps"
            }
        },
        analysis_type="report_generation"
    )
    
    result["tool"] = "generate_executive_summary"
    result["report_type"] = report_type
    return result


@tool("calculate_confidence_score", args_schema=SummaryReportInput)
def calculate_confidence_score(
    question: str,
    report_type: str = "confidence",
    findings: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Calculate overall confidence score for the analysis.
    
    Use this tool when the user asks:
    - "Give me a confidence score for your analysis"
    - "How confident are you in this analysis?"
    - "What's the reliability of these findings?"
    
    Returns confidence score with breakdown.
    """
    if findings is None:
        findings = {}
    
    logger.info(f"[Tool:calculate_confidence_score]")
    
    helper = get_helper()
    
    result = helper.analyze(
        question=question,
        context={
            "findings": findings,
            "confidence_factors": [
                "data_quality",
                "data_completeness",
                "pattern_strength",
                "cross_domain_agreement"
            ]
        },
        analysis_type="confidence_calculation"
    )
    
    result["tool"] = "calculate_confidence_score"
    return result


# ==================== Tool Registry ====================

def get_supervisor_tools() -> List:
    """
    Get all supervisor tools.
    
    Returns:
        List of LangChain tools for supervisor operations
    """
    return [
        classify_user_intent,
        determine_agents_to_call,
        analyze_cross_domain_impact,
        identify_root_cause,
        query_past_incidents,
        generate_action_recommendations,
        prepare_hitl_action,
        generate_executive_summary,
        calculate_confidence_score,
    ]


def get_tool_descriptions() -> Dict[str, str]:
    """Get descriptions for all supervisor tools."""
    tools = get_supervisor_tools()
    return {tool.name: tool.description for tool in tools}
