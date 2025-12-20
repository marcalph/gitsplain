"""Workflow manager for repository analysis workflow."""

import time
from typing import Any, Dict, Optional
from gitsplain.services.llm import LLMClient
from gitsplain.services.github import GitHubClient


from dotenv import load_dotenv

load_dotenv()


class WorkflowManager:
    """Manages the workflow for analyzing a repository."""

    def __init__(self, github_client: GitHubClient, llm_client: LLMClient):
        self.github_client = github_client
        self.llm_client = llm_client

    def read_repository(self, repo_url: str) -> Dict[str, Any]:
        """Step 1: Read repository structure."""
        username, repo = GitHubClient.parse_url(repo_url)
        return self.github_client.get_repo_data(username, repo)

    def match_components(
        self, repository_structure: Dict[str, Any]
    ) -> Dict[str, list[str]]:
        """Step 2: Match components in the repository."""
        time.sleep(1)  # Simulate delay
        return {
            "Database": ["src/config.py", "src/utils.py"],
            "API Handler": ["src/main.py", "app.py"],
            "Test Suite": ["tests/test_main.py", "tests/test_utils.py"],
            "Documentation": ["docs/README.md", "docs/API.md"],
        }

    def build_json_graph(
        self,
        repository_structure: Dict[str, Any],
        component_matches: Dict[str, list[str]],
        repo_url: str,
    ) -> Dict[str, Any]:
        """Step 3: Build JSON graph representation."""
        time.sleep(1)  # Simulate delay
        # Mock JSON graph
        return {
            "repository": repo_url,
            "components": [
                {
                    "name": "Database",
                    "files": ["src/config.py", "src/utils.py"],
                    "dependencies": ["API Handler"],
                },
                {
                    "name": "API Handler",
                    "files": ["src/main.py", "app.py"],
                    "dependencies": ["Database", "Test Suite"],
                },
                {
                    "name": "Test Suite",
                    "files": ["tests/test_main.py", "tests/test_utils.py"],
                    "dependencies": ["API Handler"],
                },
                {
                    "name": "Documentation",
                    "files": ["docs/README.md", "docs/API.md"],
                    "dependencies": [],
                },
            ],
            "total_files": 8,
            "total_components": 4,
        }

    def generate_html_graph(self, json_graph: Dict[str, Any]) -> str:
        """Step 4: Generate HTML graph visualization."""
        time.sleep(1)  # Simulate delay
        # Mock HTML graph
        return """
        <!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>
            MY GRAPH HERE
        </body>
        </html>
        """


def get_workflow_manager(
    github_client: Optional[GitHubClient] = None,
    llm_client: Optional[LLMClient] = None,
) -> WorkflowManager:
    if llm_client is None:
        llm_client = LLMClient()

    if github_client is None:
        github_client = GitHubClient()

    return WorkflowManager(github_client=github_client, llm_client=llm_client)
