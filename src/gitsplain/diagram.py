"""Diagram generator for repository architecture visualization."""

from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from gitsplain.prompts.diagram import GRAPH_PROMPT, GraphResponse
from gitsplain.prompts.mapping import MAPPING_PROMPT_STRUCTURED, MappingResponse
from gitsplain.services.ast_parser import EXTENSION_TO_LANGUAGE, ASTParser
from gitsplain.services.github import GitHubClient
from gitsplain.services.llm import LLMClient
from gitsplain.services.renderer import MermaidRenderer


@dataclass
class GenerationState:
    """Accumulates results through diagram generation."""

    owner: str = ""
    repo: str = ""
    instructions: str = ""
    repo_info: dict[str, Any] = field(default_factory=dict)
    static_analysis: dict[str, Any] = field(default_factory=dict)
    component_mapping: dict[str, Any] = field(default_factory=dict)
    graph_structure: dict[str, Any] = field(default_factory=dict)
    graph_html: str = ""


class DiagramGenerator:
    """Generates architecture diagrams from repository analysis."""

    def __init__(
        self,
        github_client: Optional[GitHubClient] = None,
        llm_client: Optional[LLMClient] = None,
        renderer: Optional[MermaidRenderer] = None,
    ):
        self.state = GenerationState()
        self.github = github_client or GitHubClient()
        self.llm = llm_client or LLMClient()
        self.renderer = renderer or MermaidRenderer()

    def fetch_repo_info(self, owner: str, repo: str) -> dict[str, Any]:
        """Fetch repository information from GitHub."""
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

    def analyze_symbols(self, max_files: int = 50) -> dict[str, Any]:
        """Perform static analysis using AST parsing."""
        parser = ASTParser()
        file_tree = self.state.repo_info.get("file_tree", [])

        parseable_files = [
            f
            for f in file_tree
            if any(f.endswith(ext) for ext in EXTENSION_TO_LANGUAGE)
        ]
        logger.info(f"Found {len(parseable_files)} parseable files")

        files_to_parse = parseable_files[:max_files]
        if len(parseable_files) > max_files:
            logger.warning(
                f"Limiting to {max_files} files (skipping {len(parseable_files) - max_files})"
            )

        file_contents = self.github.get_files_content(
            self.state.owner, self.state.repo, files_to_parse
        )
        all_symbols = parser.extract_from_files(file_contents)

        total_classes = sum(1 for s in all_symbols if s.kind != "function")
        total_functions = sum(1 for s in all_symbols if s.kind == "function")
        files_parsed = len(set(s.filepath for s in all_symbols))

        self.state.static_analysis = {
            "languages": self.state.repo_info.get("languages", {}),
            "files_parsed": files_parsed,
            "total_classes": total_classes,
            "total_functions": total_functions,
            "symbols": all_symbols,
        }
        return self.state.static_analysis

    def map_components(self) -> dict[str, Any]:
        """Map files to architectural components using LLM."""
        file_tree = "\n".join(self.state.repo_info.get("file_tree", []))
        readme = self.state.repo_info.get("readme", "")
        symbol_list = self.state.static_analysis.get("symbols", [])
        symbols = "\n".join(str(s) for s in symbol_list)

        response = self.llm.call_api_structured(
            system_prompt=MAPPING_PROMPT_STRUCTURED,
            data={
                "explanation": readme,
                "file_tree": file_tree,
                "symbols": symbols,
            },
            response_model=MappingResponse,
        )

        component_to_paths: dict[str, list[str]] = {}
        for mapping in response.mappings:
            if mapping.component not in component_to_paths:
                component_to_paths[mapping.component] = []
            component_to_paths[mapping.component].append(mapping.path)

        self.state.component_mapping = {
            "mappings": response.mappings,
            "by_component": component_to_paths,
        }
        return self.state.component_mapping

    def build_graph(self) -> dict[str, Any]:
        """Build the graph structure using LLM."""
        readme = self.state.repo_info.get("readme", "")
        mappings = self.state.component_mapping.get("mappings", [])
        component_mapping_str = "\n".join(str(m) for m in mappings)

        response = self.llm.call_api_structured(
            system_prompt=GRAPH_PROMPT,
            data={
                "explanation": readme,
                "component_mapping": component_mapping_str,
            },
            response_model=GraphResponse,
        )

        self.state.graph_structure = {
            "nodes": response.nodes,
            "edges": response.edges,
        }
        return self.state.graph_structure

    def generate_html(self) -> str:
        """Generate HTML visualization."""
        nodes = self.state.graph_structure.get("nodes", [])
        edges = self.state.graph_structure.get("edges", [])
        self.state.graph_html = self.renderer.render_html(nodes, edges)
        return self.state.graph_html

    def run_all(self, owner: str, repo: str, instructions: str = "") -> GenerationState:
        """Run all steps and return the state."""
        self.state.instructions = instructions
        self.fetch_repo_info(owner, repo)
        self.analyze_symbols()
        self.map_components()
        self.build_graph()
        self.generate_html()
        return self.state


def get_diagram_generator() -> DiagramGenerator:
    return DiagramGenerator()
