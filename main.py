"""
Main FastAPI application.
"""
from fastapi import FastAPI
from routers import translator, health, prometheus_metrics
from dotenv import load_dotenv
from databases import models
from databases.database import engine
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import os

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

# Prometheus metrics configuration
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
METRICS_ENDPOINT = os.getenv("METRICS_ENDPOINT", "/metrics")

# Initialize Prometheus instrumentation with configuration
# This automatically tracks HTTP requests, response times, and status codes
if METRICS_ENABLED:
    try:
        instrumentator = Instrumentator(
            should_group_status_codes=True,  # Group 2xx, 3xx, 4xx, 5xx
            should_ignore_untemplated=True,  # Ignore requests without a route
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            # Don't track admin/metrics endpoints
            excluded_handlers=[".*admin.*", "/metrics"],
            env_var_name="ENABLE_METRICS",
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
        )

        # Add custom instrumentation for request/response sizes
        instrumentator.add(
            lambda info: info.request.headers.get("content-length", 0)
        )

        instrumentator.instrument(app).expose(app, endpoint=METRICS_ENDPOINT)
        logger.info(f"Prometheus metrics enabled at {METRICS_ENDPOINT}")
    except Exception as e:
        logger.error(f"Failed to initialize Prometheus metrics: {e}")
else:
    logger.info("Prometheus metrics disabled")

# Include routers
app.include_router(translator.router)
app.include_router(health.router)
app.include_router(prometheus_metrics.router)

@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {"message": "Welcome to MicroservicesLab-Languages API"}
