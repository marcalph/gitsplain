"""GitHub service for fetching repository data using PyGithub."""

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from github import Auth, Github, GithubException
from github.Repository import Repository
from loguru import logger


LANGUAGE_EXTENSIONS: dict[str, set[str]] = {
    "Python": {".py", ".pyi"},
    "JavaScript": {".js", ".jsx", ".mjs"},
    "TypeScript": {".ts", ".tsx", ".mts"},
    "Go": {".go"},
    "Rust": {".rs"},
    "Java": {".java"},
    "Kotlin": {".kt", ".kts"},
    "C": {".c", ".h"},
    "C++": {".cpp", ".hpp", ".cc", ".cxx", ".hxx"},
    "C#": {".cs"},
    "Ruby": {".rb"},
    "PHP": {".php"},
    "Swift": {".swift"},
    "Scala": {".scala"},
}

PRIORITY_DIRS = {"src", "lib", "app", "pkg", "internal", "core", "cmd"}
SKIP_DIRS = {
    "test",
    "tests",
    "__tests__",
    "spec",
    "specs",
    "examples",
    "example",
    "docs",
    "doc",
    "documentation",
    "scripts",
    "script",
    "fixtures",
    "mocks",
    "mock",
    "__mocks__",
    "testdata",
    "test_data",
}
ENTRY_POINTS = {"main", "index", "app", "lib", "mod", "__init__", "server", "cli"}


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

    def close(self):
        """Close the GitHub client connection."""
        self._client.close()

    @staticmethod
    def parse_url(url: str) -> tuple[str, str]:
        """Parse a GitHub URL to extract username and repository."""
        if "/" in url and "github.com" not in url and "://" not in url:
            parts = url.strip("/").split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]

        parsed = urlparse(url)
        if parsed.netloc and "github.com" not in parsed.netloc:
            raise ValueError("URL must be from github.com")

        path = parsed.path.strip("/")
        parts = path.split("/")

        if len(parts) < 2:
            raise ValueError(
                "Invalid GitHub URL. Expected: https://github.com/username/repo"
            )
        return parts[0], parts[1]

    def _get_repo(self, username: str, repo: str) -> Repository:
        """Get a repository object."""
        return self._client.get_repo(f"{username}/{repo}")

    def _should_include_file(self, path: str) -> bool:
        """Check if a file should be included based on exclusion patterns."""
        return not any(pattern in path.lower() for pattern in self.EXCLUDED_PATTERNS)

    def check_repository_exists(self, username: str, repo: str) -> bool:
        """Check if a repository exists."""
        try:
            self._get_repo(username, repo)
            return True
        except GithubException:
            return False

    def get_default_branch(self, username: str, repo: str) -> Optional[str]:
        """Get the default branch of a repository."""
        try:
            return self._get_repo(username, repo).default_branch
        except GithubException:
            return None

    def get_file_tree(self, username: str, repo: str) -> str:
        """Get the filtered file tree of a repository."""
        try:
            repository = self._get_repo(username, repo)
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

    def get_readme(self, username: str, repo: str) -> str:
        """Get the README contents of a repository."""
        try:
            repository = self._get_repo(username, repo)
            readme = repository.get_readme()
            content = readme.decoded_content.decode("utf-8")
            logger.info(f"README fetched: {len(content)} chars")
            return content
        except GithubException as e:
            if e.status == 404:
                logger.warning(f"No README found for {username}/{repo}")
                raise ValueError("No README found.")
            raise ValueError(f"Failed to fetch README: {e}")

    def get_repo_data(self, username: str, repo: str) -> dict:
        """Get all repository data needed for diagram generation."""
        logger.info(f"Fetching repository data for {username}/{repo}")

        default_branch = self.get_default_branch(username, repo) or "main"
        file_tree = self.get_file_tree(username, repo)
        readme = self.get_readme(username, repo)

        logger.info(f"Repository data complete for {username}/{repo}")
        return {
            "default_branch": default_branch,
            "file_tree": file_tree,
            "readme": readme,
        }

    def get_languages(self, username: str, repo: str) -> dict[str, int]:
        """Get language statistics for a repository."""
        try:
            repository = self._get_repo(username, repo)
            languages = repository.get_languages()
            sorted_langs = dict(
                sorted(languages.items(), key=lambda x: x[1], reverse=True)
            )
            logger.info(f"Languages found: {list(sorted_langs.keys())[:5]}")
            return sorted_langs
        except GithubException as e:
            logger.warning(f"Failed to fetch languages: {e}")
            return {}

    def _get_extensions_for_languages(self, languages: list[str]) -> set[str]:
        """Get file extensions for the given languages."""
        extensions = set()
        for lang in languages:
            if lang in LANGUAGE_EXTENSIONS:
                extensions.update(LANGUAGE_EXTENSIONS[lang])
        return extensions

    def _score_file(self, file_path: str, target_extensions: set[str]) -> int:
        """Score a file for priority (higher = more important)."""
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in target_extensions:
            return -1

        parts = set(path.parts[:-1])
        if parts & SKIP_DIRS:
            return -1

        score = 50
        if parts & PRIORITY_DIRS:
            score += 30
        if path.stem.lower() in ENTRY_POINTS:
            score += 20
        if len(path.parts) <= 2:
            score += 10
        if len(path.parts) > 4:
            score -= (len(path.parts) - 4) * 5

        return max(0, min(100, score))

    def get_priority_files(
        self,
        file_tree: str,
        languages: dict[str, int],
        max_files: int = 30,
        top_n_languages: int = 2,
    ) -> list[str]:
        """Get prioritized list of source files to fetch."""
        top_langs = list(languages.keys())[:top_n_languages]
        if not top_langs:
            top_langs = ["Python", "JavaScript", "TypeScript", "Go"]

        target_extensions = self._get_extensions_for_languages(top_langs)
        logger.info(f"Targeting: {top_langs}, extensions: {target_extensions}")

        scored_files: list[tuple[str, int]] = []
        for file_path in file_tree.split("\n"):
            file_path = file_path.strip()
            if not file_path:
                continue
            score = self._score_file(file_path, target_extensions)
            if score >= 0:
                scored_files.append((file_path, score))

        scored_files.sort(key=lambda x: x[1], reverse=True)
        selected = [f[0] for f in scored_files[:max_files]]

        logger.info(
            f"Selected {len(selected)} priority files from {len(scored_files)} candidates"
        )
        return selected

    def get_file_content(
        self, username: str, repo: str, file_path: str, branch: Optional[str] = None
    ) -> Optional[str]:
        """Get the content of a single file."""
        try:
            repository = self._get_repo(username, repo)
            ref = branch or repository.default_branch
            contents = repository.get_contents(file_path, ref=ref)

            if not isinstance(contents, list) and contents.decoded_content:
                return contents.decoded_content.decode("utf-8")
        except GithubException as e:
            logger.warning(f"Failed to fetch {file_path}: {e}")
        except UnicodeDecodeError as e:
            logger.warning(f"Failed to decode {file_path}: {e}")
        return None

    def get_file_contents(
        self,
        username: str,
        repo: str,
        file_paths: list[str],
        branch: Optional[str] = None,
    ) -> dict[str, str]:
        """Fetch content for multiple files."""
        repository = self._get_repo(username, repo)
        ref = branch or repository.default_branch

        results = {}
        for file_path in file_paths:
            content = self.get_file_content(username, repo, file_path, ref)
            if content:
                results[file_path] = content

        logger.info(f"Fetched {len(results)}/{len(file_paths)} files")
        return results
