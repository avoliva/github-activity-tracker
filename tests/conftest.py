from typing import Dict, List
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.github import GitHubEvent
from app.repositories.github_repository import GitHubRepository
from app.services.github_service import GitHubService
from app.utils.cache import TTLCache


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    """Fixture providing mocked httpx.AsyncClient."""
    return AsyncMock()


@pytest.fixture
def mock_cache() -> TTLCache[List[GitHubEvent]]:
    """Fixture providing cache instance for testing."""
    return TTLCache(ttl_seconds=60, max_size=100)


@pytest.fixture
def mock_github_repository(
    mock_httpx_client: AsyncMock, mock_cache: TTLCache[List[GitHubEvent]]
) -> GitHubRepository:
    """Fixture providing GitHub repository instance."""
    return GitHubRepository(
        client=mock_httpx_client, cache=mock_cache, base_url="https://api.github.com", timeout=30
    )


@pytest.fixture
def mock_github_service(mock_github_repository: GitHubRepository) -> GitHubService:
    """Fixture providing GitHub service instance."""
    return GitHubService(repository=mock_github_repository)


@pytest.fixture
def sample_github_events() -> List[Dict]:
    """Fixture providing sample GitHub event data."""
    return [
        {
            "id": 12345678,
            "type": "PushEvent",
            "actor": {"login": "ge0ffrey", "id": 12345},
            "repo": {
                "id": 67890,
                "name": "ge0ffrey/test-repo",  # GitHub API format: "owner/repo-name"
                "url": "https://api.github.com/repos/ge0ffrey/test-repo",
            },
            "created_at": "2026-01-15T10:30:00Z",
        },
        {
            "id": 12345679,
            "type": "PullRequestEvent",
            "actor": {"login": "ge0ffrey", "id": 12345},
            "repo": {
                "id": 67891,
                "name": "otheruser/other-repo",  # GitHub API format: "owner/repo-name"
                "url": "https://api.github.com/repos/otheruser/other-repo",
            },
            "created_at": "2026-01-14T15:20:00Z",
        },
        {
            "id": 12345680,
            "type": "PushEvent",
            "actor": {"login": "ge0ffrey", "id": 12345},
            "repo": {
                "id": 67890,
                "name": "ge0ffrey/test-repo",  # GitHub API format: "owner/repo-name"
                "url": "https://api.github.com/repos/ge0ffrey/test-repo",
            },
            "created_at": "2026-01-13T08:15:00Z",
        },
    ]


@pytest.fixture
def test_client() -> TestClient:
    """Fixture providing FastAPI test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_app() -> FastAPI:
    """Fixture providing FastAPI app for dependency overrides."""
    return create_app()
