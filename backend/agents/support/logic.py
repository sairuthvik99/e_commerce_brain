"""
Support Agent Analysis Logic

Analyzes ticket volume, categories, and sentiment.
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


def calculate_ticket_spike(support_data: Dict) -> float:
    """
    Calculate ticket volume spike percentage.
    
    Returns:
        Spike percentage
    """
    yesterday = support_data.get('yesterday_tickets', 0)
    average = support_data.get('avg_tickets', 1)
    
    if average == 0:
        return 0.0
    
    spike_pct = ((yesterday - average) / average) * 100
    
    logger.info(f"[SupportLogic] Ticket spike: {spike_pct:.2f}%")
    return max(0, spike_pct)


def analyze_sentiment(support_data: Dict) -> Dict:
    """
    Analyze sentiment distribution.
    
    Returns:
        Dict with sentiment metrics
    """
    negative_pct = support_data.get('yesterday_negative_pct', 0)
    negative_count = support_data.get('yesterday_negative_count', 0)
    
    return {
        'negative_pct': negative_pct,
        'negative_count': negative_count,
        'is_high_negative': negative_pct > 50
    }


def analyze_top_categories(support_data: Dict) -> Tuple[str, int, float]:
    """
    Identify top complaint category.
    
    Returns:
        Tuple of (category_name, count, percentage)
    """
    categories = support_data.get('top_categories', [])
    
    if not categories:
        return ("unknown", 0, 0.0)
    
    top_category, top_count = categories[0]
    total_tickets = support_data.get('yesterday_tickets', 1)
    
    percentage = (top_count / total_tickets * 100) if total_tickets > 0 else 0
    
    logger.info(f"[SupportLogic] Top category: {top_category} ({percentage:.1f}%)")
    return (top_category, top_count, percentage)


def calculate_confidence(spike_pct: float, negative_pct: float, top_category_pct: float) -> float:
    """
    Calculate confidence based on ticket metrics.
    
    Returns:
        Confidence score (0.0 to 1.0)
    """
    # Base confidence on spike magnitude
    if spike_pct >= 300:
        base_confidence = 0.92
    elif spike_pct >= 200:
        base_confidence = 0.88
    elif spike_pct >= 100:
        base_confidence = 0.83
    elif spike_pct >= 50:
        base_confidence = 0.75
    else:
        base_confidence = 0.65
    
    # Boost if high negative sentiment
    if negative_pct > 60:
        base_confidence = min(0.95, base_confidence + 0.05)
    
    # Boost if concentrated in one category
    if top_category_pct > 50:
        base_confidence = min(0.95, base_confidence + 0.03)
    
    logger.info(f"[SupportLogic] Confidence: {base_confidence:.2%}")
    return base_confidence


def build_evidence(support_data: Dict, analysis: Dict) -> List[str]:
    """
    Build evidence list.
    
    Returns:
        List of evidence strings
    """
    evidence = []
    
    spike_pct = analysis.get('ticket_spike_pct', 0)
    negative_pct = analysis.get('negative_pct', 0)
    top_category = analysis.get('top_category', 'unknown')
    top_category_pct = analysis.get('top_category_pct', 0)
    
    if spike_pct > 50:
        evidence.append(f"ticket_spike_{spike_pct:.0f}pct")
    
    if negative_pct > 50:
        evidence.append(f"negative_sentiment_{negative_pct:.0f}pct")
    
    if top_category_pct > 40:
        evidence.append(f"concentrated_{top_category}_{top_category_pct:.0f}pct")
    
    evidence.append("data_source_mcp")
    
    return evidence