"""
Reusable database query functions.

Provides high-level query abstractions for agents.
All queries use SQLAlchemy ORM.
"""

from sqlalchemy import func, and_, desc
from backend.database.connection import session_scope
from backend.database.models import (
    Orders, InventorySnapshots, MarketingCampaignsDaily,
    SupportTickets, DailyMetrics
)
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


# ==================== UTILITY FUNCTIONS ====================

def get_most_recent_date() -> date:
    """
    Get the most recent date in the daily_metrics table.
    This represents "yesterday" in our analysis.
    
    Returns:
        Most recent date as date object
    """
    try:
        with session_scope() as session:
            result = session.query(func.max(DailyMetrics.date)).scalar()
            
            if result is None:
                logger.warning("[Queries] No data in daily_metrics table")
                return datetime.today().date()
            
            logger.info(f"[Queries] Most recent date: {result}")
            return result
    
    except Exception as e:
        logger.error(f"[Queries] Failed to get most recent date: {e}")
        raise


def get_date_range(days: int = 7) -> tuple:
    """
    Get date range for analysis (yesterday and N days before).
    
    Args:
        days: Number of days to look back (default 7)
    
    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = get_most_recent_date()
    start_date = end_date - timedelta(days=days - 1)
    return start_date, end_date


# ==================== SALES QUERIES ====================

def get_daily_sales_metrics(days: int = 7) -> Dict:
    """
    Get daily sales metrics for the last N days.
    
    Returns:
        {
            'yesterday_revenue': float,
            'yesterday_orders': int,
            'yesterday_aov': float,
            'avg_revenue': float,
            'avg_orders': float,
            'avg_aov': float,
            'daily_breakdown': [...]
        }
    """
    try:
        start_date, end_date = get_date_range(days)
        
        with session_scope() as session:
            # Get daily metrics
            metrics = session.query(DailyMetrics).filter(
                and_(
                    DailyMetrics.date >= start_date,
                    DailyMetrics.date <= end_date
                )
            ).order_by(DailyMetrics.date).all()
            
            if not metrics:
                logger.warning("[Queries] No sales metrics found")
                return {}
            
            # Yesterday (most recent)
            yesterday = metrics[-1]
            
            # Calculate averages (excluding yesterday)
            historical = metrics[:-1] if len(metrics) > 1 else metrics
            
            avg_revenue = sum(float(m.total_revenue or 0) for m in historical) / len(historical)
            avg_orders = sum(m.total_orders or 0 for m in historical) / len(historical)
            avg_aov = sum(float(m.avg_order_value or 0) for m in historical) / len(historical)
            
            result = {
                'yesterday_date': yesterday.date,
                'yesterday_revenue': float(yesterday.total_revenue or 0),
                'yesterday_orders': yesterday.total_orders or 0,
                'yesterday_aov': float(yesterday.avg_order_value or 0),
                'avg_revenue': avg_revenue,
                'avg_orders': avg_orders,
                'avg_aov': avg_aov,
                'daily_breakdown': [
                    {
                        'date': m.date,
                        'revenue': float(m.total_revenue or 0),
                        'orders': m.total_orders or 0,
                        'aov': float(m.avg_order_value or 0)
                    }
                    for m in metrics
                ]
            }
            
            logger.info(f"[Queries] Sales metrics: {result['yesterday_revenue']:.2f} vs {result['avg_revenue']:.2f}")
            return result
    
    except Exception as e:
        logger.error(f"[Queries] Failed to get sales metrics: {e}")
        raise


# ==================== INVENTORY QUERIES ====================

def get_stockout_events(target_date: Optional[date] = None) -> Dict:
    """
    Get stockout events for a specific date.
    
    Args:
        target_date: Date to analyze (defaults to most recent)
    
    Returns:
        {
            'date': date,
            'total_stockouts': int,
            'stockout_products': [product_id, ...],
            'stockout_details': [...]
        }
    """
    try:
        if target_date is None:
            target_date = get_most_recent_date()
        
        with session_scope() as session:
            # Get stockouts for the target date
            stockouts = session.query(InventorySnapshots).filter(
                and_(
                    func.date(InventorySnapshots.snapshot_timestamp) == target_date,
                    InventorySnapshots.is_out_of_stock == True
                )
            ).all()
            
            result = {
                'date': target_date,
                'total_stockouts': len(stockouts),
                'stockout_products': [s.product_id for s in stockouts],
                'stockout_details': [
                    {
                        'product_id': s.product_id,
                        'out_of_stock_since': s.out_of_stock_since,
                        'stock_level': s.available_stock
                    }
                    for s in stockouts
                ]
            }
            
            logger.info(f"[Queries] Stockouts on {target_date}: {result['total_stockouts']} products")
            return result
    
    except Exception as e:
        logger.error(f"[Queries] Failed to get stockout events: {e}")
        raise


def get_inventory_baseline(days: int = 7) -> Dict:
    """
    Get baseline stockout metrics for comparison.
    
    Returns:
        {
            'avg_daily_stockouts': float,
            'total_days': int
        }
    """
    try:
        start_date, end_date = get_date_range(days)
        
        with session_scope() as session:
            # Get stockout counts per day
            daily_stockouts = session.query(
                func.date(InventorySnapshots.snapshot_timestamp).label('date'),
                func.count(InventorySnapshots.snapshot_id).label('count')
            ).filter(
                and_(
                    func.date(InventorySnapshots.snapshot_timestamp) >= start_date,
                    func.date(InventorySnapshots.snapshot_timestamp) < end_date,  # Exclude yesterday
                    InventorySnapshots.is_out_of_stock == True
                )
            ).group_by('date').all()
            
            avg_stockouts = sum(d.count for d in daily_stockouts) / len(daily_stockouts) if daily_stockouts else 0
            
            return {
                'avg_daily_stockouts': avg_stockouts,
                'total_days': len(daily_stockouts)
            }
    
    except Exception as e:
        logger.error(f"[Queries] Failed to get inventory baseline: {e}")
        raise


# ==================== MARKETING QUERIES ====================

def get_campaign_performance(days: int = 7) -> Dict:
    """
    Get marketing campaign performance metrics.
    
    Returns:
        {
            'yesterday_conversions': int,
            'yesterday_spend': float,
            'yesterday_active_campaigns': int,
            'avg_conversions': float,
            'avg_spend': float,
            'daily_breakdown': [...]
        }
    """
    try:
        start_date, end_date = get_date_range(days)
        
        with session_scope() as session:
            # Get daily aggregated metrics
            daily_data = session.query(
                MarketingCampaignsDaily.date,
                func.sum(MarketingCampaignsDaily.conversions).label('total_conversions'),
                func.sum(MarketingCampaignsDaily.spend).label('total_spend'),
                func.count(MarketingCampaignsDaily.campaign_id).label('campaign_count'),
                func.sum(
                    func.cast(MarketingCampaignsDaily.campaign_status == 'active', Integer)
                ).label('active_campaigns')
            ).filter(
                and_(
                    MarketingCampaignsDaily.date >= start_date,
                    MarketingCampaignsDaily.date <= end_date
                )
            ).group_by(MarketingCampaignsDaily.date).order_by(MarketingCampaignsDaily.date).all()
            
            if not daily_data:
                logger.warning("[Queries] No marketing data found")
                return {}
            
            # Yesterday (most recent)
            yesterday = daily_data[-1]
            
            # Historical average
            historical = daily_data[:-1] if len(daily_data) > 1 else daily_data
            avg_conversions = sum(d.total_conversions or 0 for d in historical) / len(historical)
            avg_spend = sum(float(d.total_spend or 0) for d in historical) / len(historical)
            
            result = {
                'yesterday_date': yesterday.date,
                'yesterday_conversions': yesterday.total_conversions or 0,
                'yesterday_spend': float(yesterday.total_spend or 0),
                'yesterday_active_campaigns': yesterday.active_campaigns or 0,
                'avg_conversions': avg_conversions,
                'avg_spend': avg_spend,
                'daily_breakdown': [
                    {
                        'date': d.date,
                        'conversions': d.total_conversions or 0,
                        'spend': float(d.total_spend or 0),
                        'active_campaigns': d.active_campaigns or 0
                    }
                    for d in daily_data
                ]
            }
            
            logger.info(f"[Queries] Marketing: {result['yesterday_conversions']} conversions vs {result['avg_conversions']:.1f} avg")
            return result
    
    except Exception as e:
        logger.error(f"[Queries] Failed to get campaign performance: {e}")
        raise


# ==================== SUPPORT QUERIES ====================

def get_ticket_volume(days: int = 7) -> Dict:
    """
    Get support ticket volume and categories.
    
    Returns:
        {
            'yesterday_tickets': int,
            'yesterday_negative_pct': float,
            'avg_tickets': float,
            'top_categories': [...],
            'daily_breakdown': [...]
        }
    """
    try:
        start_date, end_date = get_date_range(days)
        end_datetime = datetime.combine(end_date, datetime.max.time())
        start_datetime = datetime.combine(start_date, datetime.min.time())
        
        with session_scope() as session:
            # Get yesterday's tickets
            yesterday_start = datetime.combine(end_date, datetime.min.time())
            yesterday_tickets = session.query(SupportTickets).filter(
                and_(
                    SupportTickets.created_timestamp >= yesterday_start,
                    SupportTickets.created_timestamp <= end_datetime
                )
            ).all()
            
            # Get historical tickets (for baseline)
            historical_tickets = session.query(
                func.date(SupportTickets.created_timestamp).label('date'),
                func.count(SupportTickets.ticket_id).label('count')
            ).filter(
                and_(
                    SupportTickets.created_timestamp >= start_datetime,
                    SupportTickets.created_timestamp < yesterday_start
                )
            ).group_by('date').all()
            
            # Calculate metrics
            yesterday_count = len(yesterday_tickets)
            yesterday_negative = len([t for t in yesterday_tickets if t.sentiment == 'negative'])
            yesterday_negative_pct = (yesterday_negative / yesterday_count * 100) if yesterday_count > 0 else 0
            
            avg_tickets = sum(h.count for h in historical_tickets) / len(historical_tickets) if historical_tickets else 0
            
            # Category breakdown for yesterday
            categories = {}
            for ticket in yesterday_tickets:
                cat = ticket.issue_category or 'unknown'
                categories[cat] = categories.get(cat, 0) + 1
            
            result = {
                'yesterday_date': end_date,
                'yesterday_tickets': yesterday_count,
                'yesterday_negative_count': yesterday_negative,
                'yesterday_negative_pct': yesterday_negative_pct,
                'avg_tickets': avg_tickets,
                'top_categories': sorted(categories.items(), key=lambda x: x[1], reverse=True),
                'daily_breakdown': [
                    {
                        'date': h.date,
                        'count': h.count
                    }
                    for h in historical_tickets
                ] + [{'date': end_date, 'count': yesterday_count}]
            }
            
            logger.info(f"[Queries] Support: {result['yesterday_tickets']} tickets vs {result['avg_tickets']:.1f} avg")
            return result
    
    except Exception as e:
        logger.error(f"[Queries] Failed to get ticket volume: {e}")
        raise