from fastapi import APIRouter
import os

METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
METRICS_ENDPOINT = os.getenv("METRICS_ENDPOINT", "/metrics")

router = APIRouter(
    prefix="/api/v1",
    tags=["health"]
)


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    health_data = {"status": "healthy"}
    if METRICS_ENABLED:
        health_data["metrics_enabled"] = True
        health_data["metrics_endpoint"] = METRICS_ENDPOINT
    return health_data