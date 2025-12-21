"""Workflow manager for repository analysis workflow."""

import time
from typing import Any, Dict, Optional
from gitsplain.services.llm import LLMClient
from gitsplain.services.github import GitHubClient
from gitsplain.utils import parse_github_url
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class GenerationState:
    """
    Data container that accumulates results as it flows through diagram generation phases.
    Each phase reads what it needs and populates its outputs, primary goal is inspection/debugging.
    """

    # inputs
    owner: str
    repo: str
    instructions: str = ""

    # static analysis phase
    # component mapping
    # graph building


class DiagramGenerator:
    """Manages the workflow for analyzing a repository."""

    def __init__(self, github_client: GitHubClient, llm_client: LLMClient):
        self.github_client = github_client
        self.llm_client = llm_client
        self.state: Optional[GenerationState] = None

    def run(self):
        # template method
        pass

    def read_repository(self, repo_url: str) -> Dict[str, Any]:
        """Step 1: Read repository structure."""
        owner, repo = parse_github_url(repo_url)
        self.state = GenerationState(owner=owner, repo=repo)
        return self.github_client.get_repo_data(owner, repo)

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
        return {
            "repository": repo_url,
            "components": [
                {
                    "name": name,
                    "files": files,
                    "dependencies": [],
                }
                for name, files in component_matches.items()
            ],
            "total_files": sum(len(f) for f in component_matches.values()),
            "total_components": len(component_matches),
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
) -> DiagramGenerator:
    if llm_client is None:
        llm_client = LLMClient()

    if github_client is None:
        github_client = GitHubClient()

    return DiagramGenerator(github_client=github_client, llm_client=llm_client)
