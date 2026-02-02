from unittest.mock import AsyncMock

import pytest

from app.exceptions import RateLimitError, UserNotFoundError
from app.repositories.github_repository import GitHubRepository


class TestGitHubRepository:
    """Unit tests for GitHubRepository."""

    @pytest.mark.asyncio
    async def test_get_user_events_success(self, mock_github_repository: GitHubRepository) -> None:
        """Test successful event retrieval from API."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: [
            {
                "id": 123,
                "type": "PushEvent",
                "actor": {"login": "testuser", "id": 1},
                "repo": {
                    "id": 1,
                    "name": "testuser/repo",  # GitHub API format: "owner/repo-name"
                    "url": "https://api.github.com/repos/testuser/repo",
                },
                "created_at": "2026-01-01T00:00:00Z",
            }
        ]
        mock_response.raise_for_status = lambda: None

        mock_github_repository.client.get = AsyncMock(return_value=mock_response)

        events = await mock_github_repository.get_user_events("testuser")

        assert len(events) == 1
        assert events[0].type == "PushEvent"
        assert events[0].actor.login == "testuser"

        # Verify API was called with correct URL
        mock_github_repository.client.get.assert_called_once()
        call_args = mock_github_repository.client.get.call_args
        assert call_args[0][0] == "https://api.github.com/users/testuser/events"

        # Verify cache was set
        cache_key = mock_github_repository._get_cache_key("testuser")
        cached_events = mock_github_repository.cache.get(cache_key)
        assert cached_events is not None
        assert len(cached_events) == 1

    @pytest.mark.asyncio
    async def test_get_user_events_cached(self, mock_github_repository: GitHubRepository) -> None:
        """Test cache hit scenario returns cached events."""
        # First call populates cache
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: [
            {
                "id": 123,
                "type": "PushEvent",
                "actor": {"login": "testuser", "id": 1},
                "repo": {
                    "id": 1,
                    "name": "testuser/repo",  # GitHub API format: "owner/repo-name"
                    "url": "https://api.github.com/repos/testuser/repo",
                },
                "created_at": "2026-01-01T00:00:00Z",
            }
        ]
        mock_response.raise_for_status = lambda: None
        mock_github_repository.client.get = AsyncMock(return_value=mock_response)

        events1 = await mock_github_repository.get_user_events("testuser")
        assert len(events1) == 1

        # Second call should use cache
        mock_github_repository.client.get.reset_mock()
        events2 = await mock_github_repository.get_user_events("testuser")

        assert len(events2) == 1
        assert events2[0].type == "PushEvent"
        mock_github_repository.client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_events_not_found(
        self, mock_github_repository: GitHubRepository
    ) -> None:
        """Test user not found error handling."""
        mock_response = AsyncMock()
        mock_response.status_code = 404

        mock_github_repository.client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(UserNotFoundError) as exc_info:
            await mock_github_repository.get_user_events("nonexistent")

        assert exc_info.value.username == "nonexistent"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_user_events_rate_limit(
        self, mock_github_repository: GitHubRepository
    ) -> None:
        """Test rate limit error handling."""
        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}

        mock_github_repository.client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(RateLimitError) as exc_info:
            await mock_github_repository.get_user_events("testuser")

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 60

    def test_get_cache_key(self, mock_github_repository: GitHubRepository) -> None:
        """Test cache key generation."""
        cache_key = mock_github_repository._get_cache_key("testuser")

        assert cache_key == "github_events:testuser"
