"""
Marketing Agent Implementation

Analyzes campaign performance and conversion trends.
"""

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent, AgentContext, AnalysisResult
from backend.agents.marketing.logic import (
    calculate_conversion_drop,
    calculate_spend_change,
    calculate_efficiency,
    analyze_campaign_status,
    calculate_confidence,
    build_evidence
)
import logging

logger = logging.getLogger(__name__)


class MarketingAgent(BaseAgent):
    """
    Marketing domain agent.
    
    Analyzes:
    - Campaign conversion rates
    - Ad spend trends
    - Marketing efficiency (conversions per dollar)
    - Campaign status (active vs paused)
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_name="marketing", **kwargs)
    
    def load_data(self, context: AgentContext) -> Dict[str, Any]:
        """
        Load marketing data from MCP server.
        
        Returns:
            Dict with campaign performance metrics
        """
        logger.info("[MarketingAgent] Loading data via MCP...")
        
        try:
            marketing_data = self.data_loader.load_marketing_data(days=7)
            
            logger.info(
                f"[MarketingAgent] Loaded: "
                f"{marketing_data['yesterday_conversions']} conversions vs "
                f"{marketing_data['avg_conversions']:.1f} avg"
            )
            
            return marketing_data
        
        except Exception as e:
            logger.error(f"[MarketingAgent] Data loading failed: {e}")
            raise
    
    def analyze(self, data: Dict[str, Any], context: AgentContext) -> AnalysisResult:
        """
        Analyze marketing data.
        
        Calculates:
        - Conversion drop %
        - Spend change %
        - Efficiency metrics
        - Campaign status
        - Confidence score
        """
        logger.info("[MarketingAgent] Analyzing data...")
        
        # Calculate metrics
        conversion_drop = calculate_conversion_drop(data)
        spend_change = calculate_spend_change(data)
        efficiency_metrics = calculate_efficiency(data)
        campaign_status = analyze_campaign_status(data)
        
        # Calculate confidence
        confidence = calculate_confidence(
            conversion_drop=conversion_drop,
            spend_change=spend_change,
            efficiency_drop=efficiency_metrics['efficiency_drop_pct']
        )
        
        # Prepare metrics dict
        metrics = {
            'conversion_drop_pct': conversion_drop,
            'spend_change_pct': spend_change,
            'efficiency_drop_pct': efficiency_metrics['efficiency_drop_pct'],
            'yesterday_conversions': data['yesterday_conversions'],
            'avg_conversions': data['avg_conversions'],
            'yesterday_spend': data['yesterday_spend'],
            'avg_spend': data['avg_spend'],
            'active_campaigns': campaign_status['active_campaigns'],
            'has_paused_campaigns': campaign_status['has_paused_campaigns']
        }
        
        # Build evidence
        evidence = build_evidence(data, metrics)
        
        logger.info(
            f"[MarketingAgent] Analysis complete: "
            f"Conversions drop {conversion_drop:.1f}%, "
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
            "Campaign conversions dropped {conversion_drop_pct:.1f}% yesterday "
            "with {active_campaigns} active campaigns"
        )
    
    def get_tool_description(self) -> str:
        """LangChain tool description."""
        return (
            "Analyzes marketing campaign performance including conversions, "
            "spend, and efficiency. Identifies underperforming campaigns."
        )