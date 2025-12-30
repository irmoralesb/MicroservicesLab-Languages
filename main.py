"""
Main FastAPI application.
"""
from fastapi import FastAPI
from routers import translate
from dotenv import load_dotenv
from databases import models
from databases.database import engine
import logging
import logging

load_dotenv()


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create tables - use checkfirst=False to avoid precision error with table existence check
# This will attempt to create tables even if they exist, but SQL Server will handle duplicates gracefully
try:
    models.Base.metadata.create_all(engine, checkfirst=False)
except Exception as e:
    # If checkfirst=False fails, try with checkfirst=True and catch the specific error
    logger.warning(f"Table creation with checkfirst=False failed: {e}")
    try:
        models.Base.metadata.create_all(engine, checkfirst=True)
    except Exception as e2:
        logger.error(f"Table creation failed: {e2}")
        # Continue anyway - tables might already exist
        pass

app = FastAPI(
    title="MicroservicesLab-Languages API",
    description="Services to Enable Learning Language",
    version="1.0.0"
)

# Include routers
app.include_router(translate.router)


@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {"message": "Welcome to MicroservicesLab-Languages API"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}
