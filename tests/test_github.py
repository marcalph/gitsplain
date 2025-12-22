"""Tests for GitHub client."""

from unittest.mock import MagicMock, patch

from github import GithubException

from gitsplain.services.github import GitHubClient


class TestGitHubClient:
    """Tests for GitHubClient class."""

    def test_init_with_pat(self):
        """Test initialization with PAT."""
        with patch("gitsplain.services.github.Github") as mock_github:
            client = GitHubClient(pat="test_token")
            assert client.token == "test_token"
            mock_github.assert_called_once()

    def test_init_without_pat(self):
        """Test initialization without PAT uses env var."""
        with (
            patch("gitsplain.services.github.Github") as mock_github,
            patch.dict("os.environ", {"GITHUB_PAT": ""}, clear=False),
        ):
            client = GitHubClient()
            assert client.token is None or client.token == ""
            mock_github.assert_called_once()

    def test_should_include_file_valid(self):
        """Test file inclusion for valid files."""
        client = GitHubClient.__new__(GitHubClient)
        client.EXCLUDED_PATTERNS = GitHubClient.EXCLUDED_PATTERNS

        assert client._should_include_file("src/main.py") is True
        assert client._should_include_file("lib/utils.js") is True

    def test_should_include_file_excluded(self):
        """Test file exclusion for excluded patterns."""
        client = GitHubClient.__new__(GitHubClient)
        client.EXCLUDED_PATTERNS = GitHubClient.EXCLUDED_PATTERNS

        assert client._should_include_file("node_modules/package/index.js") is False
        assert client._should_include_file("src/__pycache__/main.pyc") is False
        assert client._should_include_file("assets/image.png") is False
        assert client._should_include_file(".venv/lib/python.py") is False

    def test_check_repository_exists_true(self):
        """Test check_repository_exists returns True for existing repo."""
        with patch("gitsplain.services.github.Github") as mock_github:
            mock_client = MagicMock()
            mock_github.return_value = mock_client
            mock_client.get_repo.return_value = MagicMock()

            client = GitHubClient(pat="test")
            assert client.check_repository_exists("owner", "repo") is True
            mock_client.get_repo.assert_called_with("owner/repo")

    def test_check_repository_exists_false(self):
        """Test check_repository_exists returns False for missing repo."""
        with patch("gitsplain.services.github.Github") as mock_github:
            mock_client = MagicMock()
            mock_github.return_value = mock_client
            mock_client.get_repo.side_effect = GithubException(404, "Not Found", None)

            client = GitHubClient(pat="test")
            assert client.check_repository_exists("owner", "nonexistent") is False

    def test_get_default_branch(self):
        """Test get_default_branch returns correct branch."""
        with patch("gitsplain.services.github.Github") as mock_github:
            mock_client = MagicMock()
            mock_github.return_value = mock_client
            mock_repo = MagicMock()
            mock_repo.default_branch = "main"
            mock_client.get_repo.return_value = mock_repo

            client = GitHubClient(pat="test")
            assert client.get_default_branch("owner", "repo") == "main"

    def test_get_default_branch_error(self):
        """Test get_default_branch returns None on error."""
        with patch("gitsplain.services.github.Github") as mock_github:
            mock_client = MagicMock()
            mock_github.return_value = mock_client
            mock_client.get_repo.side_effect = GithubException(404, "Not Found", None)

            client = GitHubClient(pat="test")
            assert client.get_default_branch("owner", "repo") is None

    def test_get_languages(self):
        """Test get_languages returns sorted languages."""
        with patch("gitsplain.services.github.Github") as mock_github:
            mock_client = MagicMock()
            mock_github.return_value = mock_client
            mock_repo = MagicMock()
            mock_repo.get_languages.return_value = {"Python": 1000, "JavaScript": 500}
            mock_client.get_repo.return_value = mock_repo

            client = GitHubClient(pat="test")
            langs = client.get_languages("owner", "repo")

            assert list(langs.keys()) == ["Python", "JavaScript"]
            assert langs["Python"] == 1000

    def test_get_languages_error(self):
        """Test get_languages returns empty dict on error."""
        with patch("gitsplain.services.github.Github") as mock_github:
            mock_client = MagicMock()
            mock_github.return_value = mock_client
            mock_client.get_repo.side_effect = GithubException(404, "Not Found", None)

            client = GitHubClient(pat="test")
            assert client.get_languages("owner", "repo") == {}

    def test_get_readme_not_found(self):
        """Test get_readme returns empty string when not found."""
        with patch("gitsplain.services.github.Github") as mock_github:
            mock_client = MagicMock()
            mock_github.return_value = mock_client
            mock_repo = MagicMock()
            mock_repo.get_readme.side_effect = GithubException(404, "Not Found", None)
            mock_client.get_repo.return_value = mock_repo

            client = GitHubClient(pat="test")
            assert client.get_readme("owner", "repo") == ""
