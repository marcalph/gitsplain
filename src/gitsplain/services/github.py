"""GitHub service for fetching repository data using PyGithub."""

import os
from typing import Optional

from github import Auth, Github, GithubException
from github.Repository import Repository
from loguru import logger


class GitHubClient:
    """Client for interacting with the GitHub API using PyGithub."""

    EXCLUDED_PATTERNS = [
        "node_modules/",
        "vendor/",
        "venv/",
        ".venv/",
        ".min.",
        ".pyc",
        ".pyo",
        ".pyd",
        ".so",
        ".dll",
        ".class",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".ico",
        ".svg",
        ".ttf",
        ".woff",
        ".webp",
        "__pycache__/",
        ".cache/",
        ".tmp/",
        "yarn.lock",
        "poetry.lock",
        "package-lock.json",
        ".log",
        ".vscode/",
        ".idea/",
        ".git/",
    ]

    def __init__(self, pat: Optional[str] = None):
        """Initialize the GitHub client."""
        self.token = pat or os.getenv("GITHUB_PAT")
        if self.token:
            self._client = Github(auth=Auth.Token(self.token))
            logger.debug("GitHub client initialized with PAT")
        else:
            self._client = Github()
            logger.warning(
                "No GitHub PAT - using unauthenticated requests (60 req/hour)"
            )

    def _get_repo(self, owner: str, repo: str) -> Repository:
        """Get a repository object."""
        return self._client.get_repo(f"{owner}/{repo}")

    def _should_include_file(self, path: str) -> bool:
        """Check if a file should be included based on exclusion patterns."""
        return not any(pattern in path.lower() for pattern in self.EXCLUDED_PATTERNS)

    def check_repository_exists(self, owner: str, repo: str) -> bool:
        """Check if a repository exists."""
        try:
            self._get_repo(owner, repo)
            return True
        except GithubException:
            return False

    def get_default_branch(self, owner: str, repo: str) -> Optional[str]:
        """Get the default branch of a repository."""
        try:
            return self._get_repo(owner, repo).default_branch
        except GithubException:
            return None

    def get_file_tree(self, owner: str, repo: str) -> str:
        """Get the filtered file tree of a repository."""
        try:
            repository = self._get_repo(owner, repo)
            tree = repository.get_git_tree(
                sha=repository.default_branch, recursive=True
            )

            all_paths = [item.path for item in tree.tree if item.type == "blob"]
            paths = [p for p in all_paths if self._should_include_file(p)]

            logger.info(
                f"File tree: {len(paths)} files ({len(all_paths) - len(paths)} excluded)"
            )
            return "\n".join(paths)
        except GithubException as e:
            logger.error(f"Failed to fetch file tree: {e}")
            raise ValueError(
                "Could not fetch file tree. Repo may not exist or be private."
            )

    def get_readme(self, owner: str, repo: str) -> str:
        """Get the README contents of a repository."""
        try:
            repository = self._get_repo(owner, repo)
            readme = repository.get_readme()
            content = readme.decoded_content.decode("utf-8")
            logger.info(f"README fetched: {len(content)} chars")
            return content
        except GithubException as e:
            if e.status == 404:
                logger.warning(f"No README found for {owner}/{repo}")
                return ""
            raise ValueError(f"Failed to fetch README: {e}")

    def get_repo_data(self, owner: str, repo: str) -> dict:
        """Get all repository data needed for diagram generation."""
        logger.info(f"Fetching repository data for {owner}/{repo}")

        default_branch = self.get_default_branch(owner, repo) or "main"
        file_tree = self.get_file_tree(owner, repo)
        readme = self.get_readme(owner, repo)

        logger.info(f"Repository data complete for {owner}/{repo}")
        return {
            "default_branch": default_branch,
            "file_tree": file_tree,
            "readme": readme,
        }

    def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        """Get language statistics for a repository."""
        try:
            repository = self._get_repo(owner, repo)
            languages = repository.get_languages()
            sorted_langs = dict(
                sorted(languages.items(), key=lambda x: x[1], reverse=True)
            )
            logger.info(f"Languages found: {list(sorted_langs.keys())[:5]}")
            return sorted_langs
        except GithubException as e:
            logger.warning(f"Failed to fetch languages: {e}")
            return {}

    def get_file_content(self, owner: str, repo: str, path: str) -> str | None:
        """Get the content of a specific file."""
        try:
            repository = self._get_repo(owner, repo)
            content = repository.get_contents(path, ref=repository.default_branch)
            if isinstance(content, list):
                return None  # It's a directory
            return content.decoded_content.decode("utf-8")
        except GithubException as e:
            logger.debug(f"Failed to fetch {path}: {e}")
            return None

    def get_files_content(
        self, owner: str, repo: str, paths: list[str]
    ) -> dict[str, str]:
        """Get the content of multiple files."""
        results = {}
        for path in paths:
            content = self.get_file_content(owner, repo, path)
            if content is not None:
                results[path] = content
        logger.info(f"Fetched content for {len(results)}/{len(paths)} files")
        return results
