"""Phase 1: Component mapping prompts."""

from pydantic import BaseModel


class ComponentMapping(BaseModel):
    component: str
    role: str
    path: str
    is_directory: bool

    def __str__(self) -> str:
        path_type = "directory" if self.is_directory else "file"
        return f"[{path_type}] {self.component} @ {self.path} - {self.role}"


class MappingResponse(BaseModel):
    mappings: list[ComponentMapping]


MAPPING_PROMPT = """
You are tasked with mapping key components of a system design to their corresponding files and directories in a project's file structure.

You will be provided with:
1. A system design explanation in <explanation> tags
2. A file tree of the project in <file_tree> tags
3. Extracted code symbols (classes, modules, structs) in <symbols> tags showing key abstractions in each file

Your task is to analyze the system design explanation and identify key components, modules, or services mentioned. Then map these components to their corresponding directories and files using both the file tree and the extracted symbols.

Guidelines:
1. Focus on major components described in the system design.
2. Use the extracted symbols to identify which files contain relevant classes/modules.
3. Include both directories and specific files when relevant.
4. For each component, describe its role in the system (e.g., "Handles user authentication", "Manages database connections").
5. If a component doesn't have a clear corresponding file or directory, simply dont include it in the map.

Now, provide your final answer in the following format:

<component_mapping>
1. [Component Name] - [Role]: [File/Directory Path]
2. [Component Name] - [Role]: [File/Directory Path]
[Continue for all identified components]
</component_mapping>

Remember to be as specific as possible in your mappings. Use the symbols to verify that your mappings are accurate - e.g., if a component is "UserService", look for a file containing a UserService class.
"""

MAPPING_PROMPT_STRUCTURED = """
You are tasked with identifying the key architectural components of a codebase that would help someone build a mental model of how the system works.

You will be provided with:
1. A system design explanation in <explanation> tags
2. A file tree of the project in <file_tree> tags
3. Extracted code symbols (classes, modules, structs) in <symbols> tags showing key abstractions in each file

Your goal is to identify components that matter for understanding the system's architecture and data flow.

INCLUDE these types of components:
- Core services and business logic (e.g., "Authentication Service", "Payment Processor")
- Main application entry points (e.g., "API Server", "CLI Handler")
- External integrations (e.g., "Database Client", "GitHub API Client")
- Key orchestrators or coordinators (e.g., "Workflow Manager", "Pipeline Runner")
- Data stores and caches
- Message queues or event handlers

EXCLUDE these (they add noise, not architectural insight):
- Test files and test directories
- Individual utility functions (e.g., parse_url, format_date)
- Configuration/prompt/template files
- Data classes, DTOs, or Pydantic models (unless they represent core domain entities)
- Package __init__.py files
- Generic utility modules

Guidelines:
- Focus on components that have clear responsibilities and interactions
- Prefer directories for layers/modules, files for specific services
- Aim for 5-15 mappings that capture the essential architecture
- Each component should represent a meaningful architectural boundary
- Only use paths that actually exist in the provided file tree

Respond with a JSON object in this exact format:
{
  "mappings": [
    {"component": "Component Name", "role": "Handles X and manages Y", "path": "path/to/file_or_dir", "is_directory": true},
    {"component": "Another Component", "role": "Provides Z functionality", "path": "src/file.py", "is_directory": false}
  ]
}

Only output the JSON object, no other text.
"""
