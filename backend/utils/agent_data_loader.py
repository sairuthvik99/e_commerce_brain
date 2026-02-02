"""
Agent-Aware Data Loader

Data loader that respects agent-specific table access permissions.
Each agent can only access data from tables they are authorized to use.
"""

from typing import Dict, Optional
from langfuse import observe
from backend.database.permissions import (
    can_use_data_method,
    get_allowed_data_methods,
    get_allowed_tables,
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
    to their domain.
    
    Access permissions:
    - Sales: daily_metrics, orders
    - Marketing: daily_metrics, marketing_campaigns_daily  
    - Inventory: daily_metrics, inventory_snapshots
    - Support: daily_metrics, support_tickets
    - General: ALL tables
    """
    
    def __init__(self, agent_type: str, use_direct: bool = True):
        """
        Initialize agent data loader.
        
        Args:
            agent_type: The type of agent (sales, marketing, inventory, support, general)
            use_direct: If True, use direct database access (recommended)
        """
        self.agent_type = agent_type.lower()
        self.use_direct = use_direct
        self._data_loader = DataLoader(use_direct=use_direct)
        
        # Cache allowed methods for this agent
        self._allowed_methods = set(get_allowed_data_methods(self.agent_type))
        self._allowed_tables = get_allowed_tables(self.agent_type)
        
        logger.info(
            f"[AgentDataLoader] Initialized for {self.agent_type} agent. "
            f"Allowed tables: {self._allowed_tables}"
        )
    
    def _check_access(self, method_name: str) -> None:
        """
        Check if agent has access to use a method.
        
        Raises:
            AccessDeniedError if access is denied
        """
        if not can_use_data_method(self.agent_type, method_name):
            raise AccessDeniedError(
                f"Agent '{self.agent_type}' does not have access to '{method_name}'. "
                f"Allowed methods: {self._allowed_methods}"
            )
    
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
def create_agent_loader(agent_type: str, use_direct: bool = True) -> AgentDataLoader:
    """
    Factory function to create an agent-specific data loader.
    
    Args:
        agent_type: The type of agent (sales, marketing, inventory, support, general)
        use_direct: If True, use direct database access
        
    Returns:
        AgentDataLoader configured for the specified agent
        
    Example:
        # Create a sales agent loader
        loader = create_agent_loader("sales")
        
        # Sales agent can load sales data
        sales_data = loader.load_sales_data()
        
        # But cannot load support data - will raise AccessDeniedError
        # loader.load_support_data()  # Raises AccessDeniedError
    """
    return AgentDataLoader(agent_type=agent_type, use_direct=use_direct)


# Pre-configured loaders for each agent type
class AgentLoaders:
    """Pre-configured data loaders for each agent type."""
    
    _instances: Dict[str, AgentDataLoader] = {}
    
    @classmethod
    def get(cls, agent_type: str) -> AgentDataLoader:
        """Get or create an AgentDataLoader for the specified agent type."""
        agent_type = agent_type.lower()
        if agent_type not in cls._instances:
            cls._instances[agent_type] = create_agent_loader(agent_type)
        return cls._instances[agent_type]
    
    @classmethod
    def sales(cls) -> AgentDataLoader:
        """Get the sales agent data loader."""
        return cls.get("sales")
    
    @classmethod
    def marketing(cls) -> AgentDataLoader:
        """Get the marketing agent data loader."""
        return cls.get("marketing")
    
    @classmethod
    def inventory(cls) -> AgentDataLoader:
        """Get the inventory agent data loader."""
        return cls.get("inventory")
    
    @classmethod
    def support(cls) -> AgentDataLoader:
        """Get the support agent data loader."""
        return cls.get("support")
    
    @classmethod
    def general(cls) -> AgentDataLoader:
        """Get the general agent data loader."""
        return cls.get("general")
