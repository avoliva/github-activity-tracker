"""Business logic for analyzing GitHub user activity."""

from collections import Counter, defaultdict
from typing import Dict, List

from app.models.github import GitHubEvent, GitHubRepositoryResponse
from app.models.schemas import ActivityType, RepositoryActivity, UserActivityResponse
from app.repositories.github_repository import GitHubRepository


class GitHubService:
    """Business logic for GitHub activity analysis."""

    def __init__(self, repository: GitHubRepository) -> None:
        """Initialize service with repository dependency.

        Args:
            repository: GitHub repository instance

        """
        self.repository = repository

    async def analyze_user_activity(self, username: str) -> UserActivityResponse:
        """Analyze user activity: groups events by repo, calculates top 3 activity types.

        Also flags owned repos.

        Args:
            username: GitHub username to analyze

        Returns:
            UserActivityResponse with repositories, activity types, and ownership flags

        """
        events = await self.repository.get_user_events(username)
        repo_groups = self._group_events_by_repository(events)

        repositories = []
        for repo_name, repo_events in repo_groups.items():
            top_activities = self._get_top_activity_types(repo_events, top_n=3)
            repo_model = repo_events[0].repo
            is_owner = self._is_repository_owner(repo_model, username)

            repositories.append(
                RepositoryActivity(
                    repository_name=repo_name, is_owner=is_owner, top_activity_types=top_activities
                )
            )

        return UserActivityResponse(
            username=username,
            repositories=repositories,
            total_repositories=len(repositories),
            total_events=len(events),
        )

    def _group_events_by_repository(
        self, events: List[GitHubEvent]
    ) -> Dict[str, List[GitHubEvent]]:
        """Group events by repository.

        Args:
            events: List of GitHub events

        Returns:
            Events grouped by repository name

        """
        repo_groups = defaultdict(list)
        for event in events:
            repo_groups[event.repo.full_name].append(event)
        return dict(repo_groups)

    def _get_top_activity_types(
        self, events: List[GitHubEvent], top_n: int = 3
    ) -> List[ActivityType]:
        """Calculate top activity types from events.

        Args:
            events: List of events to analyze
            top_n: Number of top activities to return

        Returns:
            Top N activity types with counts

        """
        if not events:
            return []

        counter = Counter(event.type for event in events)
        top_types = counter.most_common(top_n)

        return [ActivityType(type=activity_type, count=count) for activity_type, count in top_types]

    def _is_repository_owner(self, repo: GitHubRepositoryResponse, username: str) -> bool:
        """Check if user owns repository.

        Args:
            repo: Repository to check
            username: Username to check ownership

        Returns:
            True if user owns repository

        """
        return repo.owner.login.lower() == username.lower()
