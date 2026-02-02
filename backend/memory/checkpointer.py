"""
PostgreSQL Checkpointer for Short-Term Memory

Provides a simple checkpointer that stores conversation history in PostgreSQL.
Limits storage to the last 10 messages for efficient memory management.
Uses SQLAlchemy session from the database module for consistency.

Since there's only one session in this project, we use a fixed thread_id.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy import text

from backend.database.connection import session_scope, get_engine
from backend.database.models import ConversationHistory

logger = logging.getLogger(__name__)

# Fixed thread ID since there's only one conversation session
DEFAULT_THREAD_ID = "main_session"

# Maximum number of conversation entries to keep
MAX_CONVERSATION_HISTORY = 10


class ShortTermMemory:
    """
    Simple short-term memory manager for the agent system.
    
    Stores conversation history (questions and responses) in PostgreSQL,
    limited to the last 10 entries for efficient memory management.
    
    Uses SQLAlchemy session from the database module.
    """
    
    def __init__(self):
        """Initialize the short-term memory with database connection."""
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create the conversation history table if it doesn't exist."""
        try:
            engine = get_engine()
            # Create only the ConversationHistory table if it doesn't exist
            ConversationHistory.__table__.create(engine, checkfirst=True)
            logger.info("[ShortTermMemory] Table 'conversation_history' ensured")
        except Exception as e:
            logger.error(f"[ShortTermMemory] Failed to create table: {e}")
            raise
    
    def save_conversation(
        self,
        question: str,
        response: str,
        intent: str = "",
        agent_outputs: Optional[Dict[str, Any]] = None,
        root_cause: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save a conversation entry to the database.
        
        Automatically trims old entries to keep only the last MAX_CONVERSATION_HISTORY.
        
        Args:
            question: User's question
            response: Agent's synthesized response
            intent: Detected intent
            agent_outputs: Outputs from each agent
            root_cause: Root cause analysis
        """
        try:
            with session_scope() as session:
                # Create new conversation entry
                conversation = ConversationHistory(
                    question=question,
                    response=response,
                    intent=intent,
                    agent_outputs=agent_outputs,
                    root_cause=root_cause,
                    timestamp=datetime.utcnow()
                )
                session.add(conversation)
                session.flush()  # Get the ID
                
                # Trim old entries - keep only last MAX_CONVERSATION_HISTORY
                # Get IDs to keep using raw SQL for subquery compatibility
                session.execute(text(f"""
                    DELETE FROM conversation_history
                    WHERE id NOT IN (
                        SELECT id FROM conversation_history
                        ORDER BY timestamp DESC
                        LIMIT {MAX_CONVERSATION_HISTORY}
                    )
                """))
                
                logger.info(f"[ShortTermMemory] Saved conversation, trimmed to last {MAX_CONVERSATION_HISTORY}")
                
        except Exception as e:
            logger.error(f"[ShortTermMemory] Failed to save conversation: {e}")
            raise
    
    def get_conversation_history(self, limit: int = MAX_CONVERSATION_HISTORY) -> List[Dict[str, Any]]:
        """
        Retrieve recent conversation history.
        
        Args:
            limit: Maximum number of entries to retrieve (default: 10)
            
        Returns:
            List of conversation entries, oldest first
        """
        try:
            with session_scope() as session:
                # Query recent conversations
                conversations = (
                    session.query(ConversationHistory)
                    .order_by(ConversationHistory.timestamp.desc())
                    .limit(limit)
                    .all()
                )
                
                # Convert to list of dicts, reverse to get oldest first
                history = []
                for conv in reversed(conversations):
                    history.append({
                        "id": conv.id,
                        "question": conv.question,
                        "response": conv.response,
                        "intent": conv.intent,
                        "agent_outputs": conv.agent_outputs,
                        "root_cause": conv.root_cause,
                        "timestamp": conv.timestamp.isoformat() if conv.timestamp else None
                    })
                
                logger.info(f"[ShortTermMemory] Retrieved {len(history)} conversation entries")
                return history
                
        except Exception as e:
            logger.error(f"[ShortTermMemory] Failed to get history: {e}")
            return []
    
    def get_context_summary(self) -> str:
        """
        Get a formatted summary of recent conversations for context.
        
        Returns:
            String summary of recent Q&A pairs
        """
        history = self.get_conversation_history(limit=5)  # Last 5 for context
        
        if not history:
            return ""
        
        summary_parts = ["### Recent Conversation History:"]
        for i, entry in enumerate(history, 1):
            summary_parts.append(f"\n**Q{i}:** {entry['question']}")
            if entry['response']:
                # Truncate long responses
                response = entry['response'][:500]
                if len(entry['response']) > 500:
                    response += "..."
                summary_parts.append(f"**A{i}:** {response}")
        
        return "\n".join(summary_parts)
    
    def clear_history(self) -> None:
        """Clear all conversation history."""
        try:
            with session_scope() as session:
                session.query(ConversationHistory).delete()
                logger.info("[ShortTermMemory] Conversation history cleared")
        except Exception as e:
            logger.error(f"[ShortTermMemory] Failed to clear history: {e}")
            raise


def get_config() -> Dict[str, Any]:
    """
    Get the configuration for graph invocation with checkpointer.
    
    Since there's only one session, we use a fixed thread_id.
    
    Returns:
        Config dict with thread_id
    """
    return {
        "configurable": {
            "thread_id": DEFAULT_THREAD_ID
        }
    }
