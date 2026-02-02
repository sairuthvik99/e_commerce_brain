"""
SQLAlchemy ORM models for all database tables.

Maps to existing PostgreSQL schema (no migrations needed).
"""

from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, 
    TIMESTAMP, Date, Text, BigInteger
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, date

Base = declarative_base()


class Orders(Base):
    """
    Orders table - transaction-level order data.
    
    Used by: Sales Agent
    """
    __tablename__ = "orders"
    
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    order_timestamp = Column(TIMESTAMP, nullable=False)
    customer_id = Column(Integer, nullable=False)
    region = Column(Text, nullable=True)
    order_value = Column(Numeric, nullable=False)
    product_count = Column(Integer, nullable=True)
    created_date = Column(Date, nullable=False, index=True)
    
    def __repr__(self):
        return f"<Order {self.order_id}: ${self.order_value} on {self.created_date}>"


class InventorySnapshots(Base):
    """
    Inventory snapshots - stock levels over time.
    
    Used by: Inventory Agent
    """
    __tablename__ = "inventory_snapshots"
    
    snapshot_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False, index=True)
    snapshot_timestamp = Column(TIMESTAMP, nullable=False, index=True)
    available_stock = Column(Integer, nullable=False)
    stock_threshold = Column(Integer, nullable=True)
    is_out_of_stock = Column(Boolean, nullable=False, default=False, index=True)
    out_of_stock_since = Column(TIMESTAMP, nullable=True)
    
    def __repr__(self):
        return f"<Inventory Product {self.product_id}: Stock={self.available_stock}>"


class MarketingCampaignsDaily(Base):
    """
    Marketing campaign performance - daily aggregates.
    
    Used by: Marketing Agent
    """
    __tablename__ = "marketing_campaigns_daily"
    
    # Note: No explicit primary key in seed script, adding composite key
    campaign_id = Column(Integer, primary_key=True)
    date = Column(Date, primary_key=True, index=True)
    channel = Column(Text, nullable=True)
    impressions = Column(Integer, nullable=True)
    clicks = Column(Integer, nullable=True)
    spend = Column(Numeric, nullable=True)
    conversions = Column(Integer, nullable=True)
    campaign_status = Column(Text, nullable=True, index=True)
    
    def __repr__(self):
        return f"<Campaign {self.campaign_id} on {self.date}: {self.conversions} conversions>"


class SupportTickets(Base):
    """
    Support tickets - customer issues.
    
    Used by: Support Agent
    """
    __tablename__ = "support_tickets"
    
    ticket_id = Column(Integer, primary_key=True, autoincrement=True)
    created_timestamp = Column(TIMESTAMP, nullable=False, index=True)
    issue_category = Column(Text, nullable=True, index=True)
    sentiment = Column(Text, nullable=True, index=True)
    product_id = Column(Integer, nullable=True)
    customer_id = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Ticket {self.ticket_id}: {self.issue_category} ({self.sentiment})>"


class DailyMetrics(Base):
    """
    Daily aggregated metrics - summary of all KPIs.
    
    Used by: All agents (for baseline comparisons)
    """
    __tablename__ = "daily_metrics"
    
    date = Column(Date, primary_key=True, index=True)
    total_revenue = Column(Numeric, nullable=True)
    total_orders = Column(Integer, nullable=True)
    avg_order_value = Column(Numeric, nullable=True)
    stockout_sku_count = Column(Integer, nullable=True)
    total_complaints = Column(Integer, nullable=True)
    marketing_spend = Column(Numeric, nullable=True)
    marketing_conversions = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<DailyMetrics {self.date}: Revenue=${self.total_revenue}, Orders={self.total_orders}>"


class ConversationHistory(Base):
    """
    Conversation history for short-term memory.
    
    Stores recent Q&A pairs for agent context.
    Limited to last 10 entries for efficient memory management.
    
    Used by: Memory module (MemoryLoaderNode, MemorySaverNode)
    """
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    intent = Column(Text, nullable=True, index=True)
    agent_outputs = Column(JSONB, nullable=True)
    root_cause = Column(JSONB, nullable=True)
    timestamp = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<Conversation {self.id}: {self.question[:50]}...>"