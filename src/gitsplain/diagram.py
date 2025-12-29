"""Diagram generator for repository architecture visualization."""

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from gitsplain.prompts.mapping import MAPPING_PROMPT_STRUCTURED, MappingResponse
from gitsplain.services.ast_parser import EXTENSION_TO_LANGUAGE, ASTParser
from gitsplain.services.github import GitHubClient
from gitsplain.services.llm import LLMClient


@dataclass
class GenerationState:
    """Data container that accumulates results as it flows through diagram generation phases."""

    # inputs
    owner: str = ""
    repo: str = ""
    instructions: str = ""

    # Phase 0: repository info (file tree, readme, top languages) + static analysis
    repo_info: dict[str, Any] = field(default_factory=dict)
    static_analysis: dict[str, Any] = field(default_factory=dict)

    # Phase 1: component mapping
    component_mapping: dict[str, Any] = field(default_factory=dict)

    # Phase 2: graph structure
    graph_structure: dict[str, Any] = field(default_factory=dict)

    # Final output
    graph_html: str = ""


class DiagramGenerator:
    """Generates architecture diagrams from repository analysis."""

    def __init__(
        self,
        github_client: Optional[GitHubClient] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        self.state = GenerationState()
        self.github = github_client or GitHubClient()
        self.llm = llm_client or LLMClient()

    def phase0_repo_info(self, owner: str, repo: str) -> dict[str, Any]:
        """Phase 0: Fetch repository information."""
        self.state.owner = owner
        self.state.repo = repo

        repo_data = self.github.get_repo_data(owner, repo)
        languages = self.github.get_languages(owner, repo)

        self.state.repo_info = {
            "owner": owner,
            "repo": repo,
            "default_branch": repo_data.get("default_branch", "main"),
            "file_tree": repo_data.get("file_tree", "").split("\n"),
            "readme": repo_data.get("readme", ""),
            "languages": languages,
        }
        return self.state.repo_info

    def phase0_static_analysis(self, max_files: int = 50) -> dict[str, Any]:
        """Phase 0: Perform static analysis using AST parsing."""
        parser = ASTParser()
        file_tree = self.state.repo_info.get("file_tree", [])

        # Filter to parseable files
        parseable_files = [
            f
            for f in file_tree
            if any(f.endswith(ext) for ext in EXTENSION_TO_LANGUAGE)
        ]
        logger.info(f"Found {len(parseable_files)} parseable files")

        # Limit files to avoid too many API calls
        files_to_parse = parseable_files[:max_files]
        if len(parseable_files) > max_files:
            logger.warning(
                f"Limiting to {max_files} files (skipping {len(parseable_files) - max_files})"
            )

        # Fetch file contents
        file_contents = self.github.get_files_content(
            self.state.owner, self.state.repo, files_to_parse
        )

        # Parse files and extract symbols
        all_symbols = parser.extract_from_files(file_contents)

        # Build output structure with symbol names as keys
        files_analysis = {}
        for path, symbols in all_symbols.items():
            file_symbols = {}
            for c in symbols.classes:
                file_symbols[c.name] = {
                    "kind": c.kind,
                    "line": c.line,
                    "docstring": c.docstring,
                }
            for f in symbols.functions:
                file_symbols[f.name] = {
                    "kind": f.kind,
                    "line": f.line,
                    "docstring": f.docstring,
                }
            files_analysis[path] = {
                "language": symbols.language,
                "symbols": file_symbols,
            }

        self.state.static_analysis = {
            "languages": self.state.repo_info.get("languages", {}),
            "files_parsed": len(all_symbols),
            "total_classes": sum(len(s.classes) for s in all_symbols.values()),
            "total_functions": sum(len(s.functions) for s in all_symbols.values()),
            "files": files_analysis,
        }
        return self.state.static_analysis

    def phase1_component_mapping(self) -> dict[str, Any]:
        """Phase 1: Map files to architectural components using LLM."""
        # Prepare data for LLM
        file_tree = "\n".join(self.state.repo_info.get("file_tree", []))
        readme = self.state.repo_info.get("readme", "")
        symbols = json.dumps(self.state.static_analysis.get("files", {}), indent=2)

        # Call LLM with structured output
        response = self.llm.call_api_structured(
            system_prompt=MAPPING_PROMPT_STRUCTURED,
            data={
                "explanation": readme,
                "file_tree": file_tree,
                "symbols": symbols,
            },
            response_model=MappingResponse,
        )

        # Convert to dict format grouped by component
        component_to_paths: dict[str, list[str]] = {}
        for mapping in response.mappings:
            if mapping.component not in component_to_paths:
                component_to_paths[mapping.component] = []
            component_to_paths[mapping.component].append(mapping.path)

        self.state.component_mapping = {
            "mappings": [m.model_dump() for m in response.mappings],
            "by_component": component_to_paths,
        }
        return self.state.component_mapping

    def phase2_graph_structure(self) -> dict[str, Any]:
        """Phase 2: Build the graph structure representation."""
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
        self.phase0_static_analysis()
        self.phase1_component_mapping()
        self.phase2_graph_structure()
        self.generate_html()
        return self.state


def get_diagram_generator() -> DiagramGenerator:
    """Factory function to create a DiagramGenerator instance."""
    return DiagramGenerator()
