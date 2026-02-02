from typing import List

from pydantic import BaseModel, Field


class ActivityType(BaseModel):
    """Activity type with count."""

    type: str = Field(..., description="Activity type name (e.g., PushEvent)")
    count: int = Field(..., description="Number of occurrences")


class RepositoryActivity(BaseModel):
    """Repository activity summary."""

    repository_name: str = Field(..., description="Full repository name (owner/repo)")
    is_owner: bool = Field(..., description="Whether user owns the repository")
    top_activity_types: List[ActivityType] = Field(
        ..., description="Top 3 activity types", min_length=0, max_length=3
    )


class UserActivityResponse(BaseModel):
    """Complete user activity response."""

    username: str = Field(..., description="GitHub username")
    repositories: List[RepositoryActivity] = Field(..., description="List of repository activities")
    total_repositories: int = Field(..., description="Total number of repositories analyzed")
    total_events: int = Field(..., description="Total number of events analyzed")
