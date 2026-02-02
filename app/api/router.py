"""API router module for aggregating all API routes."""

from fastapi import APIRouter

from app.api.routes import activity


def create_api_router() -> APIRouter:
    """Create API router with activity routes under /api/v1 prefix.

    Returns:
        APIRouter configured with /api/v1 prefix and 'activity' tag

    """
    api_router = APIRouter()
    api_router.include_router(activity.router, prefix="/api/v1", tags=["activity"])
    return api_router
