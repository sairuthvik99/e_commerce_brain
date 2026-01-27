"""
Sales Agent Implementation

Analyzes revenue, orders, and AOV trends.
"""

from typing import Dict, Any
from ..base_agent import BaseAgent, AgentContext, AnalysisResult
from .logic import (
    calculate_revenue_drop,
    calculate_order_drop,
    calculate_aov_drop,
    analyze_drop_cause,
    calculate_confidence,
    build_evidence
)
import logging

logger = logging.getLogger(__name__)


class SalesAgent(BaseAgent):
    """
    Sales domain agent.
    
    Analyzes:
    - Revenue trends (yesterday vs 7-day average)
    - Order count trends
    - Average order value (AOV)
    - Root cause of sales drops
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_name="sales", **kwargs)
    
    def load_data(self, context: AgentContext) -> Dict[str, Any]:
        """
        Load sales metrics from MCP server.
        
        Returns:
            Dict with yesterday/average revenue, orders, AOV
        """
        logger.info("[SalesAgent] Loading data via MCP...")
        
        try:
            sales_data = self.data_loader.load_sales_data(days=7)
            
            logger.info(
                f"[SalesAgent] Loaded: "
                f"Revenue ${sales_data['yesterday_revenue']:.2f} vs "
                f"${sales_data['avg_revenue']:.2f} avg"
            )
            
            return sales_data
        
        except Exception as e:
            logger.error(f"[SalesAgent] Data loading failed: {e}")
            raise
    
    def analyze(self, data: Dict[str, Any], context: AgentContext) -> AnalysisResult:
        """
        Analyze sales data.
        
        Calculates:
        - Revenue drop %
        - Order count drop %
        - AOV drop %
        - Primary cause (orders vs AOV)
        - Confidence score
        """
        logger.info("[SalesAgent] Analyzing data...")
        
        # Calculate metrics
        revenue_drop = calculate_revenue_drop(data)
        order_drop = calculate_order_drop(data)
        aov_drop = calculate_aov_drop(data)
        drop_cause = analyze_drop_cause(data)
        
        # Calculate confidence
        confidence = calculate_confidence(revenue_drop, order_drop, aov_drop)
        
        # Prepare metrics dict
        metrics = {
            'revenue_drop_pct': revenue_drop,
            'order_drop_pct': order_drop,
            'aov_drop_pct': aov_drop,
            'drop_cause': drop_cause,
            'yesterday_revenue': data['yesterday_revenue'],
            'avg_revenue': data['avg_revenue'],
            'yesterday_orders': data['yesterday_orders'],
            'avg_orders': data['avg_orders']
        }
        
        # Build evidence
        evidence = build_evidence(data, metrics)
        
        logger.info(
            f"[SalesAgent] Analysis complete: "
            f"Revenue drop {revenue_drop:.1f}%, "
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
            "Sales dropped {revenue_drop_pct:.1f}% yesterday "
            "with {drop_cause} as primary cause"
        )
    
    def get_tool_description(self) -> str:
        """LangChain tool description."""
        return (
            "Analyzes sales performance including revenue, order count, "
            "and average order value. Identifies drops and trends compared "
            "to 7-day baseline."
        )