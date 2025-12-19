from typing import Optional
from src.services.github.client import GitHubRepository, GitHubFileTree


def get_github_client(github_token: Optional[str] = None) -> GitHubFileTree:
    return GitHubFileTree(github_token=github_token)


def get_github_repository(
    github_url: str, github_token: Optional[str] = None
) -> GitHubRepository:
    client = get_github_client(github_token)
    return client.get_simple_tree_structure(github_url)
