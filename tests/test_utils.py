"""Tests for utility functions."""

import pytest
from github import GithubException

from gitsplain.utils import parse_github_url


class TestParseGithubUrl:
    """Tests for parse_github_url function."""

    def test_owner_repo_format(self):
        """Test parsing owner/repo format."""
        owner, repo = parse_github_url("owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_full_url(self):
        """Test parsing full GitHub URL."""
        owner, repo = parse_github_url("https://github.com/python/cpython")
        assert owner == "python"
        assert repo == "cpython"

    def test_url_with_trailing_slash(self):
        """Test parsing URL with trailing slash."""
        owner, repo = parse_github_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo == "repo"

    def test_url_with_extra_path(self):
        """Test parsing URL with extra path segments."""
        owner, repo = parse_github_url("https://github.com/owner/repo/tree/main")
        assert owner == "owner"
        assert repo == "repo"

    def test_http_url(self):
        """Test parsing http URL."""
        owner, repo = parse_github_url("http://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_invalid_url_no_repo(self):
        """Test that single segment raises GithubException."""
        with pytest.raises(GithubException):
            parse_github_url("https://github.com/owner")

    def test_non_github_url(self):
        """Test that non-GitHub URL raises GithubException."""
        with pytest.raises(GithubException):
            parse_github_url("https://gitlab.com/owner/repo")
