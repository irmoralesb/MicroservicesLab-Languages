"""
Main FastAPI application.
"""
from fastapi import FastAPI
from routers import translate, router2
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="MicroservicesLab-Languages API",
    description="Services to Enable Learning Language",
    version="1.0.0"
)

# Include routers
app.include_router(translate.router)
app.include_router(router2.router)


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
