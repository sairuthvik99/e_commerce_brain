"""
General Agent Utility Functions

Utility functions for general cross-domain data processing.
The actual analysis is done by the LLM in tools.py.

These functions are kept for backward compatibility and
can be used as fallbacks if LLM fails.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


# ==================== Data Formatting Utilities ====================

def format_currency(amount: float, currency: str = "₹") -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Numeric amount
        currency: Currency symbol (default INR)
        
    Returns:
        Formatted string like "₹45,000.00"
    """
    return f"{currency}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format value as percentage string.
    
    Args:
        value: Percentage value
        decimals: Decimal places
        
    Returns:
        Formatted string like "25.5%"
    """
    return f"{value:.{decimals}f}%"


def calculate_change_percentage(current: float, baseline: float) -> float:
    """
    Calculate percentage change between current and baseline.
    
    Args:
        current: Current value
        baseline: Baseline/average value
        
    Returns:
        Percentage change (positive = increase, negative = decrease)
    """
    if baseline == 0:
        return 0.0
    return ((current - baseline) / baseline) * 100


# ==================== Data Aggregation ====================

def aggregate_all_metrics(
    sales_data: Dict[str, Any],
    inventory_data: Dict[str, Any],
    marketing_data: Dict[str, Any],
    support_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate metrics from all domains into a unified summary.
    
    Args:
        sales_data: Sales metrics dict
        inventory_data: Inventory metrics dict
        marketing_data: Marketing metrics dict
        support_data: Support metrics dict
        
    Returns:
        Dict with aggregated metrics from all domains
    """
    aggregated = {
        "sales": {
            "yesterday_revenue": sales_data.get("yesterday_revenue", 0),
            "avg_revenue": sales_data.get("avg_revenue", 0),
            "yesterday_orders": sales_data.get("yesterday_orders", 0),
            "avg_orders": sales_data.get("avg_orders", 0),
            "yesterday_aov": sales_data.get("yesterday_aov", 0),
            "avg_aov": sales_data.get("avg_aov", 0),
        },
        "inventory": {
            "total_stockouts": inventory_data.get("total_stockouts", 0),
            "stockout_products": inventory_data.get("stockout_products", []),
        },
        "marketing": {
            "yesterday_conversions": marketing_data.get("yesterday_conversions", 0),
            "avg_conversions": marketing_data.get("avg_conversions", 0),
            "yesterday_spend": marketing_data.get("yesterday_spend", 0),
            "avg_spend": marketing_data.get("avg_spend", 0),
        },
        "support": {
            "yesterday_tickets": support_data.get("yesterday_tickets", 0),
            "avg_tickets": support_data.get("avg_tickets", 0),
            "yesterday_negative_pct": support_data.get("yesterday_negative_pct", 0),
        }
    }
    
    # Calculate change percentages
    aggregated["changes"] = {
        "revenue_change": calculate_change_percentage(
            aggregated["sales"]["yesterday_revenue"],
            aggregated["sales"]["avg_revenue"]
        ),
        "orders_change": calculate_change_percentage(
            aggregated["sales"]["yesterday_orders"],
            aggregated["sales"]["avg_orders"]
        ),
        "conversions_change": calculate_change_percentage(
            aggregated["marketing"]["yesterday_conversions"],
            aggregated["marketing"]["avg_conversions"]
        ),
        "tickets_change": calculate_change_percentage(
            aggregated["support"]["yesterday_tickets"],
            aggregated["support"]["avg_tickets"]
        ),
    }
    
    return aggregated


# ==================== Health Score Calculation ====================

def calculate_health_score(
    aggregated_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate an overall business health score.
    
    Args:
        aggregated_data: Aggregated metrics from all domains
        
    Returns:
        Dict with health score and component scores
    """
    changes = aggregated_data.get("changes", {})
    
    # Calculate component scores (0-100 scale)
    # Positive changes are good for revenue/orders/conversions
    # Negative changes are bad for tickets/stockouts
    
    def score_from_change(change: float, invert: bool = False) -> float:
        """Convert percentage change to 0-100 score."""
        if invert:
            change = -change
        
        # Map change to score: -50% = 0, 0% = 50, +50% = 100
        score = 50 + change
        return max(0, min(100, score))
    
    scores = {
        "revenue_score": score_from_change(changes.get("revenue_change", 0)),
        "orders_score": score_from_change(changes.get("orders_change", 0)),
        "conversions_score": score_from_change(changes.get("conversions_change", 0)),
        "tickets_score": score_from_change(changes.get("tickets_change", 0), invert=True),
    }
    
    # Handle stockouts separately
    inventory = aggregated_data.get("inventory", {})
    stockout_count = inventory.get("total_stockouts", 0)
    # 0 stockouts = 100, 10+ stockouts = 0
    scores["stockout_score"] = max(0, 100 - stockout_count * 10)
    
    # Calculate overall health score (weighted average)
    weights = {
        "revenue_score": 0.25,
        "orders_score": 0.20,
        "conversions_score": 0.15,
        "tickets_score": 0.15,
        "stockout_score": 0.25,
    }
    
    overall_score = sum(
        scores[key] * weight
        for key, weight in weights.items()
    )
    
    return {
        "overall_score": round(overall_score, 1),
        "component_scores": scores,
        "status": get_health_status(overall_score),
    }


def get_health_status(score: float) -> str:
    """
    Get health status label from score.
    
    Args:
        score: Health score (0-100)
        
    Returns:
        Status label
    """
    if score >= 80:
        return "excellent"
    elif score >= 65:
        return "good"
    elif score >= 50:
        return "fair"
    elif score >= 35:
        return "concerning"
    else:
        return "critical"


# ==================== Data Validation ====================

def validate_domain_data(data: Dict[str, Any], domain: str) -> bool:
    """
    Validate that domain data has minimum required fields.
    
    Args:
        data: Domain data dictionary
        domain: Domain name (sales, inventory, marketing, support)
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = {
        "sales": ["yesterday_revenue", "avg_revenue"],
        "inventory": ["total_stockouts"],
        "marketing": ["yesterday_conversions"],
        "support": ["yesterday_tickets"],
    }
    
    fields = required_fields.get(domain, [])
    
    for field in fields:
        if field not in data:
            logger.warning(f"[GeneralLogic] Missing required field '{field}' in {domain} data")
            return False
    
    return True


def get_default_domain_data(domain: str) -> Dict[str, Any]:
    """
    Get default/placeholder data for a domain when data is unavailable.
    
    Args:
        domain: Domain name
        
    Returns:
        Dict with zero/empty values
    """
    defaults = {
        "sales": {
            "yesterday_revenue": 0,
            "avg_revenue": 0,
            "yesterday_orders": 0,
            "avg_orders": 0,
            "yesterday_aov": 0,
            "avg_aov": 0,
        },
        "inventory": {
            "total_stockouts": 0,
            "stockout_products": [],
            "stockout_details": [],
        },
        "marketing": {
            "yesterday_conversions": 0,
            "avg_conversions": 0,
            "yesterday_spend": 0,
            "avg_spend": 0,
        },
        "support": {
            "yesterday_tickets": 0,
            "avg_tickets": 0,
            "yesterday_negative_pct": 0,
            "top_categories": [],
        },
    }
    
    return defaults.get(domain, {})


# ==================== Fallback Analysis (if LLM fails) ====================

def basic_health_analysis(aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basic health analysis as fallback if LLM fails.
    
    Args:
        aggregated_data: Aggregated metrics from all domains
        
    Returns:
        Dict with basic health analysis
    """
    health = calculate_health_score(aggregated_data)
    changes = aggregated_data.get("changes", {})
    
    # Generate simple finding
    issues = []
    
    if changes.get("revenue_change", 0) < -10:
        issues.append(f"revenue down {abs(changes['revenue_change']):.1f}%")
    
    if changes.get("orders_change", 0) < -10:
        issues.append(f"orders down {abs(changes['orders_change']):.1f}%")
    
    if aggregated_data.get("inventory", {}).get("total_stockouts", 0) > 3:
        issues.append(f"{aggregated_data['inventory']['total_stockouts']} products out of stock")
    
    if changes.get("tickets_change", 0) > 20:
        issues.append(f"support tickets up {changes['tickets_change']:.1f}%")
    
    if issues:
        finding = f"Business health is {health['status']}. Issues: {', '.join(issues)}."
    else:
        finding = f"Business health is {health['status']}. All metrics within normal range."
    
    return {
        "finding": finding,
        "health_score": health["overall_score"],
        "status": health["status"],
        "component_scores": health["component_scores"],
        "changes": changes,
    }


def generate_fallback_summary(aggregated_data: Dict[str, Any]) -> str:
    """
    Generate a simple summary if LLM is unavailable.
    
    Args:
        aggregated_data: Aggregated metrics from all domains
        
    Returns:
        Simple text summary
    """
    sales = aggregated_data.get("sales", {})
    inventory = aggregated_data.get("inventory", {})
    marketing = aggregated_data.get("marketing", {})
    support = aggregated_data.get("support", {})
    changes = aggregated_data.get("changes", {})
    
    summary = []
    
    # Sales summary
    revenue = format_currency(sales.get("yesterday_revenue", 0))
    orders = sales.get("yesterday_orders", 0)
    revenue_change = format_percentage(changes.get("revenue_change", 0))
    summary.append(f"Sales: {revenue} ({orders} orders, {revenue_change} vs avg)")
    
    # Inventory summary
    stockouts = inventory.get("total_stockouts", 0)
    summary.append(f"Inventory: {stockouts} products out of stock")
    
    # Marketing summary
    conversions = marketing.get("yesterday_conversions", 0)
    spend = format_currency(marketing.get("yesterday_spend", 0))
    summary.append(f"Marketing: {conversions} conversions, {spend} spend")
    
    # Support summary
    tickets = support.get("yesterday_tickets", 0)
    negative_pct = format_percentage(support.get("yesterday_negative_pct", 0))
    summary.append(f"Support: {tickets} tickets ({negative_pct} negative)")
    
    return " | ".join(summary)
