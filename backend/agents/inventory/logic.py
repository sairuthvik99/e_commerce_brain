"""
Inventory Agent Analysis Logic

Analyzes stockout events and inventory levels.
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def calculate_stockout_severity(inventory_data: Dict, baseline: Dict) -> float:
    """
    Calculate stockout severity compared to baseline.
    
    Returns:
        Severity multiplier (how much worse than normal)
    """
    current_stockouts = inventory_data.get('total_stockouts', 0)
    avg_stockouts = baseline.get('avg_daily_stockouts', 0.1)  # Avoid division by zero
    
    if avg_stockouts == 0:
        return current_stockouts if current_stockouts > 0 else 0
    
    severity = current_stockouts / avg_stockouts
    
    logger.info(f"[InventoryLogic] Stockout severity: {severity:.2f}x baseline")
    return severity


def identify_critical_products(inventory_data: Dict) -> List[int]:
    """
    Identify critical products (assumed to be low product_ids = high demand).
    
    Returns:
        List of critical product IDs
    """
    stockout_products = inventory_data.get('stockout_products', [])
    
    # Simple heuristic: products 1-5 are "critical"
    critical = [p for p in stockout_products if p <= 5]
    
    logger.info(f"[InventoryLogic] Critical products affected: {len(critical)}")
    return critical


def calculate_confidence(severity: float, critical_count: int, total_stockouts: int) -> float:
    """
    Calculate confidence based on severity and impact.
    
    Returns:
        Confidence score (0.0 to 1.0)
    """
    # Base confidence on severity
    if severity >= 5:
        base_confidence = 0.95
    elif severity >= 3:
        base_confidence = 0.90
    elif severity >= 2:
        base_confidence = 0.85
    elif severity >= 1.5:
        base_confidence = 0.75
    else:
        base_confidence = 0.65
    
    # Boost if critical products affected
    if critical_count > 0:
        base_confidence = min(0.98, base_confidence + 0.05)
    
    # Boost if many stockouts
    if total_stockouts >= 10:
        base_confidence = min(0.98, base_confidence + 0.03)
    
    logger.info(f"[InventoryLogic] Confidence: {base_confidence:.2%}")
    return base_confidence


def build_evidence(inventory_data: Dict, analysis: Dict) -> List[str]:
    """
    Build evidence list.
    
    Returns:
        List of evidence strings
    """
    evidence = []
    
    total_stockouts = inventory_data.get('total_stockouts', 0)
    critical_count = len(analysis.get('critical_products', []))
    severity = analysis.get('severity', 0)
    
    evidence.append(f"stockout_count_{total_stockouts}")
    
    if critical_count > 0:
        evidence.append(f"critical_products_affected_{critical_count}")
    
    if severity >= 2:
        evidence.append(f"severity_{severity:.1f}x_baseline")
    
    evidence.append("data_source_mcp")
    
    return evidence