"""
Sales Agent Utility Functions

Minimal utility functions for sales data processing.
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


# ==================== Data Validation ====================

def validate_sales_data(data: Dict[str, Any]) -> bool:
    """
    Validate that sales data has required fields.
    
    Args:
        data: Sales data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        'yesterday_revenue',
        'avg_revenue',
        'yesterday_orders',
        'avg_orders'
    ]
    
    for field in required_fields:
        if field not in data:
            logger.warning(f"[SalesLogic] Missing required field: {field}")
            return False
    
    return True


def get_default_sales_data() -> Dict[str, Any]:
    """
    Get default/placeholder sales data for error cases.
    
    Returns:
        Dict with zero values
    """
    return {
        'yesterday_revenue': 0,
        'avg_revenue': 0,
        'yesterday_orders': 0,
        'avg_orders': 0,
        'yesterday_aov': 0,
        'avg_aov': 0
    }


# ==================== Fallback Analysis (if LLM fails) ====================

def basic_revenue_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basic revenue analysis as fallback if LLM fails.
    
    Args:
        data: Sales data dictionary
        
    Returns:
        Dict with basic analysis
    """
    yesterday = data.get('yesterday_revenue', 0)
    average = data.get('avg_revenue', 1)
    
    change_pct = calculate_change_percentage(yesterday, average)
    
    if change_pct < -20:
        status = "significant_drop"
    elif change_pct < -10:
        status = "moderate_drop"
    elif change_pct < 0:
        status = "slight_drop"
    elif change_pct > 20:
        status = "significant_increase"
    elif change_pct > 10:
        status = "moderate_increase"
    else:
        status = "stable"
    
    return {
        "yesterday_revenue": yesterday,
        "avg_revenue": average,
        "change_percentage": change_pct,
        "status": status,
        "finding": f"Revenue {'dropped' if change_pct < 0 else 'increased'} by {abs(change_pct):.1f}% yesterday"
    }


def generate_fallback_finding(data: Dict[str, Any]) -> str:
    """
    Generate a simple finding if LLM is unavailable.
    
    Args:
        data: Sales data dictionary
        
    Returns:
        Simple finding string
    """
    analysis = basic_revenue_analysis(data)
    
    yesterday = format_currency(data.get('yesterday_revenue', 0))
    average = format_currency(data.get('avg_revenue', 0))
    change = analysis['change_percentage']
    
    return (
        f"Revenue was {yesterday} yesterday compared to {average} average "
        f"({'down' if change < 0 else 'up'} {abs(change):.1f}%)"
    )