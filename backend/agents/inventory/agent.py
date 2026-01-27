"""
Inventory Agent Implementation

Analyzes stockout events and inventory levels.
"""

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent, AgentContext, AnalysisResult
from backend.agents.inventory.logic import (
    calculate_stockout_severity,
    identify_critical_products,
    calculate_confidence,
    build_evidence
)
import logging

logger = logging.getLogger(__name__)


class InventoryAgent(BaseAgent):
    """
    Inventory domain agent.
    
    Analyzes:
    - Stockout events (count, products affected)
    - Severity compared to baseline
    - Critical product impact
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_name="inventory", **kwargs)
    
    def load_data(self, context: AgentContext) -> Dict[str, Any]:
        """
        Load inventory data from MCP server.
        
        Returns:
            Dict with stockout events and baseline
        """
        logger.info("[InventoryAgent] Loading data via MCP...")
        
        try:
            # Get yesterday's stockouts
            stockouts = self.data_loader.load_inventory_data()
            
            # Get baseline for comparison
            baseline = self.data_loader.load_inventory_baseline(days=7)
            
            # Combine data
            data = {
                **stockouts,
                'baseline': baseline
            }
            
            logger.info(
                f"[InventoryAgent] Loaded: "
                f"{stockouts['total_stockouts']} stockouts vs "
                f"{baseline['avg_daily_stockouts']:.1f} avg"
            )
            
            return data
        
        except Exception as e:
            logger.error(f"[InventoryAgent] Data loading failed: {e}")
            raise
    
    def analyze(self, data: Dict[str, Any], context: AgentContext) -> AnalysisResult:
        """
        Analyze inventory data.
        
        Calculates:
        - Stockout severity vs baseline
        - Critical products affected
        - Confidence score
        """
        logger.info("[InventoryAgent] Analyzing data...")
        
        baseline = data.get('baseline', {})
        
        # Calculate metrics
        severity = calculate_stockout_severity(data, baseline)
        critical_products = identify_critical_products(data)
        
        total_stockouts = data.get('total_stockouts', 0)
        
        # Calculate confidence
        confidence = calculate_confidence(
            severity=severity,
            critical_count=len(critical_products),
            total_stockouts=total_stockouts
        )
        
        # Prepare metrics dict
        metrics = {
            'total_stockouts': total_stockouts,
            'avg_stockouts': baseline.get('avg_daily_stockouts', 0),
            'severity': severity,
            'critical_products': critical_products,
            'critical_count': len(critical_products)
        }
        
        # Build evidence
        evidence = build_evidence(data, metrics)
        
        logger.info(
            f"[InventoryAgent] Analysis complete: "
            f"{total_stockouts} stockouts, "
            f"{severity:.1f}x severity, "
            f"Confidence {confidence:.2%}"
        )
        
        return AnalysisResult(
            metrics=metrics,
            evidence=evidence,
            confidence=confidence,
            raw_data=data
        )
    
    def get_fallback_template(self) -> str:
        """Fallback template if LLM formatting fails."""
        return (
            "{total_stockouts} products out of stock "
            "({severity:.1f}x higher than baseline)"
        )
    
    def get_tool_description(self) -> str:
        """LangChain tool description."""
        return (
            "Analyzes inventory stockout events and identifies critical "
            "products affected. Compares to baseline to assess severity."
        )