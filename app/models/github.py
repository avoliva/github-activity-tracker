"""Pydantic models for GitHub API data structures."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class GitHubActor(BaseModel):
    """GitHub actor (user) model."""

    login: str
    id: int


class GitHubRepositoryResponse(BaseModel):
    """GitHub repository response model.

    Note: In GitHub Events API, the repo object only contains id, name, and url.
    The name field contains the full repository name in "owner/repo-name" format.
    """

    id: int
    name: str  # Contains "owner/repo-name" format
    url: str

    @property
    def full_name(self) -> str:
        """Return repository name (same as name field, for API consistency)."""
        return self.name

    @property
    def owner(self) -> GitHubActor:
        """Extract owner login from name field (format: "owner/repo-name").

        Returns:
            GitHubActor with parsed login (id=0 placeholder, not from API)

        """
        # Parse owner from "owner/repo-name" format
        owner_login = self.name.split("/")[0] if "/" in self.name else ""
        # We don't have owner ID from events API, so use a placeholder
        # This is acceptable since we only use owner.login for comparison
        return GitHubActor(login=owner_login, id=0)


class GitHubEvent(BaseModel):
    """GitHub event model."""

    id: int  # GitHub API returns integer IDs for events
    type: str = Field(..., description="Event type (e.g., PushEvent, PullRequestEvent)")
    actor: GitHubActor
    repo: GitHubRepositoryResponse
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_created_at(cls, v: str) -> datetime:
        """Parse created_at string to datetime object.

        Converts ISO format datetime string from GitHub API to Python datetime.
        Handles 'Z' timezone indicator by converting to UTC offset.

        Args:
            v: ISO format datetime string (e.g., "2026-01-15T10:30:00Z")

        Returns:
            Parsed datetime object with timezone information

        """
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
