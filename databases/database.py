from monitoring.metrics import database_connections_activating, database_connections_deactivating
from contextlib import contextmanager
import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import logging

logger = logging.getLogger(__name__)

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError(
        "SQLALCHEMY_DATABASE_URL environment variable is required")

SQLALCHEMY_DATABASE_MIGRATION_URL = os.getenv(
    "SQLALCHEMY_DATABASE_MIGRATION_URL")
if not SQLALCHEMY_DATABASE_MIGRATION_URL:
    raise RuntimeError(
        "SQLALCHEMY_DATABASE_MIGRATION_URL environment variable is required")

# Add LongAsMax=Yes to connection string to fix NVARCHAR(max) precision error
# This works with ODBC Driver 18+ for SQL Server
parsed = urlparse(SQLALCHEMY_DATABASE_URL)
query_params = parse_qs(parsed.query)
if 'LongAsMax' not in query_params:
    query_params['LongAsMax'] = ['Yes']
# Also ensure use_setinputsizes is handled via connect_args
parsed = parsed._replace(query=urlencode(query_params, doseq=True))
SQLALCHEMY_DATABASE_URL = urlunparse(parsed)

# For SQL Server, the URL should look like:
# mssql+pyodbc://user:password@server:port/database?driver=SQL+Server
# For newer ODBC drivers: mssql+pyodbc://user:password@server:port/database?driver=ODBC+Driver+17+for+SQL+Server
# For local Docker/development, you may need: ?driver=SQL+Server&TrustServerCertificate=yes
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "timeout": 30,
        "fast_executemany": False  # Disable fast_executemany to avoid precision errors
    },
    # Fixes pyodbc precision error with NVARCHAR - must be at engine level, not in connect_args
    use_setinputsizes=False
)

# Optional: Monitor connection pool events for advanced metrics
# @event.listens_for(Pool, "connect")
# def receive_connect(dbapi_conn, connection_record):
#     """Track when connections are created in the pool."""
#     logger.debug("New database connection created")
#     from monitoring.metrics import database_connections_active
#     database_connections_active.inc()
#
# @event.listens_for(Pool, "close")
# def receive_close(dbapi_conn, connection_record):
#     """Track when connections are closed."""
#     logger.debug("Database connection closed")
#     from monitoring.metrics import database_connections_active
#     database_connections_active.dec()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# Database connection monitoring with context manager


@contextmanager
def get_monitored_db_session():
    """
    Context manager for database sessions with connection monitoring.
    Usage in routers:

    def get_db():
        with get_monitored_db_session() as db:
            yield db
    """
    database_connections_activating()
    session = SessionLocal()
    try:
        yield session
        if session.new or session.dirty or session.deleted:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        database_connections_deactivating()
