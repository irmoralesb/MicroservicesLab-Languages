"""
Second router module for different functionality.
"""
from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1/router2",
    tags=["router2"]
)


@router.get("/endpoint")
async def router2_endpoint():
    """
    Empty endpoint for router2 functionality.
    """
    return {"message": "Router2 endpoint"}

