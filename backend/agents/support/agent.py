"""
Support Agent Implementation

Analyzes ticket volume, sentiment, and categories.
"""

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent, AgentContext, AnalysisResult
from backend.agents.support.logic import (
    calculate_ticket_spike,
    analyze_sentiment,
    analyze_top_categories,
    calculate_confidence,
    build_evidence
)
import logging

logger = logging.getLogger(__name__)


class SupportAgent(BaseAgent):
    """
    Support domain agent.
    
    Analyzes:
    - Ticket volume trends
    - Sentiment distribution
    - Top complaint categories
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_name="support", **kwargs)
    
    def load_data(self, context: AgentContext) -> Dict[str, Any]:
        """
        Load support data from MCP server.
        
        Returns:
            Dict with ticket volume, sentiment, categories
        """
        logger.info("[SupportAgent] Loading data via MCP...")
        
        try:
            support_data = self.data_loader.load_support_data(days=7)
            
            logger.info(
                f"[SupportAgent] Loaded: "
                f"{support_data['yesterday_tickets']} tickets vs "
                f"{support_data['avg_tickets']:.1f} avg"
            )
            
            return support_data
        
        except Exception as e:
            logger.error(f"[SupportAgent] Data loading failed: {e}")
            raise
    
    def analyze(self, data: Dict[str, Any], context: AgentContext) -> AnalysisResult:
        """
        Analyze support data.
        
        Calculates:
        - Ticket spike %
        - Sentiment metrics
        - Top categories
        - Confidence score
        """
        logger.info("[SupportAgent] Analyzing data...")
        
        # Calculate metrics
        ticket_spike = calculate_ticket_spike(data)
        sentiment_metrics = analyze_sentiment(data)
        top_category, top_count, top_pct = analyze_top_categories(data)
        
        # Calculate confidence
        confidence = calculate_confidence(
            spike_pct=ticket_spike,
            negative_pct=sentiment_metrics['negative_pct'],
            top_category_pct=top_pct
        )
        
        # Prepare metrics dict
        metrics = {
            'ticket_spike_pct': ticket_spike,
            'yesterday_tickets': data['yesterday_tickets'],
            'avg_tickets': data['avg_tickets'],
            'negative_pct': sentiment_metrics['negative_pct'],
            'negative_count': sentiment_metrics['negative_count'],
            'top_category': top_category,
            'top_category_count': top_count,
            'top_category_pct': top_pct
        }
        
        # Build evidence
        evidence = build_evidence(data, metrics)
        
        logger.info(
            f"[SupportAgent] Analysis complete: "
            f"Ticket spike {ticket_spike:.0f}%, "
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
            "Support tickets increased {ticket_spike_pct:.0f}% yesterday "
            "({yesterday_tickets} vs {avg_tickets:.1f} avg)"
        )
    
    def get_tool_description(self) -> str:
        """LangChain tool description."""
        return (
            "Analyzes support ticket volume, sentiment distribution, and "
            "complaint categories. Identifies spikes and issues."
        )