"""
Data Loader Utility

High-level wrapper around MCP client for agents.
Provides synchronous interface (agents don't need to deal with async).
All data loading operations are traced via Langfuse for observability.

Supports two modes:
1. MCP mode (default): Uses MCP client for data loading
2. Direct mode: Uses direct database queries (for Jupyter notebooks)
"""

import asyncio
from typing import Dict, Optional
from langfuse import observe
from backend.settings import Settings
from backend.mcp.client import MCPClient
import logging

# Enable nested event loops (required for Jupyter notebooks)
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass  # nest_asyncio not installed, will work in non-notebook environments

logger = logging.getLogger(__name__)


class DirectDataLoader:
    """
    Direct database data loader (no MCP).
    
    Uses database queries directly, which works better in Jupyter notebooks
    where MCP's subprocess-based communication has issues.
    
    All methods are traced via Langfuse.
    """
    
    def __init__(self):
        # Import here to avoid circular imports
        from backend.database import queries
        self.queries = queries
        logger.info("[DirectDataLoader] Initialized (direct database access)")
    
    @observe(name="direct_loader_get_yesterday_date")
    def get_yesterday_date(self) -> str:
        """Get most recent date (direct). Traced via Langfuse @observe decorator."""
        logger.info("[DirectDataLoader] Getting yesterday date...")
        result = self.queries.get_most_recent_date()
        return str(result)
    
    @observe(name="direct_loader_load_sales_data")
    def load_sales_data(self, days: int = 7) -> Dict:
        """Load sales metrics (direct). Traced via Langfuse @observe decorator."""
        logger.info(f"[DirectDataLoader] Loading sales data for {days} days...")
        result = self.queries.get_daily_sales_metrics(days=days)
        return result
    
    @observe(name="direct_loader_load_inventory_data")
    def load_inventory_data(self, target_date: Optional[str] = None) -> Dict:
        """Load inventory data (direct). Traced via Langfuse @observe decorator."""
        logger.info("[DirectDataLoader] Loading inventory data...")
        # Convert string to date if provided
        from datetime import datetime
        date_obj = None
        if target_date:
            date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        result = self.queries.get_stockout_events(target_date=date_obj)
        return result
    
    @observe(name="direct_loader_load_inventory_baseline")
    def load_inventory_baseline(self, days: int = 7) -> Dict:
        """Load inventory baseline (direct). Traced via Langfuse @observe decorator."""
        logger.info("[DirectDataLoader] Loading inventory baseline...")
        result = self.queries.get_inventory_baseline(days=days)
        return result
    
    @observe(name="direct_loader_load_marketing_data")
    def load_marketing_data(self, days: int = 7) -> Dict:
        """Load marketing data (direct). Traced via Langfuse @observe decorator."""
        logger.info(f"[DirectDataLoader] Loading marketing data for {days} days...")
        result = self.queries.get_campaign_performance(days=days)
        return result
    
    @observe(name="direct_loader_load_channel_data")
    def load_channel_data(self, days: int = 7) -> Dict:
        """Load marketing channel data (direct). Traced via Langfuse @observe decorator."""
        logger.info(f"[DirectDataLoader] Loading channel data for {days} days...")
        result = self.queries.get_campaign_channels(days=days)
        return result
    
    @observe(name="direct_loader_load_support_data")
    def load_support_data(self, days: int = 7) -> Dict:
        """Load support data (direct). Traced via Langfuse @observe decorator."""
        logger.info(f"[DirectDataLoader] Loading support data for {days} days...")
        result = self.queries.get_ticket_volume(days=days)
        return result
    
    @observe(name="direct_loader_load_top_products_data")
    def load_top_products_data(self, days: int = 7, top_n: int = 5) -> Dict:
        """Load top selling products data (direct). Traced via Langfuse @observe decorator."""
        logger.info(f"[DirectDataLoader] Loading top {top_n} products for {days} days...")
        result = self.queries.get_top_selling_products(days=days, top_n=top_n)
        return result
    
    @observe(name="direct_loader_load_all_products_inventory")
    def load_all_products_inventory(self) -> Dict:
        """Load all products with their current inventory status. Traced via Langfuse @observe decorator."""
        logger.info("[DirectDataLoader] Loading all products inventory...")
        result = self.queries.get_all_products_inventory()
        return result
    
    @observe(name="direct_loader_load_product_inventory")
    def load_product_inventory(self, product_id: int) -> Dict:
        """Load inventory details for a specific product. Traced via Langfuse @observe decorator."""
        logger.info(f"[DirectDataLoader] Loading product {product_id} inventory...")
        result = self.queries.get_product_inventory(product_id)
        return result
    
    @observe(name="direct_loader_search_products")
    def search_products(self, search_term: str) -> Dict:
        """Search for products by name/id. Traced via Langfuse @observe decorator."""
        logger.info(f"[DirectDataLoader] Searching products for '{search_term}'...")
        result = self.queries.search_products_by_name(search_term)
        return result
    
    @observe(name="direct_loader_update_product_stock")
    def update_product_stock(self, product_id: int, quantity_change: int, reason: str = None) -> Dict:
        """Update stock level for a product. Traced via Langfuse @observe decorator."""
        logger.info(f"[DirectDataLoader] Updating product {product_id} stock by {quantity_change}...")
        result = self.queries.update_product_stock(product_id, quantity_change, reason)
        return result


class DataLoader:
    """
    Synchronous data loader for agents.
    All methods are traced via Langfuse.
    
    Wraps async MCP client calls in sync interface.
    Falls back to DirectDataLoader if MCP fails.
    """
    
    def __init__(self, use_direct: bool = False):
        """
        Initialize data loader.
        
        Args:
            use_direct: If True, use direct database access instead of MCP.
                        Recommended for Jupyter notebooks.
        """
        self.use_direct = use_direct
        if use_direct:
            self._direct_loader = DirectDataLoader()
            self.client = None
        else:
            self.client = MCPClient()
            self._direct_loader = None
    
    def _get_direct_loader(self):
        """Lazy-init direct loader for fallback."""
        if self._direct_loader is None:
            self._direct_loader = DirectDataLoader()
        return self._direct_loader
    
    def _run_async(self, coro):
        """
        Run async coroutine in sync context.
        
        Works in both regular Python and Jupyter notebooks
        by using nest_asyncio to allow nested event loops.
        """
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're inside a running loop (e.g., Jupyter)
                # nest_asyncio allows this to work
                return loop.run_until_complete(coro)
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop exists, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
    
    async def _get_data(self, method_name: str, **kwargs):
        """Helper to call MCP client methods."""
        async with self.client.connect():
            method = getattr(self.client, method_name)
            return await method(**kwargs)
    
    def _with_fallback(self, mcp_method: str, direct_method: str, **kwargs):
        """Try MCP first, fall back to direct if it fails."""
        if self.use_direct:
            # Use direct loader
            direct_loader = self._get_direct_loader()
            method = getattr(direct_loader, direct_method)
            return method(**kwargs)
        
        try:
            # Try MCP
            return self._run_async(self._get_data(mcp_method, **kwargs))
        except Exception as e:
            logger.warning(f"[DataLoader] MCP failed ({e}), falling back to direct database")
            direct_loader = self._get_direct_loader()
            method = getattr(direct_loader, direct_method)
            return method(**kwargs)
    
    @observe(name="data_loader_get_yesterday_date")
    def get_yesterday_date(self) -> str:
        """Get most recent date (synchronous). Traced via Langfuse @observe decorator."""
        logger.info("[DataLoader] Getting yesterday date...")
        return self._with_fallback("get_most_recent_date", "get_yesterday_date")
    
    @observe(name="data_loader_load_sales_data")
    def load_sales_data(self, days: int = 7) -> Dict:
        """Load sales metrics (synchronous). Traced via Langfuse @observe decorator."""
        logger.info(f"[DataLoader] Loading sales data for {days} days...")
        return self._with_fallback("get_daily_sales_metrics", "load_sales_data", days=days)
    
    @observe(name="data_loader_load_inventory_data")
    def load_inventory_data(self, target_date: Optional[str] = None) -> Dict:
        """Load inventory data (synchronous). Traced via Langfuse @observe decorator."""
        logger.info("[DataLoader] Loading inventory data...")
        return self._with_fallback("get_stockout_events", "load_inventory_data", target_date=target_date)
    
    @observe(name="data_loader_load_inventory_baseline")
    def load_inventory_baseline(self, days: int = 7) -> Dict:
        """Load inventory baseline (synchronous). Traced via Langfuse @observe decorator."""
        logger.info("[DataLoader] Loading inventory baseline...")
        return self._with_fallback("get_inventory_baseline", "load_inventory_baseline", days=days)
    
    @observe(name="data_loader_load_marketing_data")
    def load_marketing_data(self, days: int = 7) -> Dict:
        """Load marketing data (synchronous). Traced via Langfuse @observe decorator."""
        logger.info(f"[DataLoader] Loading marketing data for {days} days...")
        return self._with_fallback("get_campaign_performance", "load_marketing_data", days=days)
    
    @observe(name="data_loader_load_channel_data")
    def load_channel_data(self, days: int = 7) -> Dict:
        """Load marketing channel data (synchronous). Traced via Langfuse @observe decorator."""
        logger.info(f"[DataLoader] Loading channel data for {days} days...")
        return self._with_fallback("get_campaign_channels", "load_channel_data", days=days)
    
    @observe(name="data_loader_load_support_data")
    def load_support_data(self, days: int = 7) -> Dict:
        """Load support data (synchronous). Traced via Langfuse @observe decorator."""
        logger.info(f"[DataLoader] Loading support data for {days} days...")
        return self._with_fallback("get_ticket_volume", "load_support_data", days=days)
    
    @observe(name="data_loader_load_top_products_data")
    def load_top_products_data(self, days: int = 7, top_n: int = 5) -> Dict:
        """Load top selling products data (synchronous). Traced via Langfuse @observe decorator."""
        logger.info(f"[DataLoader] Loading top {top_n} products for {days} days...")
        return self._with_fallback("get_top_selling_products", "load_top_products_data", days=days, top_n=top_n)
    
    @observe(name="data_loader_load_all_products_inventory")
    def load_all_products_inventory(self) -> Dict:
        """Load all products with their current inventory status. Traced via Langfuse @observe decorator."""
        logger.info("[DataLoader] Loading all products inventory...")
        # Direct method only - no MCP equivalent
        direct_loader = self._get_direct_loader()
        return direct_loader.load_all_products_inventory()
    
    @observe(name="data_loader_load_product_inventory")
    def load_product_inventory(self, product_id: int) -> Dict:
        """Load inventory details for a specific product. Traced via Langfuse @observe decorator."""
        logger.info(f"[DataLoader] Loading product {product_id} inventory...")
        # Direct method only - no MCP equivalent
        direct_loader = self._get_direct_loader()
        return direct_loader.load_product_inventory(product_id)
    
    @observe(name="data_loader_search_products")
    def search_products(self, search_term: str) -> Dict:
        """Search for products by name/id. Traced via Langfuse @observe decorator."""
        logger.info(f"[DataLoader] Searching products for '{search_term}'...")
        # Direct method only - no MCP equivalent
        direct_loader = self._get_direct_loader()
        return direct_loader.search_products(search_term)
    
    @observe(name="data_loader_update_product_stock")
    def update_product_stock(self, product_id: int, quantity_change: int, reason: str = None) -> Dict:
        """Update stock level for a product. Traced via Langfuse @observe decorator."""
        logger.info(f"[DataLoader] Updating product {product_id} stock by {quantity_change}...")
        # Direct method only - no MCP equivalent
        direct_loader = self._get_direct_loader()
        return direct_loader.update_product_stock(product_id, quantity_change, reason)


# Singleton instances
_data_loader = None
_direct_data_loader = None


def get_data_loader(use_direct: bool = False) -> DataLoader:
    """
    Get singleton DataLoader instance.
    
    Args:
        use_direct: If True, use direct database access (recommended for Jupyter).
                    If False, use MCP with fallback to direct.
    
    Usage:
        # For Jupyter notebooks (recommended)
        loader = get_data_loader(use_direct=True)
        
        # For regular Python (uses MCP with fallback)
        loader = get_data_loader()
        
        sales_data = loader.load_sales_data(days=7)
    """
    global _data_loader, _direct_data_loader
    
    if use_direct:
        if _direct_data_loader is None:
            _direct_data_loader = DataLoader(use_direct=True)
        return _direct_data_loader
    else:
        if _data_loader is None:
            _data_loader = DataLoader(use_direct=False)
        return _data_loader


def get_direct_data_loader() -> DirectDataLoader:
    """
    Get singleton DirectDataLoader instance.
    
    Use this for direct database access (no MCP).
    Recommended for Jupyter notebooks.
    
    Usage:
        loader = get_direct_data_loader()
        sales_data = loader.load_sales_data(days=7)
    """
    global _direct_data_loader
    if _direct_data_loader is None:
        _direct_data_loader = DataLoader(use_direct=True)
    return _direct_data_loader


# Convenience functions (for backward compatibility)
# These use the fallback-enabled DataLoader

def get_yesterday_date() -> str:
    return get_data_loader().get_yesterday_date()


def load_sales_data(days: int = 7) -> Dict:
    return get_data_loader().load_sales_data(days)


def load_inventory_data(target_date: Optional[str] = None) -> Dict:
    return get_data_loader().load_inventory_data(target_date)


def load_inventory_baseline(days: int = 7) -> Dict:
    return get_data_loader().load_inventory_baseline(days)


def load_marketing_data(days: int = 7) -> Dict:
    return get_data_loader().load_marketing_data(days)


def load_support_data(days: int = 7) -> Dict:
    return get_data_loader().load_support_data(days)