"""
Marketing Agent Analysis Logic

Analyzes campaign performance and conversion trends.
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def calculate_conversion_drop(marketing_data: Dict) -> float:
    """
    Calculate conversion drop percentage.
    
    Returns:
        Drop percentage
    """
    yesterday = marketing_data.get('yesterday_conversions', 0)
    average = marketing_data.get('avg_conversions', 1)
    
    if average == 0:
        return 0.0
    
    drop_pct = ((average - yesterday) / average) * 100
    
    logger.info(f"[MarketingLogic] Conversion drop: {drop_pct:.2f}%")
    return max(0, drop_pct)


def calculate_spend_change(marketing_data: Dict) -> float:
    """
    Calculate spend change percentage.
    
    Returns:
        Change percentage (negative = decrease)
    """
    yesterday = marketing_data.get('yesterday_spend', 0)
    average = marketing_data.get('avg_spend', 1)
    
    if average == 0:
        return 0.0
    
    change_pct = ((yesterday - average) / average) * 100
    
    logger.info(f"[MarketingLogic] Spend change: {change_pct:.2f}%")
    return change_pct


def calculate_efficiency(marketing_data: Dict) -> Dict:
    """
    Calculate marketing efficiency (conversions per dollar).
    
    Returns:
        Dict with efficiency metrics
    """
    yesterday_conv = marketing_data.get('yesterday_conversions', 0)
    yesterday_spend = marketing_data.get('yesterday_spend', 1)
    avg_conv = marketing_data.get('avg_conversions', 0)
    avg_spend = marketing_data.get('avg_spend', 1)
    
    yesterday_efficiency = yesterday_conv / yesterday_spend if yesterday_spend > 0 else 0
    avg_efficiency = avg_conv / avg_spend if avg_spend > 0 else 0
    
    efficiency_drop = ((avg_efficiency - yesterday_efficiency) / avg_efficiency * 100) if avg_efficiency > 0 else 0
    
    return {
        'yesterday_efficiency': yesterday_efficiency,
        'avg_efficiency': avg_efficiency,
        'efficiency_drop_pct': max(0, efficiency_drop)
    }


def analyze_campaign_status(marketing_data: Dict) -> Dict:
    """
    Analyze campaign status (active vs paused).
    
    Returns:
        Dict with campaign status info
    """
    active_campaigns = marketing_data.get('yesterday_active_campaigns', 0)
    
    return {
        'active_campaigns': active_campaigns,
        'has_paused_campaigns': active_campaigns < 5  # Assuming 8 total campaigns
    }


def calculate_confidence(conversion_drop: float, spend_change: float, efficiency_drop: float) -> float:
    """
    Calculate confidence based on conversion and spend metrics.
    
    Returns:
        Confidence score (0.0 to 1.0)
    """
    # Base confidence on conversion drop
    if conversion_drop >= 50:
        base_confidence = 0.92
    elif conversion_drop >= 30:
        base_confidence = 0.87
    elif conversion_drop >= 20:
        base_confidence = 0.80
    elif conversion_drop >= 10:
        base_confidence = 0.72
    else:
        base_confidence = 0.60
    
    # Adjust based on spend
    if abs(spend_change) < 10:  # Spend stable but conversions down
        base_confidence = min(0.95, base_confidence + 0.05)
    
    # Adjust based on efficiency
    if efficiency_drop > 30:
        base_confidence = min(0.95, base_confidence + 0.03)
    
    logger.info(f"[MarketingLogic] Confidence: {base_confidence:.2%}")
    return base_confidence


def build_evidence(marketing_data: Dict, analysis: Dict) -> List[str]:
    """
    Build evidence list.
    
    Returns:
        List of evidence strings
    """
    evidence = []
    
    conversion_drop = analysis.get('conversion_drop_pct', 0)
    spend_change = analysis.get('spend_change_pct', 0)
    efficiency_drop = analysis.get('efficiency_drop_pct', 0)
    
    if conversion_drop > 10:
        evidence.append(f"conversion_drop_{conversion_drop:.1f}pct")
    
    if abs(spend_change) < 10:
        evidence.append("spend_stable")
    elif spend_change < -10:
        evidence.append(f"spend_decreased_{abs(spend_change):.1f}pct")
    
    if efficiency_drop > 20:
        evidence.append(f"efficiency_drop_{efficiency_drop:.1f}pct")
    
    if analysis.get('has_paused_campaigns'):
        evidence.append("campaigns_paused")
    
    evidence.append("data_source_mcp")
    
    return evidence