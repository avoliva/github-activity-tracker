from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.core.dependencies import get_github_service
from app.main import create_app
from app.models.schemas import ActivityType, RepositoryActivity, UserActivityResponse


class TestActivityAPI:
    """Integration tests for activity API endpoints."""

    def test_get_user_activity_endpoint(self) -> None:
        """Test GET /api/v1/users/{username}/activity endpoint."""
        mock_response = UserActivityResponse(
            username="ge0ffrey",
            repositories=[
                RepositoryActivity(
                    repository_name="ge0ffrey/test-repo",
                    is_owner=True,
                    top_activity_types=[ActivityType(type="PushEvent", count=2)],
                )
            ],
            total_repositories=1,
            total_events=3,
        )

        mock_service = AsyncMock()
        mock_service.analyze_user_activity = AsyncMock(return_value=mock_response)

        app = create_app()
        app.dependency_overrides[get_github_service] = lambda: mock_service

        client = TestClient(app)
        response = client.get("/api/v1/users/ge0ffrey/activity")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "ge0ffrey"
        assert "repositories" in data

        app.dependency_overrides.clear()

    def test_get_user_activity_invalid_username(self) -> None:
        """Test endpoint with invalid username returns 404."""
        from app.exceptions import UserNotFoundError

        mock_service = AsyncMock()
        mock_service.analyze_user_activity = AsyncMock(side_effect=UserNotFoundError("nonexistent"))

        app = create_app()
        app.dependency_overrides[get_github_service] = lambda: mock_service

        client = TestClient(app)
        response = client.get("/api/v1/users/nonexistent/activity")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        app.dependency_overrides.clear()

    def test_get_user_activity_response_structure(self) -> None:
        """Test response structure validation."""
        mock_response = UserActivityResponse(
            username="testuser", repositories=[], total_repositories=0, total_events=0
        )

        mock_service = AsyncMock()
        mock_service.analyze_user_activity = AsyncMock(return_value=mock_response)

        app = create_app()
        app.dependency_overrides[get_github_service] = lambda: mock_service

        client = TestClient(app)
        response = client.get("/api/v1/users/testuser/activity")

        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "repositories" in data
        assert "total_repositories" in data
        assert "total_events" in data
        assert isinstance(data["repositories"], list)

        app.dependency_overrides.clear()

    def test_get_user_activity_empty_response(self) -> None:
        """Test endpoint with user having no events."""
        mock_response = UserActivityResponse(
            username="emptyuser", repositories=[], total_repositories=0, total_events=0
        )

        mock_service = AsyncMock()
        mock_service.analyze_user_activity = AsyncMock(return_value=mock_response)

        app = create_app()
        app.dependency_overrides[get_github_service] = lambda: mock_service

        client = TestClient(app)
        response = client.get("/api/v1/users/emptyuser/activity")

        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 0
        assert data["total_repositories"] == 0
        assert len(data["repositories"]) == 0

        app.dependency_overrides.clear()

    def test_get_user_activity_rate_limit(self) -> None:
        """Test endpoint with rate limit error returns 429."""
        from app.exceptions import RateLimitError

        mock_service = AsyncMock()
        mock_service.analyze_user_activity = AsyncMock(side_effect=RateLimitError(retry_after=60))

        app = create_app()
        app.dependency_overrides[get_github_service] = lambda: mock_service

        client = TestClient(app)
        response = client.get("/api/v1/users/testuser/activity")

        assert response.status_code == 429
        data = response.json()
        assert "rate limit" in data["detail"].lower()
        assert "60" in data["detail"]  # Retry-After value

        app.dependency_overrides.clear()

    def test_get_user_activity_api_error(self) -> None:
        """Test endpoint with generic GitHub API error."""
        from app.exceptions import GitHubAPIError

        mock_service = AsyncMock()
        mock_service.analyze_user_activity = AsyncMock(
            side_effect=GitHubAPIError("API error occurred", status_code=500)
        )

        app = create_app()
        app.dependency_overrides[get_github_service] = lambda: mock_service

        client = TestClient(app)
        response = client.get("/api/v1/users/testuser/activity")

        assert response.status_code == 500
        data = response.json()
        assert "API error" in data["detail"]

        app.dependency_overrides.clear()
