import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("SQLALCHEMY_DATABASE_URL environment variable is required")

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
    use_setinputsizes=False  # Fixes pyodbc precision error with NVARCHAR - must be at engine level, not in connect_args
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()