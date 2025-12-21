"""Diagram generator for repository architecture visualization."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GenerationState:
    """Data container that accumulates results as it flows through diagram generation phases."""

    # inputs
    owner: str = ""
    repo: str = ""
    instructions: str = ""

    # Phase 0: repository info
    repo_info: dict[str, Any] = field(default_factory=dict)

    # Phase 1: static analysis
    static_analysis: dict[str, Any] = field(default_factory=dict)

    # Phase 2: component mapping
    component_mapping: dict[str, list[str]] = field(default_factory=dict)

    # Phase 3: graph structure
    graph_structure: dict[str, Any] = field(default_factory=dict)

    # Final output
    graph_html: str = ""


class DiagramGenerator:
    """Generates architecture diagrams from repository analysis."""

    def __init__(self):
        self.state = GenerationState()

    def phase0_repo_info(self, owner: str, repo: str) -> dict[str, Any]:
        """Phase 0: Fetch repository information."""
        self.state.owner = owner
        self.state.repo = repo

        # Mock data
        self.state.repo_info = {
            "owner": owner,
            "repo": repo,
            "default_branch": "main",
            "description": "A sample repository for testing",
            "language": "Python",
            "stars": 1234,
            "forks": 56,
            "file_tree": [
                "README.md",
                "pyproject.toml",
                "src/",
                "src/__init__.py",
                "src/main.py",
                "src/api/",
                "src/api/__init__.py",
                "src/api/routes.py",
                "src/api/handlers.py",
                "src/models/",
                "src/models/__init__.py",
                "src/models/user.py",
                "src/models/post.py",
                "src/services/",
                "src/services/__init__.py",
                "src/services/auth.py",
                "src/services/database.py",
                "tests/",
                "tests/test_api.py",
                "tests/test_models.py",
            ],
            "readme": "# Sample Project\n\nThis is a sample project with API, models, and services.",
        }
        return self.state.repo_info

    def phase1_static_analysis(self) -> dict[str, Any]:
        """Phase 1: Perform static analysis on the codebase."""
        # Mock data
        self.state.static_analysis = {
            "languages": {"Python": 85, "YAML": 10, "Markdown": 5},
            "frameworks_detected": ["FastAPI", "SQLAlchemy", "Pydantic"],
            "entry_points": ["src/main.py"],
            "key_modules": [
                {
                    "path": "src/api/routes.py",
                    "type": "API Routes",
                    "imports": ["fastapi", "src.services.auth", "src.models.user"],
                },
                {
                    "path": "src/services/database.py",
                    "type": "Database Service",
                    "imports": ["sqlalchemy", "src.models"],
                },
                {
                    "path": "src/services/auth.py",
                    "type": "Authentication",
                    "imports": ["jwt", "src.models.user"],
                },
            ],
            "dependency_graph": {
                "src/api/routes.py": ["src/services/auth.py", "src/models/user.py"],
                "src/services/auth.py": [
                    "src/models/user.py",
                    "src/services/database.py",
                ],
                "src/services/database.py": [
                    "src/models/user.py",
                    "src/models/post.py",
                ],
            },
        }
        return self.state.static_analysis

    def phase2_component_mapping(self) -> dict[str, list[str]]:
        """Phase 2: Map files to architectural components."""
        # Mock data
        self.state.component_mapping = {
            "API Layer": [
                "src/api/routes.py",
                "src/api/handlers.py",
                "src/main.py",
            ],
            "Data Models": [
                "src/models/user.py",
                "src/models/post.py",
            ],
            "Services": [
                "src/services/auth.py",
                "src/services/database.py",
            ],
            "Tests": [
                "tests/test_api.py",
                "tests/test_models.py",
            ],
        }
        return self.state.component_mapping

    def phase3_graph_structure(self) -> dict[str, Any]:
        """Phase 3: Build the graph structure representation."""
        # Mock data
        self.state.graph_structure = {
            "nodes": [
                {
                    "id": "api",
                    "label": "API Layer",
                    "type": "service",
                    "color": "#4CAF50",
                },
                {
                    "id": "models",
                    "label": "Data Models",
                    "type": "data",
                    "color": "#2196F3",
                },
                {
                    "id": "services",
                    "label": "Services",
                    "type": "service",
                    "color": "#FF9800",
                },
                {
                    "id": "database",
                    "label": "Database",
                    "type": "storage",
                    "color": "#9C27B0",
                },
                {"id": "auth", "label": "Auth", "type": "service", "color": "#F44336"},
            ],
            "edges": [
                {"from": "api", "to": "services", "label": "calls"},
                {"from": "api", "to": "models", "label": "uses"},
                {"from": "services", "to": "models", "label": "uses"},
                {"from": "services", "to": "database", "label": "queries"},
                {"from": "auth", "to": "models", "label": "validates"},
                {"from": "api", "to": "auth", "label": "authenticates"},
            ],
            "metadata": {
                "total_nodes": 5,
                "total_edges": 6,
                "architecture_pattern": "Layered Architecture",
            },
        }
        return self.state.graph_structure

    def generate_html(self) -> str:
        """Generate the final HTML visualization using Mermaid."""
        nodes = self.state.graph_structure.get("nodes", [])
        edges = self.state.graph_structure.get("edges", [])

        # Build Mermaid flowchart
        lines = ["flowchart TD"]

        # Add nodes
        for node in nodes:
            lines.append(f'    {node["id"]}["{node["label"]}"]')

        # Add edges
        for edge in edges:
            label = edge.get("label", "")
            if label:
                lines.append(f"    {edge['from']} -->|{label}| {edge['to']}")
            else:
                lines.append(f"    {edge['from']} --> {edge['to']}")

        # Add styling
        for node in nodes:
            color = node.get("color", "#666")
            lines.append(f"    style {node['id']} fill:{color},color:#fff")

        mermaid_code = "\n".join(lines)

        self.state.graph_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: #fafafa;
        }}
        .mermaid {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="mermaid">
{mermaid_code}
    </div>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</body>
</html>"""
        return self.state.graph_html

    def run_all(self, owner: str, repo: str, instructions: str = "") -> GenerationState:
        """Run all phases and return the complete state."""
        self.state.instructions = instructions
        self.phase0_repo_info(owner, repo)
        self.phase1_static_analysis()
        self.phase2_component_mapping()
        self.phase3_graph_structure()
        self.generate_html()
        return self.state


def get_diagram_generator() -> DiagramGenerator:
    """Factory function to create a DiagramGenerator instance."""
    return DiagramGenerator()
