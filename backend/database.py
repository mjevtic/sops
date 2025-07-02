"""
Database connection and session management with security features
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Fix database URL for async connections
def fix_database_url(url):
    """Fix database URL for async connections
    1. Convert postgres:// to postgresql:// if needed
    2. Ensure the URL uses the asyncpg driver
    """
    # Step 1: Fix postgres:// to postgresql://
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    
    # Step 2: Add driver name if not present
    if '?driver=' not in url and '+' not in url:
        if '?' in url:
            url = url.replace('?', '?driver=asyncpg&', 1)
        else:
            url = url + '?driver=asyncpg'
    
    return url

# Create async engine with security configurations
engine = create_async_engine(
    fix_database_url(settings.database_url),
    echo=settings.environment == "development",
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections every hour
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Maximum overflow connections
    connect_args={
        "sslmode": "require" if settings.environment == "production" else "prefer",
        "application_name": "supportops-automator",
        "connect_timeout": 10,
        "command_timeout": 30,
    }
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)


async def create_db_and_tables():
    """Create database tables"""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from models import (
                User, Rule, AuditLog, Integration, IntegrationCredential
            )
            
            # Create all tables
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database transaction error: {e}")
            raise
        finally:
            await session.close()


async def health_check() -> bool:
    """
    Check database connectivity
    """
    try:
        async with get_db_session() as session:
            # Simple query to test connection
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def close_db():
    """
    Close database connections
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Database initialization
async def init_database():
    """
    Initialize database with default data
    """
    try:
        # Create tables
        await create_db_and_tables()
        
        # Create default admin user if not exists
        async with get_db_session() as session:
            from models.user import User, UserRole, get_password_hash
            from sqlalchemy import select
            
            # Check if admin user exists
            result = await session.execute(
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
                await session.commit()
                logger.info("Default admin user created")
            
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

