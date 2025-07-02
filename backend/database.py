"""
Database connection and session management with security features
"""
import logging
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlmodel import SQLModel

from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Convert the database URL to use the correct format
def get_database_url(url):
    """Convert postgres:// to postgresql:// if needed"""
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url

# Create sync engine with security configurations
db_url = get_database_url(settings.database_url)

# Configure engine based on database type
if db_url.startswith('sqlite'):
    # SQLite specific configuration
    engine = create_engine(
        db_url,
        echo=settings.environment == "development",
        connect_args={"check_same_thread": False}  # Allow multi-threading for SQLite
    )
else:
    # PostgreSQL specific configuration
    engine = create_engine(
        db_url,
        echo=settings.environment == "development",
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=3600,   # Recycle connections every hour
        pool_size=10,        # Connection pool size
        max_overflow=20,     # Maximum overflow connections
        connect_args={
            "sslmode": "require" if settings.environment == "production" else "prefer",
            "application_name": "supportops-automator",
            "connect_timeout": 10,
            # "command_timeout": 30,  # Removed - not supported by psycopg2 (only by asyncpg)
        }
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=True,
    bind=engine
)


def create_db_and_tables():
    """Create database tables"""
    try:
        # Import all models to ensure they're registered
        from models import (
            User, Rule, AuditLog, Integration, IntegrationCredential
        )
        
        # Create all tables
        SQLModel.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_session() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction error: {e}")
        raise
    finally:
        session.close()


def health_check() -> bool:
    """
    Check database connectivity
    """
    try:
        with get_db_session() as session:
            # Simple query to test connection
            result = session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def close_db():
    """
    Close database connections
    """
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Database initialization
def init_database():
    """
    Initialize database with default data
    """
    try:
        # Create tables
        create_db_and_tables()
        
        # Create default admin user if not exists
        with get_db_session() as session:
            from models.user import User, UserRole, get_password_hash
            from sqlalchemy import select
            
            # Check if admin user exists
            result = session.execute(
                select(User).where(User.role == UserRole.ADMIN)
            )
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                # Create default admin user
                admin_user = User(
                    email="admin@supportops.local",
                    username="admin",
                    hashed_password=get_password_hash("admin123!"),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                    first_name="System",
                    last_name="Administrator"
                )
                session.add(admin_user)
                # No need to explicitly commit as get_db_session will do it
                logger.info("Default admin user created")
            
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

