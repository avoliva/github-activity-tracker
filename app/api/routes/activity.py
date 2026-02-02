import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_github_service
from app.exceptions import GitHubAPIError, UserNotFoundError
from app.models.schemas import UserActivityResponse
from app.services.github_service import GitHubService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/users/{username}/activity",
    response_model=UserActivityResponse,
    summary="Get user activity analysis",
    description="Analyze GitHub user activity and return top 3 activity types per repository",
)
async def get_user_activity(
    username: str, service: GitHubService = Depends(get_github_service)
) -> UserActivityResponse:
    """Get user activity analysis endpoint.

    Args:
        username: GitHub username
        service: Injected GitHub service

    Returns:
        User activity analysis response

    Raises:
        HTTPException: 404 if user not found, 500 for server errors

    """
    try:
        return await service.analyze_user_activity(username)
    except UserNotFoundError as e:
        logger.info(f"User not found: {username}")
        raise HTTPException(status_code=404, detail=e.message)
    except GitHubAPIError as e:
        logger.warning(
            f"GitHub API error for user {username}: {e.message}",
            extra={"status_code": e.status_code},
        )
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
    except Exception:
        logger.error(f"Unexpected error processing request for user {username}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
