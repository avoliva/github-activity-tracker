"""FastAPI dependency injection functions."""

from typing import List, Optional

from fastapi import Depends, Request

from app.core.config import get_settings
from app.models.github import GitHubEvent
from app.repositories.github_repository import GitHubRepository
from app.services.github_service import GitHubService
from app.utils.cache import TTLCache

# Module-level cache instance (singleton pattern)
_cache_instance: Optional[TTLCache[List[GitHubEvent]]] = None


def get_cache() -> TTLCache[List[GitHubEvent]]:
    """Get singleton cache instance configured from settings.

    Returns:
        TTLCache instance (created on first call, reused afterwards)

    """
    global _cache_instance
    if _cache_instance is None:
        settings = get_settings()
        _cache_instance = TTLCache(
            ttl_seconds=settings.cache_ttl_seconds, max_size=settings.cache_max_size
        )
    return _cache_instance


def get_github_repository(request: Request) -> GitHubRepository:
    """Get GitHub repository instance for dependency injection.

    Creates and returns a GitHubRepository instance using the shared HTTP client
    from app state and cache. This function is used as a FastAPI dependency.

    Args:
        request: FastAPI Request object to access app state

    Returns:
        GitHubRepository instance configured with HTTP client and cache

    Raises:
        RuntimeError: If HTTP client is not initialized in app state

    """
    if not hasattr(request.app.state, "http_client"):
        raise RuntimeError(
            "HTTP client not initialized. Ensure application lifespan has completed startup."
        )
    client = request.app.state.http_client
    settings = get_settings()
    cache = get_cache()
    return GitHubRepository(
        client=client,
        cache=cache,
        base_url=settings.github_api_base_url,
        timeout=settings.request_timeout_seconds,
    )


def get_github_service(
    repository: GitHubRepository = Depends(get_github_repository),
) -> GitHubService:
    """Create GitHubService instance with injected repository.

    Args:
        repository: GitHubRepository instance (injected via Depends)

    Returns:
        New GitHubService instance

    """
    return GitHubService(repository=repository)
