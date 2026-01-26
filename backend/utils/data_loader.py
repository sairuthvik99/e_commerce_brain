"""
Data Loader Utility

High-level wrapper around MCP client for agents.
Provides synchronous interface (agents don't need to deal with async).
"""

import asyncio
from typing import Dict, Optional
from backend.mcp.client import MCPClient
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Synchronous data loader for agents.
    
    Wraps async MCP client calls in sync interface.
    """
    
    def __init__(self):
        self.client = MCPClient()
    
    def _run_async(self, coro):
        """Run async coroutine in sync context."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
    
    async def _get_data(self, method_name: str, **kwargs):
        """Helper to call MCP client methods."""
        async with self.client.connect():
            method = getattr(self.client, method_name)
            return await method(**kwargs)
    
    def get_yesterday_date(self) -> str:
        """Get most recent date (synchronous)."""
        logger.info("[DataLoader] Getting yesterday date...")
        return self._run_async(self._get_data("get_most_recent_date"))
    
    def load_sales_data(self, days: int = 7) -> Dict:
        """Load sales metrics (synchronous)."""
        logger.info(f"[DataLoader] Loading sales data for {days} days...")
        return self._run_async(self._get_data("get_daily_sales_metrics", days=days))
    
    def load_inventory_data(self, target_date: Optional[str] = None) -> Dict:
        """Load inventory data (synchronous)."""
        logger.info("[DataLoader] Loading inventory data...")
        return self._run_async(self._get_data("get_stockout_events", target_date=target_date))
    
    def load_inventory_baseline(self, days: int = 7) -> Dict:
        """Load inventory baseline (synchronous)."""
        logger.info("[DataLoader] Loading inventory baseline...")
        return self._run_async(self._get_data("get_inventory_baseline", days=days))
    
    def load_marketing_data(self, days: int = 7) -> Dict:
        """Load marketing data (synchronous)."""
        logger.info(f"[DataLoader] Loading marketing data for {days} days...")
        return self._run_async(self._get_data("get_campaign_performance", days=days))
    
    def load_support_data(self, days: int = 7) -> Dict:
        """Load support data (synchronous)."""
        logger.info(f"[DataLoader] Loading support data for {days} days...")
        return self._run_async(self._get_data("get_ticket_volume", days=days))


# Singleton instance
_data_loader = DataLoader()


def get_data_loader() -> DataLoader:
    """
    Get singleton DataLoader instance.
    
    Usage:
        loader = get_data_loader()
        sales_data = loader.load_sales_data(days=7)
    """
    return _data_loader


# Convenience functions (for backward compatibility)
def get_yesterday_date() -> str:
    return _data_loader.get_yesterday_date()


def load_sales_data(days: int = 7) -> Dict:
    return _data_loader.load_sales_data(days)


def load_inventory_data(target_date: Optional[str] = None) -> Dict:
    return _data_loader.load_inventory_data(target_date)


def load_inventory_baseline(days: int = 7) -> Dict:
    return _data_loader.load_inventory_baseline(days)


def load_marketing_data(days: int = 7) -> Dict:
    return _data_loader.load_marketing_data(days)


def load_support_data(days: int = 7) -> Dict:
    return _data_loader.load_support_data(days)