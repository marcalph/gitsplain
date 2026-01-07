"""Graph renderer for generating Mermaid diagrams."""

from gitsplain.prompts.diagram import GraphEdge, GraphNode


class MermaidRenderer:
    """Renders graphs to Mermaid diagrams."""

    GROUP_COLORS = {
        "frontend": "#4CAF50",
        "backend": "#2196F3",
        "database": "#9C27B0",
        "service": "#FF9800",
        "external": "#607D8B",
        "config": "#795548",
    }

    def render_mermaid(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> str:
        """Generate Mermaid flowchart code."""
        lines = ["flowchart TD"]

        for node in nodes:
            node_id = node.id if hasattr(node, "id") else node["id"]
            label = node.label if hasattr(node, "label") else node["label"]
            lines.append(f'    {node_id}["{label}"]')

        for edge in edges:
            source = edge.source if hasattr(edge, "source") else edge["source"]
            target = edge.target if hasattr(edge, "target") else edge["target"]
            label = edge.label if hasattr(edge, "label") else edge.get("label")
            if label:
                lines.append(f"    {source} -->|{label}| {target}")
            else:
                lines.append(f"    {source} --> {target}")

        for node in nodes:
            node_id = node.id if hasattr(node, "id") else node["id"]
            group = (
                node.group if hasattr(node, "group") else node.get("group", "service")
            )
            color = self.GROUP_COLORS.get(group, "#666")
            lines.append(f"    style {node_id} fill:{color},color:#fff")

        return "\n".join(lines)

    def render_html(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> str:
        """Generate HTML page with Mermaid diagram."""
        mermaid_code = self.render_mermaid(nodes, edges)

        return f"""<!DOCTYPE html>
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
