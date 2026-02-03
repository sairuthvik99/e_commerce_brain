"""
Inventory Agent LangChain Tools

LLM-driven tools for inventory and stockout analysis.
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

class InventoryAnalysisInput(BaseModel):
    """Input schema for inventory analysis tool."""
    question: str = Field(description="The user's question about inventory")
    days: int = Field(default=7, description="Number of days for baseline comparison")


class StockoutAnalysisInput(BaseModel):
    """Input schema for stockout analysis tool."""
    question: str = Field(description="The user's question about stockouts")
    target_date: Optional[str] = Field(default=None, description="Target date for analysis (YYYY-MM-DD)")


class StockoutTrendInput(BaseModel):
    """Input schema for stockout trend analysis."""
    question: str = Field(description="The user's question about stockout trends")
    days: int = Field(default=7, description="Number of days to analyze for trends")


class CriticalProductInput(BaseModel):
    """Input schema for critical product analysis."""
    question: str = Field(description="The user's question about critical products")
    threshold: int = Field(default=5, description="Top N critical products to analyze")


class InventoryImpactInput(BaseModel):
    """Input schema for inventory impact analysis."""
    question: str = Field(description="The user's question about inventory impact on sales")
    days: int = Field(default=7, description="Number of days to analyze")


class RestockPriorityInput(BaseModel):
    """Input schema for restock prioritization."""
    question: str = Field(description="The user's question about restock priorities")
    top_n: int = Field(default=10, description="Number of top products to prioritize")


class ProductListInput(BaseModel):
    """Input schema for listing all products."""
    question: str = Field(description="The user's question about product listing")
    include_out_of_stock_only: bool = Field(default=False, description="Only show out of stock products")


class ProductDetailInput(BaseModel):
    """Input schema for getting product details."""
    product_id: int = Field(description="The product ID to look up")
    question: str = Field(default="", description="Optional question about the product")


class StockUpdateProposalInput(BaseModel):
    """Input schema for proposing stock updates."""
    product_id: int = Field(description="The product ID to update")
    quantity_change: int = Field(description="Amount to add (positive) or remove (negative)")
    reason: str = Field(default="User requested stock update", description="Reason for the update")


# ==================== LLM Analysis Helper ====================

class InventoryLLMAnalyzer:
    """
    Helper class to analyze inventory data using LLM.
    Sends data and question to LLM and returns structured response.
    
    Table Access: daily_metrics, inventory_snapshots
    """
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            api_key=Settings.DIAL_API_KEY,
            azure_endpoint=Settings.AZURE_ENDPOINT,
            api_version=Settings.API_VERSION,
            model=Settings.AGENT_MODELS.get("inventory", "gpt-4"),
            temperature=0.2,
        )
        # Use agent-specific data loader with restricted table access
        # Inventory agent can only access: daily_metrics, inventory_snapshots
        self.data_loader = create_agent_loader("inventory")
        logger.info(f"[InventoryLLMAnalyzer] Initialized with table access: {self.data_loader.allowed_tables}")
    
    @observe(name="inventory_llm_analyze")
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
            data: Inventory data from database
            analysis_type: Type of analysis (stockout, trend, impact, etc.)
            additional_context: Extra context for the LLM
            
        Returns:
            Dict with finding, evidence, confidence, and raw LLM response
        """
        try:
            # Load the analysis prompt
            system_prompt = load_prompt(
                agent="inventory",
                task="analysis",
                prompt_type="system"
            )
            
            user_prompt = load_prompt(
                agent="inventory",
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
            
            logger.info(f"[InventoryLLMAnalyzer] Calling LLM for {analysis_type} analysis...")
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
            
            logger.info(f"[InventoryLLMAnalyzer] Analysis complete: {result.get('finding', '')[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"[InventoryLLMAnalyzer] Analysis failed: {e}")
            return {
                "finding": f"Analysis failed: {str(e)}",
                "evidence": ["error"],
                "confidence": 0.0,
                "error": str(e)
            }


# Global analyzer instance (lazy initialization)
_analyzer: Optional[InventoryLLMAnalyzer] = None


def get_analyzer() -> InventoryLLMAnalyzer:
    """Get or create the global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = InventoryLLMAnalyzer()
    return _analyzer


# ==================== LangChain Tools ====================

@tool("analyze_inventory_status", args_schema=InventoryAnalysisInput)
def analyze_inventory_status(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze overall inventory status and stockout situation.
    
    Use this tool when the user asks:
    - "What's the current inventory situation?"
    - "How is our inventory looking?"
    - "Are there any inventory issues?"
    - "Overall inventory health check"
    
    Returns comprehensive inventory analysis including stockout counts and severity.
    """
    logger.info(f"[Tool:analyze_inventory_status] Question: {question}")
    
    analyzer = get_analyzer()
    
    # Load inventory data
    inventory_data = analyzer.data_loader.load_inventory_data()
    baseline = analyzer.data_loader.load_inventory_baseline(days=days)
    
    # Combine data for analysis
    combined_data = {
        **inventory_data,
        "baseline": baseline,
        "analysis_period_days": days
    }
    
    # Let LLM analyze the data
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="general_inventory_status",
        additional_context=f"Analyzing {days}-day inventory data to answer the user's question."
    )
    
    # Add raw data to result
    result["raw_data"] = combined_data
    result["tool"] = "analyze_inventory_status"
    
    return result


@tool("analyze_stockout_events", args_schema=StockoutAnalysisInput)
def analyze_stockout_events(
    question: str, 
    target_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze stockout events and affected products.
    
    Use this tool when the user asks:
    - "Which products are out of stock?"
    - "What stockouts occurred yesterday?"
    - "Which items are unavailable?"
    - "Show me stockout details"
    
    Returns detailed stockout information including affected products.
    """
    logger.info(f"[Tool:analyze_stockout_events] Question: {question}, date: {target_date}")
    
    analyzer = get_analyzer()
    
    # Load stockout data for specific date
    inventory_data = analyzer.data_loader.load_inventory_data(target_date=target_date)
    baseline = analyzer.data_loader.load_inventory_baseline(days=7)
    
    combined_data = {
        **inventory_data,
        "baseline": baseline,
        "target_date": target_date or "yesterday"
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="stockout_events",
        additional_context=f"Analyze stockout events for {target_date or 'yesterday'}. List affected products and their impact."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_stockout_events"
    
    return result


@tool("analyze_stockout_trend", args_schema=StockoutTrendInput)
def analyze_stockout_trend(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze stockout trends over time.
    
    Use this tool when the user asks:
    - "Is the stockout situation improving or worsening?"
    - "What's the stockout trend over the past week?"
    - "Are we seeing more or fewer stockouts?"
    - "Stockout pattern analysis"
    
    Returns trend analysis with direction and pattern insights.
    """
    logger.info(f"[Tool:analyze_stockout_trend] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    # Load inventory data and baseline for trend analysis
    inventory_data = analyzer.data_loader.load_inventory_data()
    baseline = analyzer.data_loader.load_inventory_baseline(days=days)
    
    combined_data = {
        **inventory_data,
        "baseline": baseline,
        "trend_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="stockout_trend",
        additional_context=f"Analyze {days}-day stockout trend. Identify pattern direction and predict near-term outlook."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_stockout_trend"
    
    return result


@tool("identify_critical_stockouts", args_schema=CriticalProductInput)
def identify_critical_stockouts(question: str, threshold: int = 5) -> Dict[str, Any]:
    """
    Identify critical products affected by stockouts.
    
    Use this tool when the user asks:
    - "Which high-value products are out of stock?"
    - "Are any critical items affected?"
    - "Top-selling products with stockouts"
    - "What's the revenue impact of current stockouts?"
    
    Returns list of critical/high-impact products with stockout issues.
    """
    logger.info(f"[Tool:identify_critical_stockouts] Question: {question}, threshold: {threshold}")
    
    analyzer = get_analyzer()
    
    inventory_data = analyzer.data_loader.load_inventory_data()
    baseline = analyzer.data_loader.load_inventory_baseline(days=7)
    
    combined_data = {
        **inventory_data,
        "baseline": baseline,
        "critical_threshold": threshold
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="critical_stockouts",
        additional_context=f"Identify top {threshold} critical products affected by stockouts. Focus on high-value/high-demand items."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "identify_critical_stockouts"
    
    return result


@tool("analyze_inventory_impact", args_schema=InventoryImpactInput)
def analyze_inventory_impact(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Analyze inventory impact on sales and revenue.
    
    Use this tool when the user asks:
    - "How are stockouts affecting sales?"
    - "What's the revenue loss from out-of-stock items?"
    - "Is inventory impacting our performance?"
    - "Correlation between stockouts and sales drop"
    
    Returns impact analysis connecting inventory issues to sales performance.
    """
    logger.info(f"[Tool:analyze_inventory_impact] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    # Load both inventory and sales data for correlation
    inventory_data = analyzer.data_loader.load_inventory_data()
    inventory_baseline = analyzer.data_loader.load_inventory_baseline(days=days)
    sales_data = analyzer.data_loader.load_sales_data(days=days)
    
    combined_data = {
        "inventory": {
            **inventory_data,
            "baseline": inventory_baseline
        },
        "sales": sales_data,
        "analysis_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="inventory_sales_impact",
        additional_context="Analyze correlation between stockouts and sales. Quantify potential revenue loss and impact."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "analyze_inventory_impact"
    
    return result


@tool("prioritize_restock", args_schema=RestockPriorityInput)
def prioritize_restock(question: str, top_n: int = 10) -> Dict[str, Any]:
    """
    Prioritize products for restocking based on impact and demand.
    
    Use this tool when the user asks:
    - "Which products should we restock first?"
    - "Restock priority list"
    - "What's the order of importance for restocking?"
    - "Urgent restock recommendations"
    
    Returns prioritized list of products needing restocking.
    """
    logger.info(f"[Tool:prioritize_restock] Question: {question}, top_n: {top_n}")
    
    analyzer = get_analyzer()
    
    inventory_data = analyzer.data_loader.load_inventory_data()
    baseline = analyzer.data_loader.load_inventory_baseline(days=7)
    
    combined_data = {
        **inventory_data,
        "baseline": baseline,
        "priority_count": top_n
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="restock_priority",
        additional_context=f"Create prioritized restock list for top {top_n} products based on demand, revenue impact, and criticality."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "prioritize_restock"
    
    return result


@tool("get_inventory_summary", args_schema=InventoryAnalysisInput)
def get_inventory_summary(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Get a comprehensive inventory summary for reporting.
    
    Use this tool when the user asks:
    - "Summarize the inventory situation"
    - "Give me an inventory overview"
    - "Executive summary of inventory status"
    - "What's the inventory status?"
    
    Returns a formatted summary suitable for reports.
    """
    logger.info(f"[Tool:get_inventory_summary] Question: {question}")
    
    analyzer = get_analyzer()
    
    inventory_data = analyzer.data_loader.load_inventory_data()
    baseline = analyzer.data_loader.load_inventory_baseline(days=days)
    
    combined_data = {
        **inventory_data,
        "baseline": baseline,
        "summary_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="summary",
        additional_context="Create clear, executive-level inventory summary. Include key metrics, stockout severity, and notable issues."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "get_inventory_summary"
    
    return result


@tool("compare_stockout_severity", args_schema=InventoryAnalysisInput)
def compare_stockout_severity(question: str, days: int = 7) -> Dict[str, Any]:
    """
    Compare current stockout severity against historical baseline.
    
    Use this tool when the user asks:
    - "Are stockouts worse than usual?"
    - "How does today's situation compare to normal?"
    - "Is this stockout level abnormal?"
    - "Stockout severity assessment"
    
    Returns severity comparison with baseline context.
    """
    logger.info(f"[Tool:compare_stockout_severity] Question: {question}, days: {days}")
    
    analyzer = get_analyzer()
    
    inventory_data = analyzer.data_loader.load_inventory_data()
    baseline = analyzer.data_loader.load_inventory_baseline(days=days)
    
    combined_data = {
        **inventory_data,
        "baseline": baseline,
        "comparison_period_days": days
    }
    
    result = analyzer.analyze(
        question=question,
        data=combined_data,
        analysis_type="severity_comparison",
        additional_context=f"Compare current stockouts against {days}-day baseline. Calculate severity multiplier and assess if situation is abnormal."
    )
    
    result["raw_data"] = combined_data
    result["tool"] = "compare_stockout_severity"
    
    return result


@tool("list_all_products", args_schema=ProductListInput)
def list_all_products(question: str, include_out_of_stock_only: bool = False) -> Dict[str, Any]:
    """
    List all products in the inventory with their stock levels.
    
    Use this tool when the user asks:
    - "List all products"
    - "Show me all products in inventory"
    - "Give me the list of all products"
    - "What products do we have?"
    - "Show inventory list"
    
    Returns a complete list of all products with their current stock status.
    """
    logger.info(f"[Tool:list_all_products] Question: {question}, out_of_stock_only: {include_out_of_stock_only}")
    
    analyzer = get_analyzer()
    
    # Load all products inventory
    inventory_data = analyzer.data_loader.load_all_products_inventory()
    
    # Filter if needed
    products = inventory_data.get('products', [])
    if include_out_of_stock_only:
        products = [p for p in products if p.get('is_out_of_stock', False)]
    
    # Format for display
    result = {
        "finding": f"Found {len(products)} products in the inventory.",
        "total_products": inventory_data.get('total_products', 0),
        "products": products,
        "summary": inventory_data.get('summary', {}),
        "evidence": ["product_list_retrieved", f"total_products_{len(products)}"],
        "confidence": 0.95,
        "tool": "list_all_products"
    }
    
    # Add formatted product list for LLM response
    product_lines = []
    for p in products[:50]:  # Limit to first 50 for display
        stock_status = "OUT OF STOCK" if p.get('is_out_of_stock') else f"Stock: {p.get('available_stock', 0)}"
        product_lines.append(f"- Product ID {p.get('product_id')}: {stock_status}")
    
    if len(products) > 50:
        product_lines.append(f"... and {len(products) - 50} more products")
    
    result["formatted_list"] = "\n".join(product_lines)
    
    return result


@tool("get_product_details", args_schema=ProductDetailInput)
def get_product_details(product_id: int, question: str = "") -> Dict[str, Any]:
    """
    Get detailed inventory information for a specific product.
    
    Use this tool when the user asks:
    - "What's the stock for product X?"
    - "Show me product 123 details"
    - "Check stock level for product ID X"
    - "Is product X in stock?"
    
    Returns detailed inventory information for the specified product.
    """
    logger.info(f"[Tool:get_product_details] Product ID: {product_id}")
    
    analyzer = get_analyzer()
    
    # Load product inventory
    product_data = analyzer.data_loader.load_product_inventory(product_id)
    
    if not product_data.get('found', False):
        return {
            "finding": f"Product {product_id} was not found in the inventory.",
            "product_id": product_id,
            "found": False,
            "evidence": ["product_not_found"],
            "confidence": 0.95,
            "tool": "get_product_details"
        }
    
    stock_status = "OUT OF STOCK" if product_data.get('is_out_of_stock') else "IN STOCK"
    stock_level = product_data.get('available_stock', 0)
    threshold = product_data.get('stock_threshold', 10)
    
    finding = f"Product {product_id} is {stock_status} with {stock_level} units available."
    if stock_level <= threshold and stock_level > 0:
        finding += f" Warning: Stock is below threshold ({threshold})."
    
    result = {
        "finding": finding,
        "product_id": product_id,
        "available_stock": stock_level,
        "stock_threshold": threshold,
        "is_out_of_stock": product_data.get('is_out_of_stock', False),
        "out_of_stock_since": str(product_data.get('out_of_stock_since')) if product_data.get('out_of_stock_since') else None,
        "snapshot_timestamp": str(product_data.get('snapshot_timestamp')),
        "found": True,
        "evidence": [f"product_{product_id}", f"stock_level_{stock_level}", stock_status.lower().replace(" ", "_")],
        "confidence": 0.95,
        "tool": "get_product_details"
    }
    
    return result


@tool("propose_stock_update", args_schema=StockUpdateProposalInput)
def propose_stock_update(product_id: int, quantity_change: int, reason: str = "User requested stock update") -> Dict[str, Any]:
    """
    Propose a stock update for a product. This creates a HITL action that requires human approval.
    
    Use this tool when the user asks:
    - "Increase stock of product X by 10"
    - "Add 50 units to product 123"
    - "Restock product X with 100 units"
    - "Decrease stock of product Y by 5"
    
    IMPORTANT: This tool does NOT directly update the stock. It creates a proposal
    that must be approved by a human through the HITL interface before the update is executed.
    
    Returns a proposal ID that needs human approval.
    """
    logger.info(f"[Tool:propose_stock_update] Product ID: {product_id}, Change: {quantity_change}, Reason: {reason}")
    
    analyzer = get_analyzer()
    
    # First, get current product details
    product_data = analyzer.data_loader.load_product_inventory(product_id)
    
    if not product_data.get('found', False):
        return {
            "finding": f"Cannot propose stock update: Product {product_id} was not found in the inventory.",
            "product_id": product_id,
            "success": False,
            "requires_approval": False,
            "evidence": ["product_not_found"],
            "confidence": 0.95,
            "tool": "propose_stock_update"
        }
    
    current_stock = product_data.get('available_stock', 0)
    new_stock = max(0, current_stock + quantity_change)
    
    # Generate proposal ID
    import uuid
    proposal_id = f"stock_update_{uuid.uuid4().hex[:12]}"
    
    # Store the pending action (this will be retrieved by the HITL endpoint)
    from backend.agents.inventory.hitl_actions import store_pending_stock_update
    store_pending_stock_update(
        proposal_id=proposal_id,
        product_id=product_id,
        current_stock=current_stock,
        quantity_change=quantity_change,
        new_stock=new_stock,
        reason=reason
    )
    
    action_type = "increase" if quantity_change > 0 else "decrease"
    
    result = {
        "finding": f"Stock update proposal created for Product {product_id}. "
                   f"Proposed to {action_type} stock from {current_stock} to {new_stock} units ({quantity_change:+d}). "
                   f"This action requires human approval before execution.",
        "proposal_id": proposal_id,
        "product_id": product_id,
        "current_stock": current_stock,
        "quantity_change": quantity_change,
        "new_stock": new_stock,
        "reason": reason,
        "success": True,
        "requires_approval": True,
        "approval_message": "Please use the HITL interface to approve or reject this stock update.",
        "evidence": [
            f"stock_update_proposal_{proposal_id}",
            f"product_{product_id}",
            f"change_{quantity_change:+d}",
            "hitl_required"
        ],
        "confidence": 0.95,
        "tool": "propose_stock_update",
        "hitl_action": {
            "action_id": proposal_id,
            "action_type": "stock_update",
            "description": f"{action_type.capitalize()} stock for Product {product_id} by {abs(quantity_change)} units",
            "target": f"Product {product_id}",
            "parameters": {
                "product_id": product_id,
                "quantity_change": quantity_change,
                "current_stock": current_stock,
                "new_stock": new_stock
            },
            "estimated_impact": f"Stock will change from {current_stock} to {new_stock}",
            "risk_level": "medium" if abs(quantity_change) > 50 else "low"
        }
    }
    
    return result


# ==================== Tool Registry ====================

def get_inventory_tools() -> List:
    """
    Get all inventory analysis tools.
    
    Returns:
        List of LangChain tools for inventory analysis
    """
    return [
        analyze_inventory_status,
        analyze_stockout_events,
        analyze_stockout_trend,
        identify_critical_stockouts,
        analyze_inventory_impact,
        prioritize_restock,
        get_inventory_summary,
        compare_stockout_severity,
        list_all_products,
        get_product_details,
        propose_stock_update,
    ]


def get_tool_descriptions() -> Dict[str, str]:
    """
    Get descriptions for all inventory tools.
    
    Useful for supervisor/router to understand tool capabilities.
    """
    tools = get_inventory_tools()
    return {tool.name: tool.description for tool in tools}
