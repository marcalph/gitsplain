"""AST parsing service using tree-sitter for extracting code symbols."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from loguru import logger

try:
    from tree_sitter_language_pack import get_parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logger.warning("tree-sitter-language-pack not installed, AST extraction disabled")


# Map file extensions to tree-sitter language names
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    # Python
    ".py": "python",
    ".pyi": "python",
    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    # Go
    ".go": "go",
    # Rust
    ".rs": "rust",
    # Java/Kotlin
    ".java": "java",
    ".kt": "kotlin",
    # C/C++
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    # C#
    ".cs": "c_sharp",
    # Ruby
    ".rb": "ruby",
    # PHP
    ".php": "php",
    # Swift
    ".swift": "swift",
    # Scala
    ".scala": "scala",
}

# Tree-sitter node types for classes/structs by language
CLASS_NODE_TYPES: dict[str, set[str]] = {
    "python": {"class_definition"},
    "javascript": {"class_declaration"},
    "typescript": {"class_declaration", "interface_declaration", "type_alias_declaration"},
    "tsx": {"class_declaration", "interface_declaration", "type_alias_declaration"},
    "go": {"type_declaration"},  # for struct types
    "rust": {"struct_item", "enum_item", "trait_item", "impl_item"},
    "java": {"class_declaration", "interface_declaration", "enum_declaration"},
    "kotlin": {"class_declaration", "object_declaration", "interface_declaration"},
    "c": {"struct_specifier", "enum_specifier", "type_definition"},
    "cpp": {"class_specifier", "struct_specifier", "enum_specifier"},
    "c_sharp": {"class_declaration", "interface_declaration", "struct_declaration"},
    "ruby": {"class", "module"},
    "php": {"class_declaration", "interface_declaration", "trait_declaration"},
    "swift": {"class_declaration", "struct_declaration", "protocol_declaration"},
    "scala": {"class_definition", "object_definition", "trait_definition"},
}

# Tree-sitter node types for functions/methods by language
FUNCTION_NODE_TYPES: dict[str, set[str]] = {
    "python": {"function_definition"},
    "javascript": {"function_declaration", "arrow_function", "method_definition"},
    "typescript": {"function_declaration", "arrow_function", "method_definition"},
    "tsx": {"function_declaration", "arrow_function", "method_definition"},
    "go": {"function_declaration", "method_declaration"},
    "rust": {"function_item"},
    "java": {"method_declaration", "constructor_declaration"},
    "kotlin": {"function_declaration"},
    "c": {"function_definition"},
    "cpp": {"function_definition"},
    "c_sharp": {"method_declaration", "constructor_declaration"},
    "ruby": {"method", "singleton_method"},
    "php": {"function_definition", "method_declaration"},
    "swift": {"function_declaration"},
    "scala": {"function_definition"},
}


@dataclass
class Symbol:
    """A code symbol (class, function, etc.)."""
    name: str
    kind: str  # "class", "function", "interface", "struct", etc.
    line: int
    docstring: Optional[str] = None


@dataclass
class FileSymbols:
    """Symbols extracted from a single file."""
    path: str
    language: str
    classes: list[Symbol] = field(default_factory=list)
    functions: list[Symbol] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.classes and not self.functions


class ASTParser:
    """Parses source files and extracts code symbols using tree-sitter."""

    def __init__(self):
        self._parsers: dict[str, any] = {}

    def _get_parser(self, language: str):
        """Get or create a parser for the given language."""
        if not TREE_SITTER_AVAILABLE:
            return None

        if language not in self._parsers:
            try:
                self._parsers[language] = get_parser(language)
            except Exception as e:
                logger.warning(f"Failed to get parser for {language}: {e}")
                return None
        return self._parsers[language]

    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect language from file extension."""
        ext = Path(file_path).suffix.lower()
        return EXTENSION_TO_LANGUAGE.get(ext)

    def extract_symbols(self, content: str, file_path: str, language: str = None) -> Optional[FileSymbols]:
        """
        Extract classes and functions from source code.

        Args:
            content: Source code content
            file_path: Path to the file (used for language detection if not specified)
            language: Tree-sitter language name (auto-detected if not provided)

        Returns:
            FileSymbols with extracted classes and functions, or None if parsing failed
        """
        if not TREE_SITTER_AVAILABLE:
            return None

        # Detect language if not provided
        if not language:
            language = self.detect_language(file_path)
            if not language:
                return None

        parser = self._get_parser(language)
        if not parser:
            return None

        try:
            tree = parser.parse(content.encode("utf-8"))
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return None

        result = FileSymbols(path=file_path, language=language)

        class_types = CLASS_NODE_TYPES.get(language, set())
        function_types = FUNCTION_NODE_TYPES.get(language, set())

        self._walk_tree(
            tree.root_node,
            content,
            language,
            class_types,
            function_types,
            result,
            depth=0,
        )

        return result

    def _walk_tree(
        self,
        node,
        content: str,
        language: str,
        class_types: set[str],
        function_types: set[str],
        result: FileSymbols,
        depth: int,
    ):
        """Recursively walk the AST and extract symbols."""
        # Only look at top-level and class-level definitions (depth 0-2)
        if depth > 3:
            return

        if node.type in class_types:
            symbol = self._extract_symbol(node, content, language, "class")
            if symbol:
                result.classes.append(symbol)

        elif node.type in function_types:
            # Skip nested functions (only get top-level and methods)
            if depth <= 2:
                symbol = self._extract_symbol(node, content, language, "function")
                if symbol:
                    result.functions.append(symbol)

        # Recurse into children
        for child in node.children:
            self._walk_tree(
                child, content, language, class_types, function_types, result, depth + 1
            )

    def _extract_symbol(self, node, content: str, language: str, kind: str) -> Optional[Symbol]:
        """Extract symbol information from an AST node."""
        name = self._get_name(node, language)
        if not name:
            return None

        # Normalize kind based on node type
        actual_kind = self._normalize_kind(node.type, kind)

        # Try to get docstring (for Python)
        docstring = None
        if language == "python":
            docstring = self._get_python_docstring(node, content)

        return Symbol(
            name=name,
            kind=actual_kind,
            line=node.start_point[0] + 1,  # 1-indexed
            docstring=docstring,
        )

    def _get_name(self, node, language: str) -> Optional[str]:
        """Extract the name from an AST node."""
        # Language-specific name extraction
        name_field_types = {
            "name",
            "identifier",
            "property_identifier",
            "type_identifier",
        }

        for child in node.children:
            if child.type in name_field_types:
                return child.text.decode("utf-8")
            # For Go type declarations, look deeper
            if child.type == "type_spec":
                for subchild in child.children:
                    if subchild.type == "type_identifier":
                        return subchild.text.decode("utf-8")

        return None

    def _normalize_kind(self, node_type: str, default_kind: str) -> str:
        """Normalize the node type to a human-readable kind."""
        kind_map = {
            "class_definition": "class",
            "class_declaration": "class",
            "class_specifier": "class",
            "interface_declaration": "interface",
            "type_alias_declaration": "type",
            "struct_specifier": "struct",
            "struct_item": "struct",
            "struct_declaration": "struct",
            "enum_specifier": "enum",
            "enum_item": "enum",
            "enum_declaration": "enum",
            "trait_item": "trait",
            "trait_definition": "trait",
            "protocol_declaration": "protocol",
            "impl_item": "impl",
            "object_declaration": "object",
            "object_definition": "object",
            "module": "module",
        }
        return kind_map.get(node_type, default_kind)

    def _get_python_docstring(self, node, content: str) -> Optional[str]:
        """Extract docstring from Python class or function."""
        # Look for string as first child of block (docstring)
        for child in node.children:
            if child.type == "block":
                for block_child in child.children:
                    if block_child.type == "string":
                        # Found a docstring - extract the content
                        for string_child in block_child.children:
                            if string_child.type == "string_content":
                                docstring = string_child.text.decode("utf-8").strip()
                                # Truncate long docstrings
                                if len(docstring) > 200:
                                    docstring = docstring[:200] + "..."
                                return docstring
                        # Fallback: get full string and strip quotes
                        docstring = block_child.text.decode("utf-8")
                        docstring = docstring.strip('"""').strip("'''").strip()
                        if len(docstring) > 200:
                            docstring = docstring[:200] + "..."
                        return docstring
                    elif block_child.type == "expression_statement":
                        # Also check expression_statement -> string pattern
                        for expr_child in block_child.children:
                            if expr_child.type == "string":
                                for string_child in expr_child.children:
                                    if string_child.type == "string_content":
                                        docstring = string_child.text.decode("utf-8").strip()
                                        if len(docstring) > 200:
                                            docstring = docstring[:200] + "..."
                                        return docstring
                    break  # Only check first non-trivial statement
        return None

    def extract_from_files(
        self,
        files: dict[str, str]
    ) -> dict[str, FileSymbols]:
        """
        Extract symbols from multiple files.

        Args:
            files: Dict mapping file paths to their content

        Returns:
            Dict mapping file paths to their extracted symbols
        """
        results = {}
        for path, content in files.items():
            symbols = self.extract_symbols(content, path)
            if symbols and not symbols.is_empty:
                results[path] = symbols
        return results
