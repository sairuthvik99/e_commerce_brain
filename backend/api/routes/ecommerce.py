"""
E-Commerce Data Endpoints

Endpoints for fetching e-commerce data from PostgreSQL database.
"""

from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from backend.database.connection import session_scope
from backend.database.models import (
    Orders, InventorySnapshots, MarketingCampaignsDaily,
    SupportTickets, DailyMetrics
)
from sqlalchemy import func, and_, desc

router = APIRouter()


@router.get(
    "/ecommerce/stats",
    summary="Get E-Commerce Statistics",
    description="Get comprehensive e-commerce statistics from PostgreSQL database",
    responses={
        200: {"description": "E-commerce statistics retrieved successfully"},
        500: {"description": "Database connection error"}
    }
)
async def get_ecommerce_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back")
) -> Dict[str, Any]:
    """
    Get comprehensive e-commerce statistics.
    
    Returns:
        dict: E-commerce statistics including sales, inventory, marketing, support data
    """
    try:
        with session_scope() as session:
            # Get date range
            most_recent = session.query(func.max(DailyMetrics.date)).scalar()
            
            if most_recent is None:
                return {
                    "error": "No data available in database",
                    "summary": {},
                    "daily_metrics": [],
                    "by_status": {},
                    "recent_jobs": [],
                    "agent_stats": {}
                }
            
            start_date = most_recent - timedelta(days=days - 1)
            
            # Get daily metrics
            daily_metrics = session.query(DailyMetrics).filter(
                and_(
                    DailyMetrics.date >= start_date,
                    DailyMetrics.date <= most_recent
                )
            ).order_by(DailyMetrics.date).all()
            
            # Yesterday (most recent)
            yesterday = daily_metrics[-1] if daily_metrics else None
            
            # Calculate totals and averages
            total_revenue = sum(float(m.total_revenue or 0) for m in daily_metrics)
            total_orders = sum(m.total_orders or 0 for m in daily_metrics)
            total_stockouts = sum(m.stockout_sku_count or 0 for m in daily_metrics)
            total_complaints = sum(m.total_complaints or 0 for m in daily_metrics)
            total_marketing_spend = sum(float(m.marketing_spend or 0) for m in daily_metrics)
            total_conversions = sum(m.marketing_conversions or 0 for m in daily_metrics)
            
            # Yesterday's metrics
            yesterday_revenue = float(yesterday.total_revenue or 0) if yesterday else 0
            yesterday_orders = yesterday.total_orders or 0 if yesterday else 0
            yesterday_aov = float(yesterday.avg_order_value or 0) if yesterday else 0
            
            # Average daily values
            num_days = len(daily_metrics) if daily_metrics else 1
            avg_daily_revenue = total_revenue / num_days
            avg_daily_orders = total_orders / num_days
            
            # Support tickets breakdown
            ticket_stats = session.query(
                SupportTickets.issue_category,
                func.count(SupportTickets.ticket_id).label('count')
            ).filter(
                func.date(SupportTickets.created_timestamp) >= start_date
            ).group_by(SupportTickets.issue_category).all()
            
            # Marketing by channel
            channel_stats = session.query(
                MarketingCampaignsDaily.channel,
                func.sum(MarketingCampaignsDaily.spend).label('spend'),
                func.sum(MarketingCampaignsDaily.conversions).label('conversions'),
                func.sum(MarketingCampaignsDaily.clicks).label('clicks')
            ).filter(
                and_(
                    MarketingCampaignsDaily.date >= start_date,
                    MarketingCampaignsDaily.date <= most_recent
                )
            ).group_by(MarketingCampaignsDaily.channel).all()
            
            # Products with stockouts
            stockout_products = session.query(
                func.count(func.distinct(InventorySnapshots.product_id))
            ).filter(
                and_(
                    InventorySnapshots.is_out_of_stock == True,
                    func.date(InventorySnapshots.snapshot_timestamp) >= start_date
                )
            ).scalar() or 0
            
            # Daily breakdown for charts
            daily_breakdown = [
                {
                    "date": m.date.isoformat(),
                    "revenue": float(m.total_revenue or 0),
                    "orders": m.total_orders or 0,
                    "aov": float(m.avg_order_value or 0),
                    "stockouts": m.stockout_sku_count or 0,
                    "complaints": m.total_complaints or 0,
                    "marketing_spend": float(m.marketing_spend or 0),
                    "conversions": m.marketing_conversions or 0
                }
                for m in daily_metrics
            ]
            
            # Jobs by hour (simulated from orders data)
            jobs_by_hour = []
            for i, m in enumerate(daily_metrics[-7:] if len(daily_metrics) >= 7 else daily_metrics):
                jobs_by_hour.append({
                    "hour": m.date.strftime("%a"),
                    "jobs": m.total_orders or 0
                })
            
            # Agent stats (simulated from real data categories)
            agent_stats = {
                "sales": {"count": len(daily_metrics), "has_findings": len([m for m in daily_metrics if m.total_revenue])},
                "inventory": {"count": len(daily_metrics), "has_findings": len([m for m in daily_metrics if m.stockout_sku_count])},
                "marketing": {"count": len(daily_metrics), "has_findings": len([m for m in daily_metrics if m.marketing_conversions])},
                "support": {"count": len(daily_metrics), "has_findings": len([m for m in daily_metrics if m.total_complaints])}
            }
            
            # Recent "jobs" (using daily metrics as recent activity)
            recent_jobs = [
                {
                    "job_id": f"daily_{m.date.isoformat()}",
                    "question": f"Daily metrics for {m.date.strftime('%B %d, %Y')}",
                    "status": "completed",
                    "created_at": datetime.combine(m.date, datetime.min.time()).isoformat(),
                    "completed_at": datetime.combine(m.date, datetime.min.time()).isoformat()
                }
                for m in reversed(daily_metrics[-10:])
            ]
            
            # Calculate success rate (orders with positive revenue)
            success_rate = (len([m for m in daily_metrics if m.total_revenue and float(m.total_revenue) > 0]) / num_days * 100) if num_days > 0 else 0
            
            return {
                "summary": {
                    "total_jobs": total_orders,
                    "jobs_last_24h": yesterday_orders,
                    "jobs_last_7d": total_orders,
                    "success_rate": round(success_rate, 1),
                    "avg_completion_time_seconds": round(yesterday_aov, 2),  # Using AOV as a metric
                    
                    # Additional e-commerce specific
                    "total_revenue": round(total_revenue, 2),
                    "yesterday_revenue": round(yesterday_revenue, 2),
                    "avg_daily_revenue": round(avg_daily_revenue, 2),
                    "total_orders": total_orders,
                    "yesterday_orders": yesterday_orders,
                    "avg_order_value": round(yesterday_aov, 2),
                    "total_stockouts": total_stockouts,
                    "stockout_products": stockout_products,
                    "total_complaints": total_complaints,
                    "marketing_spend": round(total_marketing_spend, 2),
                    "marketing_conversions": total_conversions,
                    "data_range": {
                        "start": start_date.isoformat(),
                        "end": most_recent.isoformat()
                    }
                },
                "by_status": {
                    "completed": total_orders,
                    "revenue": round(total_revenue, 2),
                    "stockouts": total_stockouts,
                    "complaints": total_complaints
                },
                "recent_jobs": recent_jobs,
                "agent_stats": agent_stats,
                "jobs_by_hour": jobs_by_hour,
                "daily_breakdown": daily_breakdown,
                "ticket_categories": {
                    row[0]: row[1] for row in ticket_stats if row[0]
                },
                "marketing_channels": [
                    {
                        "channel": row[0],
                        "spend": float(row[1] or 0),
                        "conversions": row[2] or 0,
                        "clicks": row[3] or 0
                    }
                    for row in channel_stats if row[0]
                ],
                "system": {
                    "database": "postgresql",
                    "data_available": True,
                    "days_analyzed": num_days
                }
            }
            
    except Exception as e:
        logger.error(f"Error fetching e-commerce stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch e-commerce statistics: {str(e)}"
        )


@router.get(
    "/ecommerce/sales",
    summary="Get Sales Data",
    description="Get detailed sales data from PostgreSQL",
    responses={
        200: {"description": "Sales data retrieved successfully"}
    }
)
async def get_sales_data(
    days: int = Query(7, ge=1, le=90)
) -> Dict[str, Any]:
    """Get detailed sales data."""
    try:
        with session_scope() as session:
            most_recent = session.query(func.max(DailyMetrics.date)).scalar()
            
            if not most_recent:
                return {"error": "No sales data available", "data": []}
            
            start_date = most_recent - timedelta(days=days - 1)
            
            metrics = session.query(DailyMetrics).filter(
                and_(
                    DailyMetrics.date >= start_date,
                    DailyMetrics.date <= most_recent
                )
            ).order_by(DailyMetrics.date).all()
            
            return {
                "data": [
                    {
                        "date": m.date.isoformat(),
                        "revenue": float(m.total_revenue or 0),
                        "orders": m.total_orders or 0,
                        "aov": float(m.avg_order_value or 0)
                    }
                    for m in metrics
                ],
                "summary": {
                    "total_revenue": sum(float(m.total_revenue or 0) for m in metrics),
                    "total_orders": sum(m.total_orders or 0 for m in metrics),
                    "avg_aov": sum(float(m.avg_order_value or 0) for m in metrics) / len(metrics) if metrics else 0
                }
            }
    except Exception as e:
        logger.error(f"Error fetching sales data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ecommerce/inventory",
    summary="Get Inventory Data",
    description="Get inventory and stockout data",
    responses={
        200: {"description": "Inventory data retrieved successfully"}
    }
)
async def get_inventory_data(
    days: int = Query(7, ge=1, le=90)
) -> Dict[str, Any]:
    """Get inventory data."""
    try:
        with session_scope() as session:
            most_recent = session.query(func.max(DailyMetrics.date)).scalar()
            
            if not most_recent:
                return {"error": "No inventory data available", "data": []}
            
            start_date = most_recent - timedelta(days=days - 1)
            
            metrics = session.query(DailyMetrics).filter(
                and_(
                    DailyMetrics.date >= start_date,
                    DailyMetrics.date <= most_recent
                )
            ).order_by(DailyMetrics.date).all()
            
            return {
                "data": [
                    {
                        "date": m.date.isoformat(),
                        "stockouts": m.stockout_sku_count or 0
                    }
                    for m in metrics
                ],
                "summary": {
                    "total_stockouts": sum(m.stockout_sku_count or 0 for m in metrics),
                    "avg_daily_stockouts": sum(m.stockout_sku_count or 0 for m in metrics) / len(metrics) if metrics else 0
                }
            }
    except Exception as e:
        logger.error(f"Error fetching inventory data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ecommerce/marketing",
    summary="Get Marketing Data",
    description="Get marketing campaign data",
    responses={
        200: {"description": "Marketing data retrieved successfully"}
    }
)
async def get_marketing_data(
    days: int = Query(7, ge=1, le=90)
) -> Dict[str, Any]:
    """Get marketing campaign data."""
    try:
        with session_scope() as session:
            most_recent = session.query(func.max(MarketingCampaignsDaily.date)).scalar()
            
            if not most_recent:
                return {"error": "No marketing data available", "data": []}
            
            start_date = most_recent - timedelta(days=days - 1)
            
            # Get daily aggregates
            daily = session.query(
                MarketingCampaignsDaily.date,
                func.sum(MarketingCampaignsDaily.spend).label('spend'),
                func.sum(MarketingCampaignsDaily.conversions).label('conversions'),
                func.sum(MarketingCampaignsDaily.clicks).label('clicks'),
                func.sum(MarketingCampaignsDaily.impressions).label('impressions')
            ).filter(
                and_(
                    MarketingCampaignsDaily.date >= start_date,
                    MarketingCampaignsDaily.date <= most_recent
                )
            ).group_by(MarketingCampaignsDaily.date).order_by(MarketingCampaignsDaily.date).all()
            
            return {
                "data": [
                    {
                        "date": row[0].isoformat(),
                        "spend": float(row[1] or 0),
                        "conversions": row[2] or 0,
                        "clicks": row[3] or 0,
                        "impressions": row[4] or 0
                    }
                    for row in daily
                ]
            }
    except Exception as e:
        logger.error(f"Error fetching marketing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ecommerce/support",
    summary="Get Support Data",
    description="Get customer support ticket data",
    responses={
        200: {"description": "Support data retrieved successfully"}
    }
)
async def get_support_data(
    days: int = Query(7, ge=1, le=90)
) -> Dict[str, Any]:
    """Get support ticket data."""
    try:
        with session_scope() as session:
            most_recent = session.query(func.max(DailyMetrics.date)).scalar()
            
            if not most_recent:
                return {"error": "No support data available", "data": []}
            
            start_date = most_recent - timedelta(days=days - 1)
            
            metrics = session.query(DailyMetrics).filter(
                and_(
                    DailyMetrics.date >= start_date,
                    DailyMetrics.date <= most_recent
                )
            ).order_by(DailyMetrics.date).all()
            
            # Get ticket categories
            categories = session.query(
                SupportTickets.issue_category,
                func.count(SupportTickets.ticket_id).label('count')
            ).filter(
                func.date(SupportTickets.created_timestamp) >= start_date
            ).group_by(SupportTickets.issue_category).all()
            
            return {
                "data": [
                    {
                        "date": m.date.isoformat(),
                        "complaints": m.total_complaints or 0
                    }
                    for m in metrics
                ],
                "categories": {
                    row[0]: row[1] for row in categories if row[0]
                },
                "summary": {
                    "total_complaints": sum(m.total_complaints or 0 for m in metrics)
                }
            }
    except Exception as e:
        logger.error(f"Error fetching support data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
