"""Phase 1: Component mapping prompts."""

from pydantic import BaseModel


class ComponentMapping(BaseModel):
    component: str
    path: str
    is_directory: bool


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
4. If a component doesn't have a clear corresponding file or directory, simply dont include it in the map.

Now, provide your final answer in the following format:

<component_mapping>
1. [Component Name]: [File/Directory Path]
2. [Component Name]: [File/Directory Path]
[Continue for all identified components]
</component_mapping>

Remember to be as specific as possible in your mappings. Use the symbols to verify that your mappings are accurate - e.g., if a component is "UserService", look for a file containing a UserService class.
"""

MAPPING_PROMPT_STRUCTURED = """
You are tasked with creating a comprehensive mapping of system components to their corresponding files and directories in a project's file structure.

You will be provided with:
1. A system design explanation in <explanation> tags
2. A file tree of the project in <file_tree> tags
3. Extracted code symbols (classes, modules, structs) in <symbols> tags showing key abstractions in each file

Analyze the explanation and map components to their paths. Be thorough and generous with mappings.

Guidelines:
- Map ALL components mentioned in the explanation, from high-level services to utilities
- Include directories for broad components (e.g., "API Layer" → "src/api/")
- Include specific files for focused components (e.g., "User Authentication" → "src/auth/login.py")
- Use the extracted symbols to find additional mappings - each class/module in symbols is worth considering
- Map configuration, tests, and infrastructure components too (not just core code)
- Aim for 30-30 mappings for a typical project - be comprehensive
- Only use paths that actually exist in the provided file tree

Respond with a JSON object in this exact format:
{
  "mappings": [
    {"component": "Component Name", "path": "path/to/file_or_dir", "is_directory": true},
    {"component": "Another Component", "path": "src/file.py", "is_directory": false}
  ]
}

Only output the JSON object, no other text.
"""
