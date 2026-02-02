from unittest.mock import AsyncMock

import pytest

from app.models.github import GitHubActor, GitHubEvent, GitHubRepositoryResponse
from app.services.github_service import GitHubService


class TestGitHubService:
    """Unit tests for GitHubService."""

    @pytest.mark.asyncio
    async def test_analyze_user_activity_success(
        self, mock_github_service: GitHubService, sample_github_events: list
    ) -> None:
        """Test successful user activity analysis."""
        from app.models.github import GitHubEvent

        events = [GitHubEvent(**event) for event in sample_github_events]
        mock_github_service.repository.get_user_events = AsyncMock(return_value=events)

        result = await mock_github_service.analyze_user_activity("ge0ffrey")

        assert result.username == "ge0ffrey"
        assert result.total_events == 3
        assert result.total_repositories == 2
        assert len(result.repositories) == 2

        # Verify repository details
        repo_names = {repo.repository_name for repo in result.repositories}
        assert repo_names == {"ge0ffrey/test-repo", "otheruser/other-repo"}

        # Verify ge0ffrey/test-repo details
        test_repo = next(
            r for r in result.repositories if r.repository_name == "ge0ffrey/test-repo"
        )
        assert test_repo.is_owner is True
        assert len(test_repo.top_activity_types) == 1
        assert test_repo.top_activity_types[0].type == "PushEvent"
        assert test_repo.top_activity_types[0].count == 2

        # Verify otheruser/other-repo details
        other_repo = next(
            r for r in result.repositories if r.repository_name == "otheruser/other-repo"
        )
        assert other_repo.is_owner is False
        assert len(other_repo.top_activity_types) == 1
        assert other_repo.top_activity_types[0].type == "PullRequestEvent"
        assert other_repo.top_activity_types[0].count == 1

    def test_group_events_by_repository(self, mock_github_service: GitHubService) -> None:
        """Test event grouping by repository."""
        actor = GitHubActor(login="testuser", id=1)
        repo1 = GitHubRepositoryResponse(
            id=1,
            name="testuser/repo1",  # GitHub API format: "owner/repo-name"
            url="https://api.github.com/repos/testuser/repo1",
        )
        repo2 = GitHubRepositoryResponse(
            id=2,
            name="testuser/repo2",  # GitHub API format: "owner/repo-name"
            url="https://api.github.com/repos/testuser/repo2",
        )

        events = [
            GitHubEvent(
                id=1, type="PushEvent", actor=actor, repo=repo1, created_at="2026-01-01T00:00:00Z"
            ),
            GitHubEvent(
                id=2,
                type="PullRequestEvent",
                actor=actor,
                repo=repo1,
                created_at="2026-01-01T00:00:00Z",
            ),
            GitHubEvent(
                id=3, type="PushEvent", actor=actor, repo=repo2, created_at="2026-01-01T00:00:00Z"
            ),
        ]

        result = mock_github_service._group_events_by_repository(events)

        assert len(result) == 2
        assert len(result["testuser/repo1"]) == 2
        assert len(result["testuser/repo2"]) == 1

    def test_get_top_activity_types(self, mock_github_service: GitHubService) -> None:
        """Test top activity type calculation."""
        actor = GitHubActor(login="testuser", id=1)
        repo = GitHubRepositoryResponse(
            id=1,
            name="testuser/repo",  # GitHub API format: "owner/repo-name"
            url="https://api.github.com/repos/testuser/repo",
        )

        events = [
            GitHubEvent(
                id=1, type="PushEvent", actor=actor, repo=repo, created_at="2026-01-01T00:00:00Z"
            ),
            GitHubEvent(
                id=2, type="PushEvent", actor=actor, repo=repo, created_at="2026-01-01T00:00:00Z"
            ),
            GitHubEvent(
                id=3,
                type="PullRequestEvent",
                actor=actor,
                repo=repo,
                created_at="2026-01-01T00:00:00Z",
            ),
            GitHubEvent(
                id=4,
                type="IssueCommentEvent",
                actor=actor,
                repo=repo,
                created_at="2026-01-01T00:00:00Z",
            ),
        ]

        result = mock_github_service._get_top_activity_types(events, top_n=3)

        assert len(result) == 3
        assert result[0].type == "PushEvent"
        assert result[0].count == 2
        assert result[1].type == "PullRequestEvent"
        assert result[1].count == 1

    def test_get_top_activity_types_empty_list(self, mock_github_service: GitHubService) -> None:
        """Test top activity types with empty event list."""
        result = mock_github_service._get_top_activity_types([], top_n=3)

        assert result == []

    def test_is_repository_owner_true(self, mock_github_service: GitHubService) -> None:
        """Test repository ownership detection when user owns repo."""
        repo = GitHubRepositoryResponse(
            id=1,
            name="testuser/repo",  # GitHub API format: "owner/repo-name"
            url="https://api.github.com/repos/testuser/repo",
        )

        result = mock_github_service._is_repository_owner(repo, "testuser")

        assert result is True

    def test_is_repository_owner_false(self, mock_github_service: GitHubService) -> None:
        """Test repository ownership detection when user does not own repo."""
        repo = GitHubRepositoryResponse(
            id=1,
            name="otheruser/repo",  # GitHub API format: "owner/repo-name"
            url="https://api.github.com/repos/otheruser/repo",
        )

        result = mock_github_service._is_repository_owner(repo, "testuser")

        assert result is False

    def test_is_repository_owner_case_insensitive(self, mock_github_service: GitHubService) -> None:
        """Test repository ownership detection is case-insensitive."""
        repo = GitHubRepositoryResponse(
            id=1,
            name="TestUser/repo",  # GitHub API format: "owner/repo-name"
            url="https://api.github.com/repos/TestUser/repo",
        )

        result = mock_github_service._is_repository_owner(repo, "testuser")

        assert result is True
