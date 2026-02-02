from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI

from app.api.router import create_api_router
from app.core.config import get_settings, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan handler: creates HTTP client on startup, closes on shutdown.

    Args:
        app: FastAPI application instance

    """
    # Startup: Create HTTP client
    settings = get_settings()
    client = httpx.AsyncClient(
        timeout=settings.request_timeout_seconds,
        headers={
            "User-Agent": "GitHubActivityTracker/1.0.0",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    app.state.http_client = client

    yield

    # Shutdown: Close HTTP client
    await client.aclose()


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Initializes FastAPI app with settings from configuration,
    registers API routes, and sets up lifespan event handlers.

    Returns:
        Configured FastAPI application instance

    """
    setup_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Register API router
    api_router = create_api_router()
    app.include_router(api_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
