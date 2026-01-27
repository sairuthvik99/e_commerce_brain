"""
Sales Agent Analysis Logic

Pure logic functions for sales data analysis.
No I/O, no LLM - just calculations.
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def calculate_revenue_drop(sales_data: Dict) -> float:
    """
    Calculate revenue drop percentage.
    
    Args:
        sales_data: Dict with yesterday_revenue and avg_revenue
    
    Returns:
        Drop percentage (positive number means drop)
    """
    yesterday = sales_data.get('yesterday_revenue', 0)
    average = sales_data.get('avg_revenue', 1)  # Avoid division by zero
    
    if average == 0:
        return 0.0
    
    drop_pct = ((average - yesterday) / average) * 100
    
    logger.info(f"[SalesLogic] Revenue drop: {drop_pct:.2f}%")
    return max(0, drop_pct)  # Only positive drops


def calculate_order_drop(sales_data: Dict) -> float:
    """
    Calculate order count drop percentage.
    
    Args:
        sales_data: Dict with yesterday_orders and avg_orders
    
    Returns:
        Drop percentage
    """
    yesterday = sales_data.get('yesterday_orders', 0)
    average = sales_data.get('avg_orders', 1)
    
    if average == 0:
        return 0.0
    
    drop_pct = ((average - yesterday) / average) * 100
    return max(0, drop_pct)


def calculate_aov_drop(sales_data: Dict) -> float:
    """
    Calculate AOV (Average Order Value) drop percentage.
    
    Args:
        sales_data: Dict with yesterday_aov and avg_aov
    
    Returns:
        Drop percentage
    """
    yesterday = sales_data.get('yesterday_aov', 0)
    average = sales_data.get('avg_aov', 1)
    
    if average == 0:
        return 0.0
    
    drop_pct = ((average - yesterday) / average) * 100
    return max(0, drop_pct)


def analyze_drop_cause(sales_data: Dict) -> str:
    """
    Determine primary cause of sales drop.
    
    Returns:
        "order_count" | "aov" | "both" | "none"
    """
    order_drop = calculate_order_drop(sales_data)
    aov_drop = calculate_aov_drop(sales_data)
    
    if order_drop > 10 and aov_drop > 10:
        return "both"
    elif order_drop > 10:
        return "order_count"
    elif aov_drop > 10:
        return "aov"
    else:
        return "none"


def calculate_confidence(revenue_drop: float, order_drop: float, aov_drop: float) -> float:
    """
    Calculate confidence score based on magnitude of drops.
    
    Rules:
    - Higher drop = higher confidence
    - Multiple metrics dropping = higher confidence
    
    Returns:
        Confidence score (0.0 to 1.0)
    """
    # Base confidence on revenue drop magnitude
    if revenue_drop >= 40:
        base_confidence = 0.95
    elif revenue_drop >= 30:
        base_confidence = 0.90
    elif revenue_drop >= 20:
        base_confidence = 0.85
    elif revenue_drop >= 10:
        base_confidence = 0.75
    else:
        base_confidence = 0.60
    
    # Boost confidence if multiple metrics show issues
    metrics_affected = sum([
        revenue_drop > 10,
        order_drop > 10,
        aov_drop > 10
    ])
    
    if metrics_affected >= 2:
        base_confidence = min(0.98, base_confidence + 0.05)
    
    logger.info(f"[SalesLogic] Confidence: {base_confidence:.2%}")
    return base_confidence


def build_evidence(sales_data: Dict, analysis: Dict) -> List[str]:
    """
    Build evidence list based on analysis.
    
    Returns:
        List of evidence strings
    """
    evidence = []
    
    revenue_drop = analysis.get('revenue_drop_pct', 0)
    order_drop = analysis.get('order_drop_pct', 0)
    aov_drop = analysis.get('aov_drop_pct', 0)
    
    if revenue_drop > 10:
        evidence.append(f"revenue_drop_{revenue_drop:.1f}pct")
    
    if order_drop > 10:
        evidence.append(f"order_count_drop_{order_drop:.1f}pct")
    elif order_drop < -5:  # Orders increased
        evidence.append("order_count_stable")
    
    if aov_drop > 10:
        evidence.append(f"aov_drop_{aov_drop:.1f}pct")
    elif aov_drop < -5:  # AOV increased
        evidence.append("aov_stable")
    
    evidence.append("data_source_mcp")
    
    return evidence