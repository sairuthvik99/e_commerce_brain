"""
Long-Term Memory Module using LangGraph Store API

Provides cross-session persistent memory for storing:
- User preferences
- Learned facts
- System knowledge

Uses PostgresStore for production-ready persistent storage.
Since there's only one session in this project, we use a simplified namespace structure.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import atexit

from langgraph.store.postgres import PostgresStore
from psycopg_pool import ConnectionPool

from backend.settings import Settings

logger = logging.getLogger(__name__)

# Namespace structure for long-term memory
# Format: (category, subcategory)
NAMESPACE_PREFERENCES = ("system", "preferences")
NAMESPACE_FACTS = ("system", "facts")
NAMESPACE_KNOWLEDGE = ("system", "knowledge")

# Global instances (singleton)
_pool: Optional[ConnectionPool] = None
_conn = None
_store: Optional[PostgresStore] = None


def _get_connection_pool() -> ConnectionPool:
    """Get or create the connection pool."""
    global _pool
    
    if _pool is None:
        # Build connection string for psycopg3
        conn_string = (
            f"host={Settings.DB_HOST} "
            f"port={Settings.DB_PORT} "
            f"dbname={Settings.DB_NAME} "
            f"user={Settings.DB_USER} "
            f"password={Settings.DB_PASSWORD.replace('%40', '@')}"
        )
        _pool = ConnectionPool(conn_string, min_size=1, max_size=5)
        logger.info("[LongTermMemory] Connection pool created")
        
        # Register cleanup on exit
        atexit.register(_cleanup_pool)
    
    return _pool


def _cleanup_pool():
    """Cleanup the connection pool on exit."""
    global _pool, _store, _conn
    if _conn and _pool:
        try:
            _conn.commit()  # Commit any pending transactions
            _pool.putconn(_conn)
            logger.info("[LongTermMemory] Connection returned to pool")
        except Exception as e:
            logger.warning(f"[LongTermMemory] Error returning connection: {e}")
        _conn = None
    
    if _pool:
        try:
            _pool.close()
            logger.info("[LongTermMemory] Connection pool closed")
        except Exception as e:
            logger.warning(f"[LongTermMemory] Error closing pool: {e}")
        _pool = None
    
    _store = None


def get_store() -> PostgresStore:
    """
    Get or create the PostgresStore instance.
    
    Uses a singleton pattern to reuse the store connection.
    
    Returns:
        PostgresStore instance
    """
    global _store, _conn
    
    if _store is not None:
        return _store
    
    try:
        pool = _get_connection_pool()
        
        # Get a persistent connection from the pool
        _conn = pool.getconn()
        
        # Create PostgresStore with the connection
        _store = PostgresStore(conn=_conn)
        
        # Setup the store tables
        _store.setup()
        
        logger.info("[LongTermMemory] PostgresStore initialized successfully")
        return _store
        
    except Exception as e:
        logger.error(f"[LongTermMemory] Failed to initialize PostgresStore: {e}")
        raise


class LongTermMemory:
    """
    Long-term memory manager for the agent system.
    
    Stores persistent information that survives across sessions:
    - User preferences (theme, language, etc.)
    - Learned facts (user info, business rules)
    - System knowledge (accumulated insights)
    
    Uses LangGraph's Store API with PostgreSQL backend.
    """
    
    def __init__(self):
        """Initialize the long-term memory store."""
        self._store = None
    
    @property
    def store(self) -> PostgresStore:
        """Lazy initialization of the store."""
        if self._store is None:
            self._store = get_store()
        return self._store
    
    # ==================== PREFERENCES ====================
    
    def save_preference(self, key: str, value: Any) -> None:
        """
        Save a user/system preference.
        
        Args:
            key: Preference key (e.g., 'theme', 'language', 'model')
            value: Preference value
        """
        try:
            self.store.put(
                namespace=NAMESPACE_PREFERENCES,
                key=key,
                value={
                    "value": value,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"[LongTermMemory] Saved preference: {key}")
        except Exception as e:
            logger.error(f"[LongTermMemory] Failed to save preference {key}: {e}")
            raise
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a user/system preference.
        
        Args:
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        try:
            item = self.store.get(
                namespace=NAMESPACE_PREFERENCES,
                key=key
            )
            if item and item.value:
                return item.value.get("value", default)
            return default
        except Exception as e:
            logger.warning(f"[LongTermMemory] Failed to get preference {key}: {e}")
            return default
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """
        Get all stored preferences.
        
        Returns:
            Dict of all preferences
        """
        try:
            items = self.store.search(NAMESPACE_PREFERENCES)
            return {
                item.key: item.value.get("value")
                for item in items
                if item.value
            }
        except Exception as e:
            logger.warning(f"[LongTermMemory] Failed to get all preferences: {e}")
            return {}
    
    def delete_preference(self, key: str) -> None:
        """Delete a preference."""
        try:
            self.store.delete(namespace=NAMESPACE_PREFERENCES, key=key)
            logger.info(f"[LongTermMemory] Deleted preference: {key}")
        except Exception as e:
            logger.warning(f"[LongTermMemory] Failed to delete preference {key}: {e}")
    
    # ==================== FACTS ====================
    
    def save_fact(self, fact: str, category: str = "general", key: Optional[str] = None) -> str:
        """
        Save a learned fact.
        
        Args:
            fact: The fact to store
            category: Category of the fact (e.g., 'user_info', 'business_rule')
            key: Optional key (auto-generated if not provided)
            
        Returns:
            The key used to store the fact
        """
        if key is None:
            key = f"{category}_{uuid.uuid4().hex[:8]}"
        
        try:
            self.store.put(
                namespace=NAMESPACE_FACTS,
                key=key,
                value={
                    "fact": fact,
                    "category": category,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"[LongTermMemory] Saved fact: {key}")
            return key
        except Exception as e:
            logger.error(f"[LongTermMemory] Failed to save fact: {e}")
            raise
    
    def get_facts(self, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get stored facts, optionally filtered by category.
        
        Args:
            category: Optional category filter
            limit: Maximum number of facts to return
            
        Returns:
            List of facts
        """
        try:
            items = self.store.search(NAMESPACE_FACTS, limit=limit)
            
            facts = []
            for item in items:
                if item.value:
                    fact_data = item.value
                    # Filter by category if specified
                    if category is None or fact_data.get("category") == category:
                        facts.append({
                            "key": item.key,
                            "fact": fact_data.get("fact", ""),
                            "category": fact_data.get("category", "general"),
                            "created_at": fact_data.get("created_at")
                        })
            
            return facts[:limit]
        except Exception as e:
            logger.warning(f"[LongTermMemory] Failed to get facts: {e}")
            return []
    
    def delete_fact(self, key: str) -> None:
        """Delete a fact by key."""
        try:
            self.store.delete(namespace=NAMESPACE_FACTS, key=key)
            logger.info(f"[LongTermMemory] Deleted fact: {key}")
        except Exception as e:
            logger.warning(f"[LongTermMemory] Failed to delete fact {key}: {e}")
    
    # ==================== KNOWLEDGE ====================
    
    def save_knowledge(self, topic: str, content: str, source: str = "agent") -> str:
        """
        Save accumulated knowledge/insights.
        
        Args:
            topic: Topic/title of the knowledge
            content: The knowledge content
            source: Source of the knowledge (e.g., 'agent', 'user', 'analysis')
            
        Returns:
            The key used to store the knowledge
        """
        key = f"{source}_{uuid.uuid4().hex[:8]}"
        
        try:
            self.store.put(
                namespace=NAMESPACE_KNOWLEDGE,
                key=key,
                value={
                    "topic": topic,
                    "content": content,
                    "source": source,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"[LongTermMemory] Saved knowledge: {topic}")
            return key
        except Exception as e:
            logger.error(f"[LongTermMemory] Failed to save knowledge: {e}")
            raise
    
    def get_knowledge(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get stored knowledge entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of knowledge entries
        """
        try:
            items = self.store.search(NAMESPACE_KNOWLEDGE, limit=limit)
            
            knowledge = []
            for item in items:
                if item.value:
                    knowledge.append({
                        "key": item.key,
                        "topic": item.value.get("topic", ""),
                        "content": item.value.get("content", ""),
                        "source": item.value.get("source", ""),
                        "created_at": item.value.get("created_at")
                    })
            
            return knowledge
        except Exception as e:
            logger.warning(f"[LongTermMemory] Failed to get knowledge: {e}")
            return []
    
    # ==================== CONTEXT HELPERS ====================
    
    def get_memory_context(self) -> str:
        """
        Get a formatted summary of long-term memories for agent context.
        
        Returns:
            Formatted string with preferences and relevant facts
        """
        context_parts = []
        
        # Add preferences
        preferences = self.get_all_preferences()
        if preferences:
            context_parts.append("### User Preferences:")
            for key, value in preferences.items():
                context_parts.append(f"- {key}: {value}")
        
        # Add recent facts
        facts = self.get_facts(limit=5)
        if facts:
            context_parts.append("\n### Known Facts:")
            for fact in facts:
                context_parts.append(f"- {fact['fact']}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def clear_all(self) -> None:
        """
        Clear all long-term memory (use with caution).
        
        This deletes all preferences, facts, and knowledge.
        """
        try:
            # Clear preferences
            for item in self.store.search(NAMESPACE_PREFERENCES):
                self.store.delete(namespace=NAMESPACE_PREFERENCES, key=item.key)
            
            # Clear facts
            for item in self.store.search(NAMESPACE_FACTS):
                self.store.delete(namespace=NAMESPACE_FACTS, key=item.key)
            
            # Clear knowledge
            for item in self.store.search(NAMESPACE_KNOWLEDGE):
                self.store.delete(namespace=NAMESPACE_KNOWLEDGE, key=item.key)
            
            logger.info("[LongTermMemory] All memory cleared")
        except Exception as e:
            logger.error(f"[LongTermMemory] Failed to clear memory: {e}")
            raise
