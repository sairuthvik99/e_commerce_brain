"""
Reusable database query functions.

Provides high-level query abstractions for agents.
All queries use SQLAlchemy ORM.
"""

from sqlalchemy import func, and_, desc, Integer
from backend.database.connection import session_scope
from backend.database.models import (
    Orders, OrderItems, InventorySnapshots, MarketingCampaignsDaily,
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


def get_top_selling_products(days: int = 7, top_n: int = 5) -> Dict:
    """
    Get top selling products by quantity and revenue.
    
    Args:
        days: Number of days to analyze (default 7)
        top_n: Number of top products to return (default 5)
    
    Returns:
        {
            'period_start': date,
            'period_end': date,
            'top_by_quantity': [
                {'product_id': int, 'total_quantity': int, 'total_revenue': float, 'order_count': int},
                ...
            ],
            'top_by_revenue': [
                {'product_id': int, 'total_quantity': int, 'total_revenue': float, 'order_count': int},
                ...
            ]
        }
    """
    try:
        start_date, end_date = get_date_range(days)
        
        with session_scope() as session:
            # Get top products by quantity sold
            top_by_quantity = session.query(
                OrderItems.product_id,
                func.sum(OrderItems.quantity).label('total_quantity'),
                func.sum(OrderItems.item_total).label('total_revenue'),
                func.count(func.distinct(OrderItems.order_id)).label('order_count')
            ).join(
                Orders, Orders.order_id == OrderItems.order_id
            ).filter(
                and_(
                    Orders.created_date >= start_date,
                    Orders.created_date <= end_date
                )
            ).group_by(
                OrderItems.product_id
            ).order_by(
                desc('total_quantity')
            ).limit(top_n).all()
            
            # Get top products by revenue
            top_by_revenue = session.query(
                OrderItems.product_id,
                func.sum(OrderItems.quantity).label('total_quantity'),
                func.sum(OrderItems.item_total).label('total_revenue'),
                func.count(func.distinct(OrderItems.order_id)).label('order_count')
            ).join(
                Orders, Orders.order_id == OrderItems.order_id
            ).filter(
                and_(
                    Orders.created_date >= start_date,
                    Orders.created_date <= end_date
                )
            ).group_by(
                OrderItems.product_id
            ).order_by(
                desc('total_revenue')
            ).limit(top_n).all()
            
            result = {
                'period_start': start_date,
                'period_end': end_date,
                'top_by_quantity': [
                    {
                        'product_id': p.product_id,
                        'total_quantity': p.total_quantity or 0,
                        'total_revenue': float(p.total_revenue or 0),
                        'order_count': p.order_count or 0
                    }
                    for p in top_by_quantity
                ],
                'top_by_revenue': [
                    {
                        'product_id': p.product_id,
                        'total_quantity': p.total_quantity or 0,
                        'total_revenue': float(p.total_revenue or 0),
                        'order_count': p.order_count or 0
                    }
                    for p in top_by_revenue
                ]
            }
            
            logger.info(f"[Queries] Top selling products: {len(result['top_by_quantity'])} products returned")
            return result
    
    except Exception as e:
        logger.error(f"[Queries] Failed to get top selling products: {e}")
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


def get_campaign_channels(days: int = 7) -> Dict:
    """
    Get marketing campaign channels and their performance.
    
    Returns:
        {
            'period_start': date,
            'period_end': date,
            'channels': [
                {
                    'channel': str,
                    'total_impressions': int,
                    'total_clicks': int,
                    'total_spend': float,
                    'total_conversions': int,
                    'campaign_count': int
                },
                ...
            ],
            'channel_list': [str, ...]  # Just the channel names
        }
    """
    try:
        start_date, end_date = get_date_range(days)
        
        with session_scope() as session:
            # Get channel-level aggregated metrics
            channel_data = session.query(
                MarketingCampaignsDaily.channel,
                func.sum(MarketingCampaignsDaily.impressions).label('total_impressions'),
                func.sum(MarketingCampaignsDaily.clicks).label('total_clicks'),
                func.sum(MarketingCampaignsDaily.spend).label('total_spend'),
                func.sum(MarketingCampaignsDaily.conversions).label('total_conversions'),
                func.count(func.distinct(MarketingCampaignsDaily.campaign_id)).label('campaign_count')
            ).filter(
                and_(
                    MarketingCampaignsDaily.date >= start_date,
                    MarketingCampaignsDaily.date <= end_date
                )
            ).group_by(MarketingCampaignsDaily.channel).order_by(desc('total_conversions')).all()
            
            if not channel_data:
                logger.warning("[Queries] No marketing channel data found")
                return {
                    'period_start': start_date,
                    'period_end': end_date,
                    'channels': [],
                    'channel_list': []
                }
            
            result = {
                'period_start': start_date,
                'period_end': end_date,
                'channels': [
                    {
                        'channel': c.channel or 'Unknown',
                        'total_impressions': c.total_impressions or 0,
                        'total_clicks': c.total_clicks or 0,
                        'total_spend': float(c.total_spend or 0),
                        'total_conversions': c.total_conversions or 0,
                        'campaign_count': c.campaign_count or 0
                    }
                    for c in channel_data
                ],
                'channel_list': [c.channel or 'Unknown' for c in channel_data]
            }
            
            logger.info(f"[Queries] Marketing channels: {len(result['channels'])} channels found - {result['channel_list']}")
            return result
    
    except Exception as e:
        logger.error(f"[Queries] Failed to get campaign channels: {e}")
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


# ==================== INVENTORY DATA RETRIEVAL ====================

def get_all_products_inventory() -> Dict:
    """
    Get all products with their current inventory status.
    
    Returns:
        {
            'total_products': int,
            'products': [
                {
                    'product_id': int,
                    'available_stock': int,
                    'stock_threshold': int,
                    'is_out_of_stock': bool,
                    'out_of_stock_since': datetime or None,
                    'snapshot_timestamp': datetime
                },
                ...
            ],
            'summary': {
                'in_stock_count': int,
                'out_of_stock_count': int,
                'low_stock_count': int
            }
        }
    """
    try:
        with session_scope() as session:
            # Get the most recent snapshot for each product
            # Using subquery to get latest timestamp per product
            from sqlalchemy import func
            from sqlalchemy.orm import aliased
            
            # Subquery to get max timestamp for each product
            subq = session.query(
                InventorySnapshots.product_id,
                func.max(InventorySnapshots.snapshot_timestamp).label('max_ts')
            ).group_by(InventorySnapshots.product_id).subquery()
            
            # Get the full records matching the latest timestamp
            products = session.query(InventorySnapshots).join(
                subq,
                and_(
                    InventorySnapshots.product_id == subq.c.product_id,
                    InventorySnapshots.snapshot_timestamp == subq.c.max_ts
                )
            ).order_by(InventorySnapshots.product_id).all()
            
            # Calculate summary
            in_stock = [p for p in products if not p.is_out_of_stock]
            out_of_stock = [p for p in products if p.is_out_of_stock]
            low_stock = [p for p in products if p.available_stock <= (p.stock_threshold or 10) and not p.is_out_of_stock]
            
            result = {
                'total_products': len(products),
                'products': [
                    {
                        'product_id': p.product_id,
                        'available_stock': p.available_stock,
                        'stock_threshold': p.stock_threshold,
                        'is_out_of_stock': p.is_out_of_stock,
                        'out_of_stock_since': p.out_of_stock_since,
                        'snapshot_timestamp': p.snapshot_timestamp
                    }
                    for p in products
                ],
                'summary': {
                    'in_stock_count': len(in_stock),
                    'out_of_stock_count': len(out_of_stock),
                    'low_stock_count': len(low_stock)
                }
            }
            
            logger.info(f"[Queries] Retrieved {len(products)} products inventory data")
            return result
    
    except Exception as e:
        logger.error(f"[Queries] Failed to get all products inventory: {e}")
        raise


def get_product_inventory(product_id: int) -> Dict:
    """
    Get inventory details for a specific product.
    
    Args:
        product_id: The product ID to look up
    
    Returns:
        {
            'product_id': int,
            'available_stock': int,
            'stock_threshold': int,
            'is_out_of_stock': bool,
            'out_of_stock_since': datetime or None,
            'snapshot_timestamp': datetime,
            'found': bool
        }
    """
    try:
        with session_scope() as session:
            # Get the most recent snapshot for this product
            product = session.query(InventorySnapshots).filter(
                InventorySnapshots.product_id == product_id
            ).order_by(desc(InventorySnapshots.snapshot_timestamp)).first()
            
            if not product:
                return {
                    'product_id': product_id,
                    'found': False,
                    'error': f'Product {product_id} not found in inventory'
                }
            
            result = {
                'product_id': product.product_id,
                'available_stock': product.available_stock,
                'stock_threshold': product.stock_threshold,
                'is_out_of_stock': product.is_out_of_stock,
                'out_of_stock_since': product.out_of_stock_since,
                'snapshot_timestamp': product.snapshot_timestamp,
                'found': True
            }
            
            logger.info(f"[Queries] Product {product_id} stock: {result['available_stock']}")
            return result
    
    except Exception as e:
        logger.error(f"[Queries] Failed to get product {product_id} inventory: {e}")
        raise


def update_product_stock(product_id: int, quantity_change: int, reason: str = None) -> Dict:
    """
    Update stock level for a product.
    
    Args:
        product_id: The product ID to update
        quantity_change: Amount to add (positive) or remove (negative)
        reason: Optional reason for the update
    
    Returns:
        {
            'product_id': int,
            'previous_stock': int,
            'new_stock': int,
            'quantity_change': int,
            'is_out_of_stock': bool,
            'success': bool,
            'message': str
        }
    """
    try:
        with session_scope() as session:
            # Get current stock level
            current = session.query(InventorySnapshots).filter(
                InventorySnapshots.product_id == product_id
            ).order_by(desc(InventorySnapshots.snapshot_timestamp)).first()
            
            if not current:
                return {
                    'product_id': product_id,
                    'success': False,
                    'message': f'Product {product_id} not found in inventory'
                }
            
            previous_stock = current.available_stock
            new_stock = max(0, previous_stock + quantity_change)  # Don't allow negative stock
            
            # Create new snapshot with updated stock
            from datetime import datetime
            new_snapshot = InventorySnapshots(
                product_id=product_id,
                snapshot_timestamp=datetime.utcnow(),
                available_stock=new_stock,
                stock_threshold=current.stock_threshold,
                is_out_of_stock=(new_stock == 0),
                out_of_stock_since=datetime.utcnow() if new_stock == 0 and previous_stock > 0 else current.out_of_stock_since
            )
            
            session.add(new_snapshot)
            session.flush()  # Ensure the insert happens
            
            result = {
                'product_id': product_id,
                'previous_stock': previous_stock,
                'new_stock': new_stock,
                'quantity_change': quantity_change,
                'is_out_of_stock': new_stock == 0,
                'success': True,
                'message': f'Stock updated from {previous_stock} to {new_stock}',
                'reason': reason
            }
            
            logger.info(f"[Queries] Updated product {product_id} stock: {previous_stock} -> {new_stock}")
            return result
    
    except Exception as e:
        logger.error(f"[Queries] Failed to update product {product_id} stock: {e}")
        raise


def search_products_by_name(search_term: str) -> Dict:
    """
    Search for products by name/id.
    Since we don't have product names in the schema, this searches by product_id.
    
    Args:
        search_term: Search term (will try to match as product_id)
    
    Returns:
        {
            'search_term': str,
            'products': [...],
            'total_matches': int
        }
    """
    try:
        with session_scope() as session:
            # Try to parse as integer for product_id search
            try:
                product_id = int(search_term)
                # Search by exact product_id
                products = session.query(InventorySnapshots).filter(
                    InventorySnapshots.product_id == product_id
                ).order_by(desc(InventorySnapshots.snapshot_timestamp)).limit(1).all()
            except ValueError:
                # Not a number, return empty (we don't have product names in this schema)
                products = []
            
            result = {
                'search_term': search_term,
                'products': [
                    {
                        'product_id': p.product_id,
                        'available_stock': p.available_stock,
                        'stock_threshold': p.stock_threshold,
                        'is_out_of_stock': p.is_out_of_stock
                    }
                    for p in products
                ],
                'total_matches': len(products)
            }
            
            logger.info(f"[Queries] Product search for '{search_term}': {len(products)} matches")
            return result
    
    except Exception as e:
        logger.error(f"[Queries] Failed to search products: {e}")
        raise