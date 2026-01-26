"""
Database connection management using SQLAlchemy.

Provides:
- Engine creation with connection pooling
- Session factory
- Context managers for safe transactions
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from backend.settings import Settings
import logging

logger = logging.getLogger(__name__)

# Global engine instance (singleton)
_engine = None
_SessionLocal = None


def get_engine():
    """
    Get or create SQLAlchemy engine.
    
    Uses connection pooling for better performance.
    
    Returns:
        SQLAlchemy engine instance
    """
    global _engine

    print(Settings.DATABASE_URL)
    
    if _engine is None:
        try:
            logger.info(f"[Database] Creating engine for {Settings.DB_NAME}")
            
            _engine = create_engine(
                Settings.DATABASE_URL,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connections before using
                echo=False,  # Set to True for SQL query logging
            )
            
            # Test connection
            with _engine.connect() as conn:
                logger.info("[Database] Connection successful")
            
        except Exception as e:
            logger.error(f"[Database] Failed to create engine: {e}")
            raise
    
    return _engine


def get_session_factory():
    """
    Get or create session factory.
    
    Returns:
        SQLAlchemy sessionmaker
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        logger.info("[Database] Session factory created")
    
    return _SessionLocal


def get_session() -> Session:
    """
    Get a new database session.
    
    Usage:
        session = get_session()
        try:
            # Do work
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
    
    Returns:
        SQLAlchemy Session instance
    """
    SessionLocal = get_session_factory()
    return SessionLocal()


@contextmanager
def session_scope():
    """
    Provide a transactional scope for database operations.
    
    Usage:
        with session_scope() as session:
            result = session.query(Orders).all()
    
    Automatically commits on success, rolls back on error.
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"[Database] Transaction failed: {e}")
        raise
    finally:
        session.close()


# Optional: Add event listeners for debugging
# if Settings.DEBUG:
#     @event.listens_for(get_engine(), "connect")
#     def receive_connect(dbapi_conn, connection_record):
#         logger.debug("[Database] New connection established")