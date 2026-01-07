"""Phase 2: Graph generation prompt."""

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    group: str
    title: str
    path: str | None = None

    def __str__(self) -> str:
        path_info = f" @ {self.path}" if self.path else ""
        return f"[{self.group}] {self.label}{path_info} - {self.title}"


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str | None = None

    def __str__(self) -> str:
        label_info = f" ({self.label})" if self.label else ""
        return f"{self.source} -> {self.target}{label_info}"


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


GRAPH_PROMPT = """
You are a principal software engineer tasked with creating a system architecture graph. Your goal is to represent the architecture as a directed graph with nodes (components) and edges (relationships).

You will be provided with:
1. A detailed explanation of the architecture in <explanation> tags
2. A component mapping showing which files/directories implement each component in <component_mapping> tags

Create a graph with:

NODES - Each node represents a component/module/service:
- id: Unique identifier (lowercase, underscores, no spaces). Example: "api_gateway", "user_service"
- label: Human-readable display name. Example: "API Gateway", "User Service"
- group: Category for coloring. Must be one of: frontend, backend, database, service, external, config
- title: A 1-2 sentence tooltip describing the component's responsibilities. Be specific. Example: "Handles JWT authentication, manages login/logout flows, and validates session tokens."
- path: The file or directory path from the component_mapping (if available)

EDGES - Each edge represents a relationship/dependency:
- source: The node id that initiates the relationship
- target: The node id that receives/is depended upon
- label: Brief description of the relationship (optional). Example: "calls", "reads from", "authenticates"

Guidelines:
- Include ALL major components from the explanation
- Show data flow direction (source → target)
- Group related components using the same group category
- Use paths from component_mapping when available
- Keep labels concise but descriptive
- Aim for 8-20 nodes for a readable diagram
"""
