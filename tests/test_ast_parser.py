"""Tests for AST parser."""

from gitsplain.services.ast_parser import ASTParser, Symbol


class TestSymbol:
    """Tests for Symbol dataclass."""

    def test_str_without_docstring(self):
        """Test string representation without docstring."""
        symbol = Symbol(
            name="MyClass",
            kind="class",
            line=42,
            filepath="src/models.py",
            language="python",
        )
        assert str(symbol) == "class MyClass @ src/models.py:42"

    def test_str_with_docstring(self):
        """Test string representation with docstring."""
        symbol = Symbol(
            name="process_data",
            kind="function",
            line=15,
            filepath="src/utils.py",
            language="python",
            docstring="Process input data.",
        )
        assert (
            str(symbol)
            == "function process_data @ src/utils.py:15 - Process input data."
        )

    def test_str_interface(self):
        """Test string representation for interface."""
        symbol = Symbol(
            name="IService",
            kind="interface",
            line=8,
            filepath="src/services.ts",
            language="typescript",
        )
        assert str(symbol) == "interface IService @ src/services.ts:8"


class TestASTParser:
    """Tests for ASTParser class."""

    def test_detect_language_python(self):
        """Test language detection for Python files."""
        parser = ASTParser()
        assert parser.detect_language("src/main.py") == "python"
        assert parser.detect_language("src/types.pyi") == "python"

    def test_detect_language_javascript(self):
        """Test language detection for JavaScript files."""
        parser = ASTParser()
        assert parser.detect_language("src/app.js") == "javascript"
        assert parser.detect_language("src/component.jsx") == "javascript"

    def test_detect_language_typescript(self):
        """Test language detection for TypeScript files."""
        parser = ASTParser()
        assert parser.detect_language("src/app.ts") == "typescript"
        assert parser.detect_language("src/component.tsx") == "tsx"

    def test_detect_language_unknown(self):
        """Test language detection returns None for unknown extensions."""
        parser = ASTParser()
        assert parser.detect_language("README.md") is None
        assert parser.detect_language("data.json") is None

    def test_extract_symbols_python_class(self):
        """Test extracting Python class."""
        parser = ASTParser()
        code = '''
class MyClass:
    """A test class."""
    pass
'''
        symbols = parser.extract_symbols(code, "test.py")
        assert len(symbols) == 1
        assert symbols[0].name == "MyClass"
        assert symbols[0].kind == "class"
        assert symbols[0].filepath == "test.py"
        assert symbols[0].language == "python"
        assert symbols[0].docstring == "A test class."

    def test_extract_symbols_python_function(self):
        """Test extracting Python function."""
        parser = ASTParser()
        code = '''
        def my_function():
            """Do something."""
            pass
        '''
        symbols = parser.extract_symbols(code, "test.py")
        assert len(symbols) == 1
        assert symbols[0].name == "my_function"
        assert symbols[0].kind == "function"
        assert symbols[0].docstring == "Do something."

    def test_extract_symbols_empty_for_unknown_language(self):
        """Test that unknown file extensions return empty list."""
        parser = ASTParser()
        symbols = parser.extract_symbols("some content", "file.unknown")
        assert symbols == []

    def test_extract_from_files(self):
        """Test extracting symbols from multiple files."""
        parser = ASTParser()
        files = {
            "src/models.py": "class User:\n    pass",
            "src/utils.py": "def helper():\n    pass",
        }
        symbols = parser.extract_from_files(files)
        assert len(symbols) == 2
        names = {s.name for s in symbols}
        assert names == {"User", "helper"}

    def test_extract_from_files_excludes_tests(self):
        """Test that test files are excluded by default."""
        parser = ASTParser()
        files = {
            "src/models.py": "class User:\n    pass",
            "tests/test_models.py": "class TestUser:\n    pass",
        }
        symbols = parser.extract_from_files(files, exclude_tests=True)
        assert len(symbols) == 1
        assert symbols[0].name == "User"

    def test_extract_from_files_includes_tests_when_disabled(self):
        """Test that test files are included when exclude_tests=False."""
        parser = ASTParser()
        files = {
            "src/models.py": "class User:\n    pass",
            "tests/test_models.py": "class TestUser:\n    pass",
        }
        symbols = parser.extract_from_files(files, exclude_tests=False)
        assert len(symbols) == 2
