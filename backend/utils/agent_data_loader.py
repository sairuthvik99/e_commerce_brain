"""
Agent-Aware Data Loader

Data loader that respects agent-specific table access permissions.
Each agent can only access data from tables they are authorized to use.
Supports cross-domain access for queries that require multiple data sources.
"""

from typing import Dict, Optional, Set
from langfuse import observe
from backend.database.permissions import (
    can_use_data_method,
    get_allowed_data_methods,
    get_allowed_tables,
    get_cross_domain_methods,
    AgentType
)
from backend.utils.data_loader import DataLoader, DirectDataLoader
import logging

logger = logging.getLogger(__name__)


class AccessDeniedError(Exception):
    """Raised when an agent tries to access data they don't have permission for."""
    pass


class AgentDataLoader:
    """
    Agent-specific data loader with table access restrictions.
    
    This loader wraps the base DataLoader and enforces access permissions
    based on the agent type. Each agent can only access tables relevant
    to their domain. Cross-domain access can be enabled for queries
    that require data from multiple sources.
    
    Access permissions (base):
    - Sales: daily_metrics, orders
    - Marketing: daily_metrics, marketing_campaigns_daily  
    - Inventory: daily_metrics, inventory_snapshots
    - Support: daily_metrics, support_tickets
    - General: ALL tables
    
    Cross-domain access (when enabled):
    - Inventory: + orders (for viewed/purchased analysis)
    - Marketing: + orders (for discount/ROI analysis)
    - Support: + orders (for review/conversion correlation)
    - Sales: + inventory_snapshots, marketing_campaigns_daily (for root cause)
    """
    
    def __init__(
        self, 
        agent_type: str, 
        use_direct: bool = True,
        allow_cross_domain: bool = True
    ):
        """
        Initialize agent data loader.
        
        Args:
            agent_type: The type of agent (sales, marketing, inventory, support, general)
            use_direct: If True, use direct database access (recommended)
            allow_cross_domain: If True, enable cross-domain data access
        """
        self.agent_type = agent_type.lower()
        self.use_direct = use_direct
        self.allow_cross_domain = allow_cross_domain
        self._data_loader = DataLoader(use_direct=use_direct)
        
        # Cache allowed methods for this agent 
        self._allowed_methods = set(
            get_allowed_data_methods(self.agent_type, include_cross_domain=allow_cross_domain)
        )
        self._allowed_tables = get_allowed_tables(
            self.agent_type, include_cross_domain=allow_cross_domain
        )
        self._cross_domain_methods = get_cross_domain_methods(self.agent_type)
        
        logger.info(
            f"[AgentDataLoader] Initialized for {self.agent_type} agent. "
            f"Cross-domain: {allow_cross_domain}. "
            f"Allowed methods: {self._allowed_methods}"
        )
    
    def _check_access(self, method_name: str) -> None:
        """
        Check if agent has access to use a method.
        
        Raises:
            AccessDeniedError if access is denied
        """
        if not can_use_data_method(
            self.agent_type, 
            method_name, 
            include_cross_domain=self.allow_cross_domain
        ):
            raise AccessDeniedError(
                f"Agent '{self.agent_type}' does not have access to '{method_name}'. "
                f"Allowed methods: {self._allowed_methods}"
            )
    
    def is_cross_domain_method(self, method_name: str) -> bool:
        """Check if a method is accessed via cross-domain permissions."""
        return method_name in self._cross_domain_methods
    
    @property
    def cross_domain_methods(self) -> Set[str]:
        """Get the set of methods accessible via cross-domain permissions."""
        return self._cross_domain_methods.copy()
    
    @property
    def allowed_tables(self) -> set:
        """Get the set of tables this agent can access."""
        return self._allowed_tables.copy()
    
    @property  
    def allowed_methods(self) -> set:
        """Get the set of data loader methods this agent can use."""
        return self._allowed_methods.copy()
    
    @observe(name="agent_loader_get_yesterday_date")
    def get_yesterday_date(self) -> str:
        """Get most recent date. All agents have access to this."""
        self._check_access('get_yesterday_date')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Getting yesterday date...")
        return self._data_loader.get_yesterday_date()
    
    @observe(name="agent_loader_load_sales_data")
    def load_sales_data(self, days: int = 7) -> Dict:
        """
        Load sales metrics.
        
        Requires access to: daily_metrics, orders
        Available to: sales, general agents
        """
        self._check_access('load_sales_data')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Loading sales data for {days} days...")
        return self._data_loader.load_sales_data(days=days)
    
    @observe(name="agent_loader_load_inventory_data")
    def load_inventory_data(self, target_date: Optional[str] = None) -> Dict:
        """
        Load inventory/stockout data.
        
        Requires access to: daily_metrics, inventory_snapshots
        Available to: inventory, general agents
        """
        self._check_access('load_inventory_data')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Loading inventory data...")
        return self._data_loader.load_inventory_data(target_date=target_date)
    
    @observe(name="agent_loader_load_inventory_baseline")
    def load_inventory_baseline(self, days: int = 7) -> Dict:
        """
        Load inventory baseline metrics.
        
        Requires access to: daily_metrics, inventory_snapshots
        Available to: inventory, general agents
        """
        self._check_access('load_inventory_baseline')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Loading inventory baseline...")
        return self._data_loader.load_inventory_baseline(days=days)
    
    @observe(name="agent_loader_load_marketing_data")
    def load_marketing_data(self, days: int = 7) -> Dict:
        """
        Load marketing campaign data.
        
        Requires access to: daily_metrics, marketing_campaigns_daily
        Available to: marketing, general agents
        """
        self._check_access('load_marketing_data')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Loading marketing data for {days} days...")
        return self._data_loader.load_marketing_data(days=days)
    
    @observe(name="agent_loader_load_channel_data")
    def load_channel_data(self, days: int = 7) -> Dict:
        """
        Load marketing channel data.
        
        Requires access to: marketing_campaigns_daily
        Available to: marketing, general agents
        """
        self._check_access('load_channel_data')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Loading channel data for {days} days...")
        return self._data_loader.load_channel_data(days=days)
    
    @observe(name="agent_loader_load_support_data") 
    def load_support_data(self, days: int = 7) -> Dict:
        """
        Load support ticket data.
        
        Requires access to: daily_metrics, support_tickets
        Available to: support, general agents
        """
        self._check_access('load_support_data')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Loading support data for {days} days...")
        return self._data_loader.load_support_data(days=days)
    
    @observe(name="agent_loader_load_all_products_inventory")
    def load_all_products_inventory(self) -> Dict:
        """
        Load all products with their current inventory status.
        
        Requires access to: inventory_snapshots
        Available to: inventory, general agents
        """
        self._check_access('load_all_products_inventory')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Loading all products inventory...")
        return self._data_loader.load_all_products_inventory()
    
    @observe(name="agent_loader_load_product_inventory")
    def load_product_inventory(self, product_id: int) -> Dict:
        """
        Load inventory details for a specific product.
        
        Requires access to: inventory_snapshots
        Available to: inventory, general agents
        """
        self._check_access('load_product_inventory')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Loading product {product_id} inventory...")
        return self._data_loader.load_product_inventory(product_id)
    
    @observe(name="agent_loader_search_products")
    def search_products(self, search_term: str) -> Dict:
        """
        Search for products by name/id.
        
        Requires access to: inventory_snapshots
        Available to: inventory, general agents
        """
        self._check_access('search_products')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Searching products for '{search_term}'...")
        return self._data_loader.search_products(search_term)
    
    @observe(name="agent_loader_update_product_stock")
    def update_product_stock(self, product_id: int, quantity_change: int, reason: str = None) -> Dict:
        """
        Update stock level for a product.
        
        Requires access to: inventory_snapshots (write)
        Available to: inventory, general agents
        NOTE: This should only be called after HITL approval
        """
        self._check_access('update_product_stock')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Updating product {product_id} stock by {quantity_change}...")
        return self._data_loader.update_product_stock(product_id, quantity_change, reason)
    
    @observe(name="agent_loader_load_top_products_data")
    def load_top_products_data(self, days: int = 7, top_n: int = 5) -> Dict:
        """
        Load top selling products data.
        
        Requires access to: orders, order_items
        Available to: sales, general agents
        """
        self._check_access('load_top_products_data')
        logger.info(f"[AgentDataLoader:{self.agent_type}] Loading top {top_n} products for {days} days...")
        return self._data_loader.load_top_products_data(days=days, top_n=top_n)
    
    def load_all_domain_data(self, days: int = 7) -> Dict:
        """
        Load data from all domains the agent has access to.
        
        Returns a dict with data from each accessible domain.
        Only available to general agent by default.
        """
        data = {}
        
        if 'load_sales_data' in self._allowed_methods:
            try:
                data['sales'] = self.load_sales_data(days=days)
            except Exception as e:
                logger.warning(f"Failed to load sales data: {e}")
                data['sales'] = {}
        
        if 'load_inventory_data' in self._allowed_methods:
            try:
                data['inventory'] = self.load_inventory_data()
                data['inventory_baseline'] = self.load_inventory_baseline(days=days)
            except Exception as e:
                logger.warning(f"Failed to load inventory data: {e}")
                data['inventory'] = {}
        
        if 'load_marketing_data' in self._allowed_methods:
            try:
                data['marketing'] = self.load_marketing_data(days=days)
            except Exception as e:
                logger.warning(f"Failed to load marketing data: {e}")
                data['marketing'] = {}
        
        if 'load_support_data' in self._allowed_methods:
            try:
                data['support'] = self.load_support_data(days=days)
            except Exception as e:
                logger.warning(f"Failed to load support data: {e}")
                data['support'] = {}
        
        return data


# Factory function to create agent-specific loaders
def create_agent_loader(
    agent_type: str, 
    use_direct: bool = True,
    allow_cross_domain: bool = True
) -> AgentDataLoader:
    """
    Factory function to create an agent-specific data loader.
    
    Args:
        agent_type: The type of agent (sales, marketing, inventory, support, general)
        use_direct: If True, use direct database access
        allow_cross_domain: If True, enable cross-domain data access
        
    Returns:
        AgentDataLoader configured for the specified agent
        
    Example:
        # Create an inventory agent loader with cross-domain access
        loader = create_agent_loader("inventory", allow_cross_domain=True)
        
        # Inventory agent can load inventory data (base permission)
        inventory_data = loader.load_inventory_data()
        
        # Inventory agent can also load sales data (cross-domain permission)
        sales_data = loader.load_sales_data()  # Works with cross-domain enabled!
    """
    return AgentDataLoader(
        agent_type=agent_type, 
        use_direct=use_direct,
        allow_cross_domain=allow_cross_domain
    )


# Pre-configured loaders for each agent type
class AgentLoaders:
    """Pre-configured data loaders for each agent type."""
    
    _instances: Dict[str, AgentDataLoader] = {}
    
    @classmethod
    def get(cls, agent_type: str, allow_cross_domain: bool = True) -> AgentDataLoader:
        """Get or create an AgentDataLoader for the specified agent type."""
        agent_type = agent_type.lower()
        cache_key = f"{agent_type}_{allow_cross_domain}"
        if cache_key not in cls._instances:
            cls._instances[cache_key] = create_agent_loader(
                agent_type, 
                allow_cross_domain=allow_cross_domain
            )
        return cls._instances[cache_key]
    
    @classmethod
    def sales(cls, allow_cross_domain: bool = True) -> AgentDataLoader:
        """Get the sales agent data loader."""
        return cls.get("sales", allow_cross_domain=allow_cross_domain)
    
    @classmethod
    def marketing(cls, allow_cross_domain: bool = True) -> AgentDataLoader:
        """Get the marketing agent data loader."""
        return cls.get("marketing", allow_cross_domain=allow_cross_domain)
    
    @classmethod
    def inventory(cls, allow_cross_domain: bool = True) -> AgentDataLoader:
        """Get the inventory agent data loader."""
        return cls.get("inventory", allow_cross_domain=allow_cross_domain)
    
    @classmethod
    def support(cls, allow_cross_domain: bool = True) -> AgentDataLoader:
        """Get the support agent data loader."""
        return cls.get("support", allow_cross_domain=allow_cross_domain)
    
    @classmethod
    def general(cls) -> AgentDataLoader:
        """Get the general agent data loader."""
        return cls.get("general", allow_cross_domain=True)
