"""
Main FastAPI application.
"""
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from databases import models
from databases.database import engine
from routers import health, prometheus_metrics, translator

load_dotenv()


# Configure logging from environment (default INFO)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
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

# CORS configuration
cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
            env_var_name="METRICS_ENABLED",
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
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
