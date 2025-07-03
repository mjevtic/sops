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
try:
    # First, try to construct URL from individual components (Docker/Coolify style)
    if settings.database_host and settings.database_user and settings.database_password and settings.database_name:
        constructed_url = f"postgresql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port or '5432'}/{settings.database_name}"
        db_url = get_database_url(constructed_url)
        logger.info(f"Using constructed database URL from components")
    # Otherwise use the database_url setting
    elif settings.database_url:
        db_url = get_database_url(settings.database_url)
        logger.info(f"Using database URL from settings")
    else:
        # Fallback to SQLite
        db_url = "sqlite:///./test.db"
        logger.warning(f"No database configuration found, falling back to SQLite database: {db_url}")
    
    # Log sanitized URL (hide credentials)
    if '@' in db_url:
        sanitized_url = db_url.replace(db_url.split('@')[0], '***')
    else:
        sanitized_url = db_url
    logger.info(f"Database URL: {sanitized_url}")
    
except Exception as e:
    logger.error(f"Invalid database URL format: {e}")
    db_url = "sqlite:///./test.db"  # Fallback to SQLite
    logger.warning(f"Falling back to SQLite database: {db_url}")

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


def check_database_connection():
    """
    Check if database connection is working
    Returns True if connection is successful, False otherwise
    """
    try:
        # Try to connect to the database and execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()  # Actually fetch the result to verify connection
            
            # Get database info for diagnostics
            if not db_url.startswith('sqlite'):
                try:
                    db_info = connection.execute(text("SELECT version()")).fetchone()[0]
                    logger.info(f"Connected to database: {db_info}")
                except:
                    pass  # Skip if we can't get version info
            
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        
        # Provide more detailed diagnostics based on error type
        if "could not translate host name" in str(e).lower():
            logger.error(f"DNS resolution error: Could not resolve database hostname. Check network configuration and DNS settings.")
        elif "connection refused" in str(e).lower():
            logger.error(f"Connection refused: Database server is not accepting connections. Check if database is running and accessible.")
        elif "authentication failed" in str(e).lower():
            logger.error(f"Authentication error: Invalid username or password. Check database credentials.")
        
        return False

# Database initialization
def init_database():
    """
    Initialize database with default data
    """
    # First check if database connection is working
    if not check_database_connection():
        logger.warning("Database connection failed, will retry once more")
        # Wait a bit and retry once more
        import time
        time.sleep(5)
        if not check_database_connection():
            logger.error("Database connection failed after retry")
            if not db_url.startswith('sqlite'):
                logger.warning("Falling back to SQLite database")
                global engine, SessionLocal
                engine = create_engine(
                    "sqlite:///./fallback.db",
                    echo=settings.environment == "development",
                    connect_args={"check_same_thread": False}
                )
                SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)
            else:
                logger.error("Already using SQLite, cannot fallback further")
                raise Exception("Database connection failed")
    
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
                try:
                    # Get admin credentials from settings
                    admin_email = settings.admin_email
                    admin_password = settings.admin_password
                except AttributeError:
                    # Fallback to default values if not in settings
                    admin_email = "admin@supportops.local"
                    admin_password = "admin123!"
                    logger.warning(f"Admin credentials not found in settings, using defaults")
                
                admin_user = User(
                    email=admin_email,
                    username="admin",
                    hashed_password=get_password_hash(admin_password),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                    first_name="System",
                    last_name="Administrator"
                )
                session.add(admin_user)
                # No need to explicitly commit as get_db_session will do it
                logger.info(f"Default admin user created with email: {admin_email}")
            
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

