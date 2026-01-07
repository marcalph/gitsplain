"""Utility functions for GitHub URL handling."""

from urllib.parse import urlparse

from github import GithubException


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Extract owner and repo name from a GitHub URL.

    Args:
        url: GitHub repository URL or owner/repo format

    Returns:
        Tuple of (owner, repo_name)

    Raises:
        GithubException: If URL is invalid

    Examples:
        >>> parse_github_url("https://github.com/owner/repo")
        ('owner', 'repo')
        >>> parse_github_url("owner/repo")
        ('owner', 'repo')
    """
    # Handle direct owner/repo format
    if "/" in url and "github.com" not in url and "://" not in url:
        parts = url.strip("/").split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]

    # Handle full GitHub URLs
    parsed = urlparse(url)
    if parsed.netloc and "github.com" not in parsed.netloc:
        raise GithubException(400, "URL must be from github.com", None)

    path = parsed.path.strip("/")
    parts = path.split("/")

    if len(parts) < 2:
        raise GithubException(
            400,
            "Invalid GitHub URL. Expected: https://github.com/owner/repo or owner/repo",
            None,
        )
    return parts[0], parts[1]


def build_github_url(owner: str, repo: str) -> str:
    """
    Generate a GitHub repository URL from owner and repo name.

    Args:
        owner: GitHub username or organization
        repo: Repository name

    Returns:
        Full GitHub repository URL

    Examples:
        >>> build_github_url("owner", "repo")
        'https://github.com/owner/repo'
    """
    return f"https://github.com/{owner}/{repo}"
