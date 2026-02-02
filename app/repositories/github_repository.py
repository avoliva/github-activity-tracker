from typing import List

import httpx

from app.exceptions import GitHubAPIError, RateLimitError, UserNotFoundError
from app.models.github import GitHubEvent
from app.utils.cache import TTLCache


class GitHubRepository:
    """Repository pattern for GitHub API access."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        cache: TTLCache[List[GitHubEvent]],
        base_url: str,
        timeout: int,
    ) -> None:
        """Initialize repository with dependencies.

        Args:
            client: HTTP client for API calls
            cache: Cache instance for API responses
            base_url: GitHub API base URL
            timeout: Request timeout in seconds

        """
        self.client = client
        self.cache = cache
        self.base_url = base_url
        self.timeout = timeout

    async def get_user_events(self, username: str) -> List[GitHubEvent]:
        """Fetch user events from GitHub API with caching.

        Args:
            username: GitHub username

        Returns:
            List of user events

        Raises:
            UserNotFoundError: If user not found
            RateLimitError: If rate limit exceeded
            GitHubAPIError: For other API errors

        """
        cache_key = self._get_cache_key(username)
        cached_events = self.cache.get(cache_key)
        if cached_events is not None:
            return cached_events

        events = await self._fetch_from_api(username)
        self.cache.set(cache_key, events)
        return events

    async def _fetch_from_api(self, username: str) -> List[GitHubEvent]:
        """Make actual API call to GitHub.

        Args:
            username: GitHub username

        Returns:
            List of events from API

        Raises:
            UserNotFoundError: If user not found
            RateLimitError: If rate limit exceeded
            GitHubAPIError: For other API errors

        """
        url = f"{self.base_url}/users/{username}/events"
        try:
            response = await self.client.get(url, timeout=self.timeout)
            if response.status_code == 404:
                raise UserNotFoundError(username)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 0))
                raise RateLimitError(retry_after=retry_after)
            response.raise_for_status()
            events_data = response.json()
            return [GitHubEvent(**event) for event in events_data]
        except httpx.HTTPStatusError as e:
            raise GitHubAPIError(f"GitHub API error: {e}", status_code=e.response.status_code)
        except httpx.RequestError as e:
            raise GitHubAPIError(f"Request error: {e}")

    def _get_cache_key(self, username: str) -> str:
        """Generate cache key for username.

        Args:
            username: GitHub username

        Returns:
            Cache key string

        """
        return f"github_events:{username}"
