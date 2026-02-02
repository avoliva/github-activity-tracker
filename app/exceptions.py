"""Custom exceptions for GitHub API errors."""

from typing import Optional


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors.

    Attributes:
        message: Error message describing the issue
        status_code: HTTP status code from GitHub API (if applicable)

    """

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        """Initialize GitHub API error.

        Args:
            message: Error message describing the issue
            status_code: HTTP status code from GitHub API (optional)

        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UserNotFoundError(GitHubAPIError):
    """Exception raised when a GitHub user is not found.

    Attributes:
        username: The username that was not found
        message: Error message indicating user not found
        status_code: HTTP status code (404)

    """

    def __init__(self, username: str) -> None:
        """Initialize user not found error.

        Args:
            username: The GitHub username that was not found

        """
        self.username = username
        super().__init__(f"User '{username}' not found", status_code=404)


class RateLimitError(GitHubAPIError):
    """Exception raised when GitHub API rate limit is exceeded.

    Attributes:
        retry_after: Number of seconds to wait before retrying (optional)
        message: Error message with retry information
        status_code: HTTP status code (429)

    """

    def __init__(self, retry_after: Optional[int] = None) -> None:
        """Initialize rate limit error.

        Args:
            retry_after: Number of seconds to wait before retrying (optional)

        """
        self.retry_after = retry_after
        message = "GitHub API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, status_code=429)
